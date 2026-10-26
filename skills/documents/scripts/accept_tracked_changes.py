#!/usr/bin/env python3
"""Accept or reject the tracked changes in a DOCX by patching OOXML.

For the common request — "give me the final version with the redlines
accepted". Revision wrappers in `word/document.xml` are rewritten:

    w:ins, w:moveTo     accepted → unwrapped in place;  rejected → deleted
    w:del, w:moveFrom   accepted → deleted;             rejected → unwrapped

Unwrapping keeps the children where the wrapper was, in order, so surrounding
runs do not move.

Modes: `report` prints counts and writes nothing; `accept` and `reject` need
`--out`. Tracking is switched off in the output unless `--keep_tracking_on`.

This is a pragmatic helper covering the common constructs, not a full-fidelity
Word revision engine. Render and read the result afterwards.

    python scripts/accept_tracked_changes.py in.docx --mode report
    python scripts/accept_tracked_changes.py in.docx --mode accept --out out.docx
"""

from __future__ import annotations

import argparse
import zipfile
from typing import NamedTuple

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
DOCUMENT_PART = "word/document.xml"
SETTINGS_PART = "word/settings.xml"

# Wrapper tag → whether it holds content that survives an "accept".
REVISION_TAGS = (("moveTo", True), ("moveFrom", False), ("ins", True), ("del", False))


class Tally(NamedTuple):
    ins: int = 0
    del_: int = 0
    moveto: int = 0
    movefrom: int = 0

    def as_line(self) -> str:
        return f"ins={self.ins} del={self.del_} moveTo={self.moveto} moveFrom={self.movefrom}"


def parse(archive: zipfile.ZipFile, name: str) -> etree._Element:
    return etree.fromstring(archive.read(name))


def dump(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def unwrap_in_place(element: etree._Element) -> None:
    """Swap a wrapper for its children, keeping their position and order."""
    parent = element.getparent()
    if parent is None:
        return
    position = parent.index(element)
    children = list(element)
    parent.remove(element)
    for offset, child in enumerate(children):
        parent.insert(position + offset, child)


def detach(element: etree._Element) -> None:
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def count_revisions(document_root: etree._Element) -> Tally:
    def total(tag: str) -> int:
        return len(document_root.xpath(f".//w:{tag}", namespaces=NS))

    return Tally(ins=total("ins"), del_=total("del"),
                 moveto=total("moveTo"), movefrom=total("moveFrom"))


def resolve_revisions(document_root: etree._Element, mode: str) -> None:
    """Apply accept/reject to every revision wrapper, deepest-last first."""
    for tag, is_insertion in REVISION_TAGS:
        keep = is_insertion if mode == "accept" else not is_insertion
        # Reverse document order so earlier positions stay valid while editing.
        for element in reversed(document_root.xpath(f".//w:{tag}", namespaces=NS)):
            unwrap_in_place(element) if keep else detach(element)


def clear_tracking_flag(settings_root: etree._Element) -> bool:
    edited = False
    for element in settings_root.xpath(".//w:trackRevisions", namespaces=NS):
        detach(element)
        edited = True
    return edited


def write_package(source_docx: str, out_docx: str, document_xml: bytes,
                  settings_xml: bytes | None) -> None:
    with zipfile.ZipFile(source_docx, "r") as source, \
            zipfile.ZipFile(out_docx, "w", zipfile.ZIP_DEFLATED) as destination:
        for info in source.infolist():
            name = info.filename
            if name == DOCUMENT_PART:
                destination.writestr(name, document_xml)
            elif settings_xml is not None and name == SETTINGS_PART:
                destination.writestr(name, settings_xml)
            else:
                destination.writestr(name, source.read(name))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_docx")
    ap.add_argument("--mode", choices=["report", "accept", "reject"], required=True)
    ap.add_argument("--out", help="Output DOCX (required for accept/reject)")
    ap.add_argument(
        "--keep_tracking_on",
        action="store_true",
        help="Do not remove trackRevisions from settings.xml",
    )
    args = ap.parse_args()

    with zipfile.ZipFile(args.in_docx, "r") as source:
        document_root = parse(source, DOCUMENT_PART)
        settings_root = (parse(source, SETTINGS_PART)
                         if SETTINGS_PART in source.namelist() else None)

    print(f"[report] {count_revisions(document_root).as_line()}")
    if args.mode == "report":
        return
    if not args.out:
        raise SystemExit("--out is required for accept/reject")

    resolve_revisions(document_root, args.mode)

    settings_xml = None
    if settings_root is not None and not args.keep_tracking_on:
        if clear_tracking_flag(settings_root):
            settings_xml = dump(settings_root)

    print(f"[after]  {count_revisions(document_root).as_line()}")
    write_package(args.in_docx, args.out, dump(document_root), settings_xml)
    print(f"[OK] wrote {args.out}")


if __name__ == "__main__":
    main()
