#!/usr/bin/env python3
"""Add Figure/Table captions, with optional bookmarks and field materialization.

A pragmatic OOXML helper for the automation-friendly subset of Word's caption
feature:

* a `Caption`-styled paragraph is inserted after each table (`w:tbl`) and after
  each paragraph that holds a drawing or picture, numbered with a `SEQ` field;
* with `--bookmarks`, the caption number is wrapped in a bookmark (`tbl1`,
  `fig1`, …) so `insert_ref_fields.py` can point `REF` fields at it;
* with `--materialize`, SEQ/REF results are frozen so headless renders show the
  right numbers.

Anything already carrying a matching caption is left alone, so the tool is safe
to re-run.

    python scripts/captions_and_crossrefs.py in.docx out.docx --tables --figures --bookmarks
"""

from __future__ import annotations

import argparse
import tempfile
from dataclasses import dataclass
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
NS = {"w": W_NS, "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

CAPTION_STYLE = "Caption"
FIELD_RESULT_PLACEHOLDER = "0"


@dataclass(frozen=True)
class CaptionSpec:
    """One caption family: what it says, how it counts, how it is bookmarked."""

    label: str            # "Table" / "Figure"
    sequence_name: str    # SEQ field name
    bookmark_prefix: str  # tbl / fig

    @property
    def instruction(self) -> str:
        return f" SEQ {self.sequence_name} \\* ARABIC "


TABLE_SPEC = CaptionSpec(label="Table", sequence_name="Table", bookmark_prefix="tbl")
FIGURE_SPEC = CaptionSpec(label="Figure", sequence_name="Figure", bookmark_prefix="fig")


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


def field_marker_run(kind: str) -> etree._Element:
    run = etree.Element(qn("r"))
    etree.SubElement(run, qn("fldChar")).set(qn("fldCharType"), kind)
    return run


def instruction_run(instruction: str) -> etree._Element:
    run = etree.Element(qn("r"))
    element = etree.SubElement(run, qn("instrText"))
    element.set(XML_SPACE, "preserve")
    element.text = instruction
    return run


def cached_result_run(text: str = FIELD_RESULT_PLACEHOLDER) -> etree._Element:
    run = etree.Element(qn("r"))
    etree.SubElement(run, qn("t")).text = text
    return run


def caption_paragraph(spec: CaptionSpec, caption_text: str) -> etree._Element:
    """`Table 1: caption text` as a Caption-styled paragraph with a SEQ field."""
    paragraph = etree.Element(qn("p"))
    style = etree.SubElement(etree.SubElement(paragraph, qn("pPr")), qn("pStyle"))
    style.set(qn("val"), CAPTION_STYLE)

    paragraph.append(text_run(f"{spec.label} "))
    paragraph.append(field_marker_run("begin"))
    paragraph.append(instruction_run(spec.instruction))
    paragraph.append(field_marker_run("separate"))
    paragraph.append(cached_result_run())
    paragraph.append(field_marker_run("end"))

    if caption_text:
        paragraph.append(text_run(f": {caption_text}"))
    return paragraph


def already_captioned(element: etree._Element, label: str) -> bool:
    """True when the next sibling is a Caption paragraph starting with `label`."""
    following = element.getnext()
    if following is None or following.tag != qn("p"):
        return False
    style = following.find("w:pPr/w:pStyle", namespaces=NS)
    if style is None or style.get(qn("val")) != CAPTION_STYLE:
        return False
    return "".join(following.xpath(".//w:t/text()", namespaces=NS)).strip().startswith(label)


def highest_bookmark_id(root: etree._Element) -> int:
    highest = 0
    for tag in ("bookmarkStart", "bookmarkEnd"):
        for bookmark in root.findall(f".//w:{tag}", namespaces=NS):
            value = bookmark.get(qn("id"))
            if value and value.isdigit():
                highest = max(highest, int(value))
    return highest


def bookmark_field_result(paragraph: etree._Element, name: str, bookmark_id: int) -> None:
    """Wrap the field's cached result run in a bookmark, for REF targets."""
    after_separate = False
    target_run = None

    for run in paragraph.xpath(".//w:r", namespaces=NS):
        marker = run.find("w:fldChar", namespaces=NS)
        if marker is not None and marker.get(qn("fldCharType")) == "separate":
            after_separate = True
            continue
        if after_separate and run.find("w:t", namespaces=NS) is not None:
            target_run = run
            break

    if target_run is None:
        return

    parent = target_run.getparent()
    position = parent.index(target_run)

    start = etree.Element(qn("bookmarkStart"))
    start.set(qn("id"), str(bookmark_id))
    start.set(qn("name"), name)
    end = etree.Element(qn("bookmarkEnd"))
    end.set(qn("id"), str(bookmark_id))

    parent.insert(position, start)
    parent.insert(position + 2, end)


def holds_a_picture(paragraph: etree._Element) -> bool:
    return (paragraph.find(".//w:drawing", namespaces=NS) is not None
            or paragraph.find(".//w:pict", namespaces=NS) is not None)


def caption_elements(root: etree._Element, spec: CaptionSpec):
    """Elements that should carry one of these captions, in document order."""
    if spec is TABLE_SPEC:
        return root.findall(".//w:tbl", namespaces=NS)
    return [p for p in root.findall(".//w:p", namespaces=NS) if holds_a_picture(p)]


class CaptionInserter:
    def __init__(self, caption_text: str, add_bookmarks: bool) -> None:
        self.caption_text = caption_text
        self.add_bookmarks = add_bookmarks

    def process_part(self, root: etree._Element, specs: list[CaptionSpec]) -> None:
        next_bookmark_id = highest_bookmark_id(root) + 1

        for spec in specs:
            counter = 0
            for element in caption_elements(root, spec):
                if already_captioned(element, spec.label):
                    continue
                counter += 1
                caption = caption_paragraph(spec, self.caption_text)
                element.addnext(caption)
                if self.add_bookmarks:
                    bookmark_field_result(
                        caption, f"{spec.bookmark_prefix}{counter}", next_bookmark_id
                    )
                    next_bookmark_id += 1


def materialize_part(tree: etree._ElementTree) -> None:
    """Freeze SEQ counters and REF results so renders are deterministic."""
    from fields_materialize import materialize_fields_in_root

    materialize_fields_in_root(tree.getroot(), {"SEQ", "REF"})


def add_captions(docx_path: Path, out_docx: Path, add_tables: bool, add_figures: bool,
                 caption_text: str, add_bookmarks: bool, materialize: bool) -> None:
    specs = []
    if add_tables:
        specs.append(TABLE_SPEC)
    if add_figures:
        specs.append(FIGURE_SPEC)

    inserter = CaptionInserter(caption_text, add_bookmarks)

    with tempfile.TemporaryDirectory(prefix="docx_unz_") as staging:
        unzipped = Path(staging) / "unz"
        unzip_docx(docx_path, unzipped)

        for part in word_parts(unzipped):
            tree = read_part(part)
            inserter.process_part(tree.getroot(), specs)
            if materialize:
                materialize_part(tree)
            write_part(tree, part)

        zip_docx(unzipped, out_docx)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input_docx", type=Path)
    ap.add_argument("output_docx", type=Path)
    ap.add_argument("--tables", action="store_true", help="Add table captions.")
    ap.add_argument("--figures", action="store_true", help="Add figure captions.")
    ap.add_argument("--caption_text", default="",
                    help="Text appended after the caption number, e.g. 'Results by category'.")
    ap.add_argument("--bookmarks", action="store_true",
                    help="Add bookmarks around caption numbers (tbl1, tbl2, fig1...).")
    ap.add_argument("--materialize", action="store_true",
                    help="Materialize SEQ/REF fields so headless renders show correct numbers.")
    args = ap.parse_args()

    if not args.tables and not args.figures:
        ap.error("Please specify at least one of --tables or --figures")

    add_captions(
        args.input_docx,
        args.output_docx,
        add_tables=args.tables,
        add_figures=args.figures,
        caption_text=args.caption_text,
        add_bookmarks=args.bookmarks,
        materialize=args.materialize,
    )

    print(f"[OK] wrote {args.output_docx}")


if __name__ == "__main__":
    main()
