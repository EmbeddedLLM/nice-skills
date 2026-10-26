#!/usr/bin/env python3
"""Turn `[[REF:bookmark]]` markers into real Word cross-reference fields.

A Word cross-reference is a `REF` field pointing at a bookmark, and
`python-docx` has no API for it. So author the prose with a lightweight marker:

    See [[REF:tbl1]] for the quarterly breakdown.

and let this rewrite each marker into the five runs that make up a complex
field: `fldChar` begin, `instrText` with ` REF <bookmark> \\h `, separate, a
placeholder result, and end.

Design notes and limits:

* the marker has to sit wholly inside one `<w:t>` — if Word split it across
  runs, retype it as one contiguous token;
* bookmarks are *not* created here; pair this with
  `captions_and_crossrefs.py --bookmarks`;
* the placeholder result reads "0" until fields are updated, so run
  `fields_materialize.py` afterwards for deterministic headless QA;
* `document.xml` plus every header and footer are processed.

Typical sequence:

    python scripts/captions_and_crossrefs.py in.docx out_caps.docx --tables --bookmarks
    python scripts/insert_ref_fields.py out_caps.docx out_refs.docx
    python scripts/fields_materialize.py out_refs.docx --out out_refs_mat.docx
"""

from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path

from lxml import etree

try:
    from docx_ooxml_patch import unzip_docx, zip_docx
except Exception:
    # Standalone fallback so a lone copy of this script still runs.
    import os
    import shutil
    import zipfile

    def unzip_docx(docx_path: Path, out_dir: Path) -> None:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(docx_path, "r") as archive:
            archive.extractall(out_dir)

    def zip_docx(in_dir: Path, out_docx_path: Path) -> None:
        if out_docx_path.exists():
            out_docx_path.unlink()
        with zipfile.ZipFile(out_docx_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for root, _dirs, files in os.walk(in_dir):
                for name in files:
                    absolute = Path(root) / name
                    archive.write(absolute, absolute.relative_to(in_dir).as_posix())


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
NS = {"w": W_NS}

DEFAULT_MARKER = r"\[\[REF:(?P<bookmark>[A-Za-z0-9_:\-]+)\]\]"
PLACEHOLDER_RESULT = "0"


def qn(local: str) -> str:
    return f"{{{W_NS}}}{local}"


def preserve_spaces(text_element: etree._Element) -> None:
    text = text_element.text or ""
    if text and (text.startswith(" ") or text.endswith(" ")):
        text_element.set(XML_SPACE, "preserve")


def read_part(path: Path) -> etree._ElementTree:
    return etree.parse(str(path), etree.XMLParser(remove_blank_text=False))


def write_part(tree: etree._ElementTree, path: Path) -> None:
    tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone="yes")


def word_parts(unzipped: Path) -> list[Path]:
    candidates = [unzipped / "word" / "document.xml"]
    for pattern in ("header*.xml", "footer*.xml"):
        candidates.extend(sorted((unzipped / "word").glob(pattern)))
    return [path for path in candidates if path.exists()]


def text_run(text: str) -> etree._Element:
    run = etree.Element(qn("r"))
    element = etree.SubElement(run, qn("t"))
    element.text = text
    preserve_spaces(element)
    return run


def field_run(kind: str) -> etree._Element:
    run = etree.Element(qn("r"))
    marker = etree.SubElement(run, qn("fldChar"))
    marker.set(qn("fldCharType"), kind)
    return run


def instruction_run(bookmark: str) -> etree._Element:
    run = etree.Element(qn("r"))
    instruction = etree.SubElement(run, qn("instrText"))
    instruction.set(XML_SPACE, "preserve")
    instruction.text = f" REF {bookmark} \\h "
    return run


def result_run(text: str = PLACEHOLDER_RESULT) -> etree._Element:
    """Cached field result; materialized later or refreshed by Word."""
    run = etree.Element(qn("r"))
    etree.SubElement(run, qn("t")).text = text
    return run


def reference_field(bookmark: str) -> list[etree._Element]:
    return [
        field_run("begin"),
        instruction_run(bookmark),
        field_run("separate"),
        result_run(),
        field_run("end"),
    ]


def runs_for_text(text: str, matches, prefix: str) -> list[etree._Element]:
    """Literal text runs interleaved with one REF field per match."""
    runs: list[etree._Element] = []
    cursor = 0

    for match in matches:
        leading = text[cursor:match.start()]
        if leading:
            runs.append(text_run(leading))
        if prefix:
            runs.append(text_run(prefix))
        runs.extend(reference_field(match.group("bookmark")))
        cursor = match.end()

    trailing = text[cursor:]
    if trailing:
        runs.append(text_run(trailing))
    return runs


def replace_markers_in_part(tree: etree._ElementTree, marker_re: re.Pattern[str],
                            prefix: str) -> int:
    replaced = 0

    for text_element in tree.getroot().findall(".//w:t", namespaces=NS):
        if text_element.text is None:
            continue
        matches = list(marker_re.finditer(text_element.text))
        if not matches:
            continue

        run = text_element.getparent()
        paragraph = run.getparent() if run is not None else None
        if run is None or run.tag != qn("r") or paragraph is None:
            continue

        position = paragraph.index(run)
        paragraph.remove(run)
        for offset, new_run in enumerate(runs_for_text(text_element.text, matches, prefix)):
            paragraph.insert(position + offset, new_run)

        replaced += len(matches)

    return replaced


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input_docx", type=Path)
    ap.add_argument("output_docx", type=Path)
    ap.add_argument(
        "--pattern",
        default=DEFAULT_MARKER,
        help="Regex for markers. Must contain a named group 'bookmark'. "
             "Default matches [[REF:tbl1]].",
    )
    ap.add_argument(
        "--prefix",
        default="",
        help="Optional text inserted immediately before the REF field.",
    )
    args = ap.parse_args()

    marker_re = re.compile(args.pattern)

    with tempfile.TemporaryDirectory(prefix="docx_unz_") as staging:
        unzipped = Path(staging) / "unz"
        unzip_docx(args.input_docx, unzipped)

        total = 0
        for part in word_parts(unzipped):
            tree = read_part(part)
            total += replace_markers_in_part(tree, marker_re, args.prefix)
            write_part(tree, part)

        zip_docx(unzipped, args.output_docx)

    print(f"[OK] wrote {args.output_docx} | markers_replaced={total}")


if __name__ == "__main__":
    main()
