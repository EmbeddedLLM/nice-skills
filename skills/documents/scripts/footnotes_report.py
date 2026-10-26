#!/usr/bin/env python3
"""Summarise the footnote/endnote wiring of a DOCX.

Real notes are not footer text. They live in their own parts —
`word/footnotes.xml` and `word/endnotes.xml` — and the body reaches them
through `w:footnoteReference` / `w:endnoteReference` elements carrying an id.

This walks both directions of that wiring and prints what it finds: whether
each note part exists, how many ids are defined versus referenced, which ids
are referenced more than once, and a few note texts to eyeball.

    python scripts/footnotes_report.py in.docx
"""

from __future__ import annotations

import argparse
import zipfile
from collections import Counter

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

DOCUMENT_PART = "word/document.xml"
DOCUMENT_LABEL = "document.xml"  # how the report refers to the body part
NOTE_PARTS = {"footnote": "word/footnotes.xml", "endnote": "word/endnotes.xml"}
SNIPPET_LIMIT = 5
ID_DISPLAY_LIMIT = 10
SNIPPET_CHARS = 120


def parse_part(archive: zipfile.ZipFile, name: str) -> etree._Element:
    return etree.fromstring(archive.read(name))


def reference_ids(body: etree._Element, kind: str) -> list[int]:
    """Ids the document body points at, in document order."""
    elements = body.xpath(f".//w:{kind}Reference", namespaces=NS)
    return [int(element.get(f"{{{W_NS}}}id")) for element in elements]


def note_text(note: etree._Element) -> str:
    return "".join(t.text for t in note.xpath(".//w:t", namespaces=NS) if t.text).strip()


def defined_notes(root: etree._Element, kind: str) -> list[etree._Element]:
    """Note elements proper; ids -1 and 0 are the separator/continuation entries."""
    return root.xpath(f".//w:{kind}[number(@w:id) >= 1]", namespaces=NS)


def summarise_note_part(archive: zipfile.ZipFile, part: str, kind: str) -> None:
    notes = defined_notes(parse_part(archive, part), kind)
    ids = [int(note.get(f"{{{W_NS}}}id")) for note in notes]
    shown = sorted(ids)[:ID_DISPLAY_LIMIT]
    ellipsis = "..." if len(ids) > ID_DISPLAY_LIMIT else ""
    print(f"[{part}] defined_{kind}s={len(ids)} ids={shown}{ellipsis}")

    for note in notes[:SNIPPET_LIMIT]:
        text = note_text(note)
        if text:
            print(f"  - id={note.get(f'{{{W_NS}}}id')}: {text[:SNIPPET_CHARS]}")


def report(archive: zipfile.ZipFile) -> None:
    body = parse_part(archive, DOCUMENT_PART)
    names = archive.namelist()

    collected = {}
    for kind in ("footnote", "endnote"):
        ids = reference_ids(body, kind)
        collected[kind] = ids
        print(f"[{DOCUMENT_LABEL}] {kind}References={len(ids)} ids={sorted(set(ids))}")

    repeated = [key for key, count in Counter(collected["footnote"]).items() if count > 1]
    if repeated:
        print(
            "[warn] duplicated footnote reference ids (multiple references to same note): "
            f"{repeated}"
        )

    for kind, part in NOTE_PARTS.items():
        if part in names:
            summarise_note_part(archive, part, kind)
        else:
            print(f"[{part}] MISSING")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    args = ap.parse_args()

    with zipfile.ZipFile(args.docx, "r") as archive:
        report(archive)


if __name__ == "__main__":
    main()
