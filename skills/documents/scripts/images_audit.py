#!/usr/bin/env python3
"""Report the images a DOCX carries: inline or floating, how big, from where.

Image placement is the most common Word-versus-LibreOffice divergence, and the
first question is usually "are any of these anchored?" This scans
`document.xml` plus every header and footer for `wp:inline` and `wp:anchor`
drawings, resolves each one's `r:embed` relationship to the media part, and
prints the extent from the OOXML in inches.

Best-effort by nature: charts and SmartArt live in different parts and are not
reported. python-docx only ever produces inline images, so an `anchor` row
means the file has been through the Word UI.
"""

from __future__ import annotations

import argparse
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W_NS, "r": R_NS, "wp": WP_NS, "a": A_NS, "rel": REL_NS}

EMU_PER_INCH = 914400
DRAWING_KINDS = (("inline", ".//wp:inline"), ("anchor", ".//wp:anchor"))
ANCHOR_WARNING = (
    "- Floating/anchored images detected (wp:anchor). These are the most common "
    "Word-vs-LO mismatch."
)


@dataclass
class ImageRow:
    part: str
    kind: str
    relationship_id: str
    target: str
    zip_path: str
    size_inches: str
    byte_count: str


def content_parts(archive: zipfile.ZipFile):
    """Main document plus numbered headers and footers."""
    for name in archive.namelist():
        if not name.startswith("word/"):
            continue
        base = name.rsplit("/", 1)[-1]
        if name.endswith("document.xml"):
            yield name
        elif base.endswith(".xml") and base.startswith(("header", "footer")):
            yield name


def relationships_path(part_name: str) -> str:
    """word/document.xml → word/_rels/document.xml.rels"""
    return f"word/_rels/{part_name.rsplit('/', 1)[-1]}.rels"


def relationship_targets(archive: zipfile.ZipFile, part_name: str) -> dict[str, str]:
    rels_name = relationships_path(part_name)
    if rels_name not in archive.namelist():
        return {}
    root = etree.fromstring(archive.read(rels_name))
    return {
        rel.get("Id"): rel.get("Target")
        for rel in root.findall("rel:Relationship", namespaces=NS)
        if rel.get("Id") and rel.get("Target")
    }


def inches_from_emu(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return int(value) / EMU_PER_INCH
    except (TypeError, ValueError):
        return None


def extent_inches(drawing: etree._Element) -> tuple[float | None, float | None]:
    extent = drawing.find("wp:extent", namespaces=NS)
    if extent is None:
        return None, None
    return inches_from_emu(extent.get("cx")), inches_from_emu(extent.get("cy"))


def media_bytes(archive: zipfile.ZipFile, target: str) -> tuple[str, bytes | None]:
    """Resolve a `media/…` relationship target to its package path and payload."""
    if not target.startswith("media/"):
        return "", None
    zip_path = "word/" + target
    if zip_path not in archive.namelist():
        return zip_path, None
    try:
        return zip_path, archive.read(zip_path)
    except Exception:
        return zip_path, None


def describe_drawing(archive: zipfile.ZipFile, part: str, kind: str,
                     drawing: etree._Element, targets: dict[str, str]) -> ImageRow:
    width, height = extent_inches(drawing)

    blip = drawing.find(".//a:blip", namespaces=NS)
    relationship_id = blip.get(f"{{{R_NS}}}embed") if blip is not None else None
    target = targets.get(relationship_id, "") if relationship_id else ""
    zip_path, payload = media_bytes(archive, target)

    size = f"{width:.2f} x {height:.2f}" if width and height else "(unknown)"
    return ImageRow(
        part=part,
        kind=kind,
        relationship_id=relationship_id or "",
        target=target,
        zip_path=zip_path,
        size_inches=size,
        byte_count=str(len(payload)) if payload is not None else "",
    )


def audit(docx: Path) -> tuple[list[ImageRow], Counter]:
    rows: list[ImageRow] = []
    kinds: Counter[str] = Counter()

    with zipfile.ZipFile(docx, "r") as archive:
        parser = etree.XMLParser(recover=True)
        for part in content_parts(archive):
            targets = relationship_targets(archive, part)
            root = etree.fromstring(archive.read(part), parser=parser)
            for kind, xpath in DRAWING_KINDS:
                for drawing in root.findall(xpath, namespaces=NS):
                    kinds[kind] += 1
                    rows.append(describe_drawing(archive, part, kind, drawing, targets))

    return rows, kinds


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit images in a DOCX (inline vs floating, sizes)")
    ap.add_argument("docx", type=Path)
    ap.add_argument("--max_rows", type=int, default=50)
    args = ap.parse_args()

    if not args.docx.exists():
        raise FileNotFoundError(args.docx)

    rows, kinds = audit(args.docx)
    if not rows:
        print("No inline/anchored drawings found in document/header/footer parts.")
        return

    print("IMAGE KINDS")
    for kind, count in kinds.most_common():
        print(f"- {kind}: {count}")

    print("\nROWS (part | kind | size | target)")
    for row in rows[: args.max_rows]:
        print(f"- {row.part} | {row.kind} | {row.size_inches} | {row.target}")
    if len(rows) > args.max_rows:
        print(f"- ... ({len(rows) - args.max_rows} more)")

    if kinds.get("anchor"):
        print("\nWARNING")
        print(ANCHOR_WARNING)
        print("  Strongly recommend: render to PNG and check placement on every affected page.")


if __name__ == "__main__":
    main()
