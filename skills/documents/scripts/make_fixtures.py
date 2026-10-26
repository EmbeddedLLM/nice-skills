#!/usr/bin/env python3
"""Generate small, reproducible DOCX fixtures for edge-case testing.

Two OOXML constructs are painful to produce by hand and are responsible for a
disproportionate share of "this looks wrong" reports, so they get fixtures:

* `tracked_changes_fixture.docx` — a paragraph whose run has been replaced by a
  `w:del` / `w:ins` pair, with `w:trackRevisions` enabled in settings;
* `watermark_fixture.docx` — a header carrying a VML WordArt shape whose
  textpath reads `DRAFT`.

This is not a general document generator. It emits exactly these two files so
downstream tools can be tested deterministically. Note that headless
LibreOffice does not draw every VML variant; the watermark fixture exists for
OOXML auditing and removal, not for pixel comparison.

    python scripts/make_fixtures.py --outdir work/fixtures
    python scripts/make_fixtures.py --outdir work/fixtures --only tracked
"""

from __future__ import annotations

import argparse
import os
import re
import zipfile
from datetime import datetime, timezone

from docx import Document
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
V_NS = "urn:schemas-microsoft-com:vml"
O_NS = "urn:schemas-microsoft-com:office:office"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W_NS, "v": V_NS, "o": O_NS, "r": R_NS}

DOCUMENT_PART = "word/document.xml"
SETTINGS_PART = "word/settings.xml"
HEADER_PART = re.compile(r"word/header\d+\.xml")

FIXTURE_AUTHOR = "FixtureMaker"
TRACKED_MARKER = "REPLACE_ME"
TRACKED_REPLACEMENT = "INSERTED_TEXT"
WATERMARK_TEXT = "DRAFT"


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_part(archive: zipfile.ZipFile, name: str) -> etree._Element:
    return etree.fromstring(archive.read(name))


def serialise(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def repackage(source_path: str, destination_path: str, replacements: dict[str, bytes]) -> None:
    """Copy a package, substituting given parts and adding any new ones."""
    with zipfile.ZipFile(source_path, "r") as source, \
            zipfile.ZipFile(destination_path, "w", zipfile.ZIP_DEFLATED) as destination:
        original = [info.filename for info in source.infolist()]
        for name in original:
            payload = replacements[name] if name in replacements else source.read(name)
            destination.writestr(name, payload)
        for name, payload in replacements.items():
            if name not in original:
                destination.writestr(name, payload)


def revision_wrapper(tag: str, text_tag: str, text: str, revision_id: str) -> etree._Element:
    """One `w:del` or `w:ins` element holding a single run."""
    wrapper = etree.Element(f"{{{W_NS}}}{tag}", nsmap={"w": W_NS, "r": R_NS})
    wrapper.set(f"{{{W_NS}}}id", revision_id)
    wrapper.set(f"{{{W_NS}}}author", FIXTURE_AUTHOR)
    wrapper.set(f"{{{W_NS}}}date", timestamp())
    run = etree.SubElement(wrapper, f"{{{W_NS}}}r")
    etree.SubElement(run, f"{{{W_NS}}}{text_tag}").text = text
    return wrapper


def turn_tracking_on(settings: etree._Element) -> None:
    for existing in settings.xpath(".//w:trackRevisions", namespaces=NS):
        existing.getparent().remove(existing)
    settings.append(etree.Element(f"{{{W_NS}}}trackRevisions"))


def make_tracked_changes_fixture(out_path: str) -> None:
    staging = out_path + ".base.docx"

    document = Document()
    document.add_heading("Tracked Changes Fixture", level=1)
    sentence = document.add_paragraph("Sentence with a pending edit: ")
    sentence.add_run(TRACKED_MARKER)
    document.add_paragraph("End of fixture.")
    document.save(staging)

    with zipfile.ZipFile(staging, "r") as source:
        document_root = read_part(source, DOCUMENT_PART)
        settings = read_part(source, SETTINGS_PART)

    marked = document_root.xpath(f".//w:r[w:t='{TRACKED_MARKER}']", namespaces=NS)
    if not marked:
        raise RuntimeError(
            f"Could not find marker text {TRACKED_MARKER} in generated document.xml"
        )

    # Swap the plain run for a deletion of the old text plus an insertion of the new.
    run = marked[0]
    paragraph = run.getparent()
    position = paragraph.index(run)
    paragraph.remove(run)
    paragraph.insert(position, revision_wrapper("del", "delText", TRACKED_MARKER, "1"))
    paragraph.insert(position + 1, revision_wrapper("ins", "t", TRACKED_REPLACEMENT, "2"))

    turn_tracking_on(settings)
    repackage(staging, out_path, {
        DOCUMENT_PART: serialise(document_root),
        SETTINGS_PART: serialise(settings),
    })
    os.remove(staging)


def watermark_paragraph(text: str) -> etree._Element:
    """A paragraph holding one VML WordArt shape, the classic Word watermark."""
    paragraph = etree.Element(f"{{{W_NS}}}p")
    picture = etree.SubElement(etree.SubElement(paragraph, f"{{{W_NS}}}r"), f"{{{W_NS}}}pict")

    shape = etree.SubElement(picture, f"{{{V_NS}}}shape")
    shape.set("id", "PowerPlusWaterMarkObject1")
    shape.set(f"{{{O_NS}}}spid", "_x0000_s1025")
    shape.set("type", "#_x0000_t136")
    shape.set("style",
              "position:absolute;margin-left:0;margin-top:0;width:468pt;height:234pt;rotation:315")
    shape.set("fillcolor", "#d0d0d0")
    shape.set("stroked", "f")

    etree.SubElement(shape, f"{{{V_NS}}}fill").set("opacity", ".25")
    textpath = etree.SubElement(shape, f"{{{V_NS}}}textpath")
    textpath.set("style", "font-family:'Calibri';font-size:1pt")
    textpath.set("string", text)
    return paragraph


def inject_watermark(header_root: etree._Element, text: str) -> None:
    container = header_root.find("w:body", namespaces=NS) or header_root
    paragraph = watermark_paragraph(text)
    if len(container):
        container.insert(0, paragraph)
    else:
        container.append(paragraph)


def make_watermark_fixture(out_path: str) -> None:
    staging = out_path + ".base.docx"

    document = Document()
    # Force python-docx to materialize a header part.
    header = document.sections[0].header
    if header.paragraphs:
        header.paragraphs[0].text = ""
    else:
        header.add_paragraph("")

    document.add_heading("Watermark Fixture", level=1)
    document.add_paragraph(
        f"This file contains a VML watermark-like header shape with text {WATERMARK_TEXT}."
    )
    document.add_paragraph("LibreOffice headless may not render it; use OOXML audit/removal.")
    document.save(staging)

    with zipfile.ZipFile(staging, "r") as source:
        header_name = next(
            (name for name in source.namelist() if HEADER_PART.fullmatch(name)), None
        )
        if header_name is None:
            raise RuntimeError("No header part found in generated DOCX; cannot inject watermark")
        header_root = read_part(source, header_name)

    inject_watermark(header_root, WATERMARK_TEXT)
    repackage(staging, out_path, {header_name: serialise(header_root)})
    os.remove(staging)


BUILDERS = {
    "tracked": ("tracked_changes_fixture.docx", make_tracked_changes_fixture),
    "watermark": ("watermark_fixture.docx", make_watermark_fixture),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True, help="Directory to write fixtures")
    ap.add_argument(
        "--only",
        choices=["tracked", "watermark", "all"],
        default="all",
        help="Which fixtures to generate",
    )
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    wanted = list(BUILDERS) if args.only == "all" else [args.only]
    for key in wanted:
        filename, builder = BUILDERS[key]
        destination = os.path.join(args.outdir, filename)
        builder(destination)
        print(f"[OK] wrote {destination}")


if __name__ == "__main__":
    main()
