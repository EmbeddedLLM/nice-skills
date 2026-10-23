#!/usr/bin/env python3
"""Replace REF/PAGEREF fields with the text they currently display.

Headless LibreOffice sometimes drops a REF field's cached result even though
Word shows it fine, which makes screenshot regression runs unreliable. Freezing
the field into a literal run removes that variable.

A field occupies a span of runs inside one paragraph:

    <w:fldChar w:fldCharType="begin"/>
    <w:instrText>REF tbl1 …</w:instrText>
    <w:fldChar w:fldCharType="separate"/>
    <w:t>Table 3</w:t>              ← the cached, visible result
    <w:fldChar w:fldCharType="end"/>

The whole span is replaced by a single run holding that visible text. Only
`REF` and `PAGEREF` instructions are touched, and only fields contained in one
paragraph — that is the best-effort scope.

    python scripts/flatten_ref_fields.py in.docx --out out.docx
"""

from __future__ import annotations

import argparse
import re
import zipfile

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
DOCUMENT_PART = "word/document.xml"

REFERENCE_INSTRUCTION = re.compile(r"\b(?:PAGE)?REF\b", re.IGNORECASE)


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def serialise(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def field_char_kind(element: etree._Element) -> str | None:
    """`begin` / `separate` / `end` when this child carries a fldChar, else None."""
    marker = element.find(".//w:fldChar", namespaces=NS)
    if marker is None or marker.tag != w("fldChar"):
        return None
    return marker.get(w("fldCharType"))


def locate_field(children: list[etree._Element], start: int) -> tuple[int, int, int] | None:
    """Indices (begin, separate, end) of the first complete field at/after start."""
    if field_char_kind(children[start]) != "begin":
        return None

    separate = None
    for index in range(start + 1, len(children)):
        kind = field_char_kind(children[index])
        if kind == "separate":
            separate = index
        elif kind == "end":
            return None if separate is None else (start, separate, index)
    return None


def joined_text(children: list[etree._Element], first: int, last: int, xpath: str) -> str:
    collected = []
    for child in children[first:last]:
        collected.extend(child.xpath(xpath, namespaces=NS))
    return "".join(collected)


def instruction_of(children: list[etree._Element], begin: int, separate: int) -> str:
    return joined_text(children, begin, separate + 1, ".//w:instrText/text()")


def cached_result(children: list[etree._Element], separate: int, end: int) -> str:
    return joined_text(children, separate + 1, end, ".//w:t/text()")


def literal_run(text: str) -> etree._Element:
    run = etree.Element(w("r"))
    etree.SubElement(run, w("t")).text = text
    return run


def flatten_paragraph(paragraph: etree._Element) -> int:
    """Collapse every REF/PAGEREF field in one paragraph; report how many."""
    flattened = 0
    children = list(paragraph)
    index = 0

    while index < len(children):
        span = locate_field(children, index)
        if span is None:
            index += 1
            continue

        begin, separate, end = span
        if not REFERENCE_INSTRUCTION.search(instruction_of(children, begin, separate)):
            index += 1
            continue

        visible = cached_result(children, separate, end)
        if not visible.strip():
            index = end + 1
            continue

        paragraph.insert(begin, literal_run(visible))
        for element in children[begin:end + 1]:
            paragraph.remove(element)

        flattened += 1
        children = list(paragraph)
        index += 1

    return flattened


def flatten_part(root: etree._Element) -> int:
    return sum(flatten_paragraph(p) for p in root.xpath(".//w:p", namespaces=NS))


def main() -> None:
    ap = argparse.ArgumentParser(description="Flatten REF/PAGEREF fields to literal text")
    ap.add_argument("in_docx")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with zipfile.ZipFile(args.in_docx, "r") as source:
        root = etree.fromstring(source.read(DOCUMENT_PART))
        count = flatten_part(root)
        replacements = {DOCUMENT_PART: serialise(root)} if count else {}

        with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as destination:
            for info in source.infolist():
                name = info.filename
                payload = replacements[name] if name in replacements else source.read(name)
                destination.writestr(name, payload)

    print(f"[OK] wrote {args.out} (fields_flattened={count})")


if __name__ == "__main__":
    main()
