#!/usr/bin/env python3
"""Freeze SEQ and REF field results into literal text.

Word evaluates fields; headless renderers often do not, which makes visual QA
unreliable — caption numbers show as the cached placeholder, cross-references
show a stale page. This writes each field's *display* text into the result run
while leaving the field code intact, so:

* renders are stable and deterministic;
* Word can still update the field later.

Supported: `SEQ <name>` (counted in document order per name) and
`REF <bookmark>` (resolved to the text currently inside that bookmark).
Deliberately unsupported: `PAGE` / `NUMPAGES` (they need pagination) and `TOC`
(rebuild it in Word or use `insert_toc.py`).

    python scripts/fields_materialize.py in.docx --out out.docx
    python scripts/fields_materialize.py in.docx --out out.docx --only SEQ REF
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

try:
    from docx_ooxml_patch import unzip_docx, zip_docx
except Exception:
    # Standalone fallback so a lone copy of this script still runs.
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
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS, "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

SEQ_INSTRUCTION = re.compile(r"\bSEQ\s+([A-Za-z0-9_]+)")
REF_INSTRUCTION = re.compile(r"\bREF\s+([A-Za-z0-9_:\-\.]+)")
WHITESPACE = re.compile(r"\s+")


def qn(local: str) -> str:
    return f"{{{W_NS}}}{local}"


def set_result_text(text_node: etree._Element, value: str) -> None:
    text_node.text = value
    if value.startswith(" ") or value.endswith(" "):
        text_node.set(f"{{{XML_NS}}}space", "preserve")


def materialisable_parts(unzipped: Path) -> list[Path]:
    word = unzipped / "word"
    candidates = [word / "document.xml"]
    candidates += [Path(p) for p in sorted(glob.glob(str(word / "header*.xml")))]
    candidates += [Path(p) for p in sorted(glob.glob(str(word / "footer*.xml")))]
    return [path for path in candidates if path.exists()]


@dataclass
class FieldSpan:
    """One complete complex field inside a paragraph."""

    instruction: str
    result_nodes: list[etree._Element] = field(default_factory=list)

    @property
    def normalised_instruction(self) -> str:
        return WHITESPACE.sub(" ", self.instruction)

    def write_result(self, value: str) -> bool:
        """Put `value` in the first result node and blank any extras."""
        if not self.result_nodes:
            return False
        set_result_text(self.result_nodes[0], value)
        for extra in self.result_nodes[1:]:
            set_result_text(extra, "")
        return True


def iter_fields(paragraph: etree._Element):
    """Yield each `fldChar` begin…end field found in one paragraph."""
    current: FieldSpan | None = None
    after_separate = False

    for run in paragraph.xpath(".//w:r", namespaces=NS):
        marker = run.find("w:fldChar", namespaces=NS)

        if marker is not None:
            kind = marker.get(qn("fldCharType"))
            if kind == "begin":
                current, after_separate = FieldSpan(instruction=""), False
                continue
            if current is None:
                continue
            if kind == "separate":
                after_separate = True
                continue
            if kind == "end":
                yield current
                current, after_separate = None, False
                continue

        if current is None:
            continue

        instruction_node = run.find("w:instrText", namespaces=NS)
        if instruction_node is not None and not after_separate:
            current.instruction += instruction_node.text or ""

        if after_separate:
            current.result_nodes.extend(run.findall(".//w:t", namespaces=NS))


def bookmark_text_map(root: etree._Element) -> dict[str, str]:
    """Bookmark name → text found between its start and end markers."""
    open_bookmarks: list[tuple[str, str, list[str]]] = []
    collected: dict[str, str] = {}

    for element in root.iter():
        if element.tag == qn("bookmarkStart"):
            name = element.get(qn("name")) or ""
            if name:  # Word-internal marks like _GoBack carry no useful name
                open_bookmarks.append((element.get(qn("id")) or "", name, []))
        elif element.tag == qn("bookmarkEnd"):
            wanted = element.get(qn("id")) or ""
            for position in range(len(open_bookmarks) - 1, -1, -1):
                if open_bookmarks[position][0] == wanted:
                    _id, name, buffer = open_bookmarks.pop(position)
                    collected[name] = "".join(buffer)
                    break
        elif element.tag == qn("t") and open_bookmarks:
            text = element.text or ""
            # Nested bookmarks all see the same text; nesting depth is tiny.
            for entry in open_bookmarks:
                entry[2].append(text)

    return collected


class SequenceResolver:
    """Counts `SEQ <name>` occurrences in document order."""

    def __init__(self) -> None:
        self.counters: dict[str, int] = {}

    def resolve(self, span: FieldSpan) -> str | None:
        match = SEQ_INSTRUCTION.search(span.normalised_instruction)
        if not match:
            return None
        name = match.group(1)
        self.counters[name] = self.counters.get(name, 0) + 1
        return str(self.counters[name])


class BookmarkResolver:
    """Reads `REF <bookmark>` results from the text the bookmark wraps."""

    def __init__(self, root: etree._Element) -> None:
        self.bookmarks = bookmark_text_map(root)

    def resolve(self, span: FieldSpan) -> str | None:
        match = REF_INSTRUCTION.search(span.normalised_instruction)
        if not match:
            return None
        return self.bookmarks.get(match.group(1))


def materialize_fields_in_root(root: etree._Element, only: set[str]) -> int:
    """Freeze the selected field kinds in one XML root; return the count.

    Order matters: a bookmark often wraps a SEQ result, so sequences are
    resolved first — otherwise every REF would capture the placeholder "0".
    Each resolver is built immediately before its own pass so it sees the tree
    as the previous pass left it.
    """
    passes = []
    if "SEQ" in only:
        passes.append(SequenceResolver)
    if "REF" in only:
        passes.append(lambda: BookmarkResolver(root))

    updated = 0
    for build in passes:
        resolver = build()
        for paragraph in root.findall(".//w:p", namespaces=NS):
            for span in iter_fields(paragraph):
                value = resolver.resolve(span)
                if value is not None and span.write_result(value):
                    updated += 1

    return updated


def main() -> None:
    ap = argparse.ArgumentParser(description="Materialize SEQ/REF field results inside a DOCX")
    ap.add_argument("input_docx")
    ap.add_argument("--out", required=True, help="Output DOCX path")
    ap.add_argument(
        "--only",
        nargs="+",
        default=["SEQ", "REF"],
        choices=["SEQ", "REF"],
        help="Which field types to materialize (default: SEQ REF)",
    )
    args = ap.parse_args()

    input_docx = Path(args.input_docx)
    out_docx = Path(args.out)
    selected = set(args.only)

    with tempfile.TemporaryDirectory(prefix="docx_unzip_") as staging:
        unzipped = Path(staging) / "docx"
        unzip_docx(input_docx, unzipped)

        parser = etree.XMLParser(remove_blank_text=False)
        total = 0
        for part in materialisable_parts(unzipped):
            tree = etree.parse(str(part), parser)
            updated = materialize_fields_in_root(tree.getroot(), only=selected)
            if updated:
                tree.write(str(part), xml_declaration=True, encoding="UTF-8", standalone="yes")
            total += updated

        zip_docx(unzipped, out_docx)

    print(f"[OK] materialized {total} field(s) -> {out_docx}")


if __name__ == "__main__":
    main()
