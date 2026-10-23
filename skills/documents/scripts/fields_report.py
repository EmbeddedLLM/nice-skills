#!/usr/bin/env python3
"""Inventory the Word fields inside a DOCX.

A surprising share of "the render looks wrong" reports are stale fields:
`PAGE`, `NUMPAGES`, `TOC`, `REF`, `PAGEREF`. Headless LibreOffice and the Word
GUI refresh fields differently, so an export can show placeholders that Word
never would. Knowing which fields a document carries tells you whether a
refresh step belongs in the plan.

Both field spellings are handled — `<w:fldSimple w:instr="…"/>` and the complex
`fldChar` begin/end form whose instruction is spread over `instrText` nodes —
plus a fallback that surfaces stray `instrText` when the `fldChar` structure is
malformed. Field *switches* are not interpreted; only the leading token is used
to classify.
"""

from __future__ import annotations

import argparse
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W_NS, "r": R_NS}

FLD_CHAR = f"{{{W_NS}}}fldChar"
FLD_CHAR_TYPE = f"{{{W_NS}}}fldCharType"
INSTR_TEXT = f"{{{W_NS}}}instrText"
INSTR_ATTR = f"{{{W_NS}}}instr"
WHITESPACE = re.compile(r"\s+")

# Parts that commonly carry fields.
ALWAYS_SCANNED = {"document.xml", "settings.xml", "footnotes.xml", "endnotes.xml"}
FIELD_TYPES_NEEDING_UPDATE = ("TOC", "REF", "PAGEREF", "NUMPAGES", "PAGE")
UPDATE_REMINDER = (
    "- If the PDF/PNGs show placeholders or wrong page numbers/TOC, open in Word "
    "and run: Ctrl+A → F9 (Update Fields), then re-render."
)


def scannable_parts(archive: zipfile.ZipFile):
    for name in archive.namelist():
        if not (name.startswith("word/") and name.endswith(".xml")):
            continue
        base = name.rsplit("/", 1)[-1]
        if base in ALWAYS_SCANNED or base.startswith(("header", "footer")):
            yield name


def field_kind(instruction: str) -> str:
    text = (instruction or "").strip()
    return text.split()[0].upper() if text else "(empty)"


def simple_field_instructions(root: etree._Element) -> list[str]:
    found = []
    for element in root.findall(".//w:fldSimple", namespaces=NS):
        instruction = element.get(INSTR_ATTR) or element.get("w:instr")  # prefixed fallback
        if instruction:
            found.append(instruction)
    return found


def complex_field_instructions(root: etree._Element) -> list[str]:
    """Instructions of fldChar-delimited fields, in document order."""
    found: list[str] = []
    inside_field = False
    buffer: list[str] = []

    for node in root.iter():
        if node.tag == FLD_CHAR:
            kind = node.get(FLD_CHAR_TYPE)
            if kind == "begin":
                inside_field, buffer = True, []
            elif kind == "end" and inside_field:
                instruction = "".join(buffer).strip()
                if instruction:
                    found.append(instruction)
                inside_field, buffer = False, []
            continue
        if inside_field and node.tag == INSTR_TEXT:
            buffer.append(node.text or "")

    return found


def stray_instruction_text(root: etree._Element) -> list[str]:
    return [
        node.text or ""
        for node in root.findall(".//w:instrText", namespaces=NS)
        if (node.text or "").strip()
    ]


def extract_field_instructions(xml_bytes: bytes) -> list[str]:
    parser = etree.XMLParser(recover=True, remove_blank_text=False)
    root = etree.fromstring(xml_bytes, parser=parser)

    instructions = simple_field_instructions(root) + complex_field_instructions(root)
    if not instructions:
        instructions = stray_instruction_text(root)

    normalised = []
    for instruction in instructions:
        collapsed = WHITESPACE.sub(" ", instruction).strip()
        if collapsed:
            normalised.append(collapsed)
    return normalised


def scan_package(docx: Path, max_examples: int):
    by_part: dict[str, list[str]] = {}
    counts: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)

    with zipfile.ZipFile(docx, "r") as archive:
        for part in scannable_parts(archive):
            try:
                instructions = extract_field_instructions(archive.read(part))
            except Exception:
                continue
            if not instructions:
                continue
            by_part[part] = instructions
            for instruction in instructions:
                kind = field_kind(instruction)
                counts[kind] += 1
                if len(examples[kind]) < max_examples:
                    examples[kind].append(instruction)

    return by_part, counts, examples


def print_report(by_part, counts: Counter, examples) -> None:
    print("FIELD COUNTS")
    for kind, total in counts.most_common():
        print(f"- {kind}: {total}")

    print("\nEXAMPLES")
    for kind, _total in counts.most_common():
        samples = examples.get(kind, [])
        if not samples:
            continue
        print(f"\n[{kind}]")
        for instruction in samples:
            print(f"  - {instruction}")

    print("\nPER-PART DETAILS")
    for part, instructions in sorted(by_part.items()):
        print(f"\n== {part} ==")
        for instruction in instructions:
            print(f"- {instruction}")

    if any(kind in counts for kind in FIELD_TYPES_NEEDING_UPDATE):
        print("\nREMINDER")
        print(UPDATE_REMINDER)


def main() -> None:
    ap = argparse.ArgumentParser(description="Scan a DOCX for Word fields (PAGE/TOC/REF/...).")
    ap.add_argument("docx", type=Path)
    ap.add_argument("--max_examples", type=int, default=8, help="Examples to print per field type")
    args = ap.parse_args()

    if not args.docx.exists():
        raise FileNotFoundError(args.docx)

    by_part, counts, examples = scan_package(args.docx, args.max_examples)
    if not by_part:
        print("No fields found in document.xml/headers/footers.")
        return

    print_report(by_part, counts, examples)


if __name__ == "__main__":
    main()
