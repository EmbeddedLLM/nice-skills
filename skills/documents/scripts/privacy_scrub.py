#!/usr/bin/env python3
"""Strip the metadata that identifies people and machines from a DOCX.

Before a file goes outside the organisation, four kinds of residue are worth
removing:

* `docProps/core.xml` — `dc:creator` and `cp:lastModifiedBy` are blanked;
* `docProps/custom.xml` — dropped entirely, together with the package
  relationship that points at it and its content-type override;
* `w:rsid*` attributes — Word's revision-session identifiers, sprinkled through
  the story parts (document, headers, footers, footnotes, endnotes);
* nothing else. Content is untouched.

Personal data *inside* the text is a redaction problem, not a metadata one —
see `redact_docx.py`.

    python scripts/privacy_scrub.py in.docx --out out.docx
"""

from __future__ import annotations

import argparse
import re
import zipfile

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
NS = {"w": W_NS, "rel": REL_NS, "ct": CT_NS, "cp": CP_NS, "dc": DC_NS}

CORE_PART = "docProps/core.xml"
CUSTOM_PART = "docProps/custom.xml"
PACKAGE_RELS = "_rels/.rels"
CONTENT_TYPES_PART = "[Content_Types].xml"

RSID_PREFIX = f"{{{W_NS}}}rsid"
AUTHOR_XPATHS = (".//dc:creator", ".//cp:lastModifiedBy")
STORY_PART = re.compile(
    r"word/(?:document|footnotes|endnotes|header\d+|footer\d+)\.xml$"
)


def parse(archive: zipfile.ZipFile, name: str) -> etree._Element:
    return etree.fromstring(archive.read(name))


def dump(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def story_parts(archive: zipfile.ZipFile) -> list[str]:
    return [name for name in archive.namelist() if STORY_PART.match(name)]


def remove_rsid_attributes(root: etree._Element) -> int:
    """Drop every `w:rsid*` attribute; they only record editing sessions."""
    removed = 0
    for element in root.iter():
        for attribute in [k for k in element.attrib if k.startswith(RSID_PREFIX)]:
            del element.attrib[attribute]
            removed += 1
    return removed


def blank_author_fields(core_root: etree._Element) -> bool:
    edited = False
    for xpath in AUTHOR_XPATHS:
        for element in core_root.xpath(xpath, namespaces=NS):
            if (element.text or "").strip():
                element.text = ""
                edited = True
    return edited


def remove_custom_property_relationship(rels_root: etree._Element) -> bool:
    # From the package root the target reads "../docProps/custom.xml".
    edited = False
    for relationship in list(rels_root.findall(f"{{{REL_NS}}}Relationship")):
        if (relationship.get("Target") or "").endswith(CUSTOM_PART):
            rels_root.remove(relationship)
            edited = True
    return edited


def remove_custom_property_override(content_types: etree._Element) -> bool:
    edited = False
    for override in list(content_types.findall(f"{{{CT_NS}}}Override")):
        if (override.get("PartName") or "") == f"/{CUSTOM_PART}":
            content_types.remove(override)
            edited = True
    return edited


def scrub(in_docx: str, out_docx: str) -> dict[str, int]:
    stats = {
        "rsid_attrs_removed": 0,
        "core_props_scrubbed": 0,
        "custom_props_removed": 0,
        "rels_updated": 0,
        "content_types_updated": 0,
    }

    with zipfile.ZipFile(in_docx, "r") as source:
        names = source.namelist()
        rewritten: dict[str, bytes] = {}

        for part in story_parts(source):
            root = parse(source, part)
            count = remove_rsid_attributes(root)
            if count:
                stats["rsid_attrs_removed"] += count
                rewritten[part] = dump(root)

        if CORE_PART in names:
            core_root = parse(source, CORE_PART)
            if blank_author_fields(core_root):
                rewritten[CORE_PART] = dump(core_root)
                stats["core_props_scrubbed"] = 1

        if PACKAGE_RELS in names:
            rels_root = parse(source, PACKAGE_RELS)
            if remove_custom_property_relationship(rels_root):
                rewritten[PACKAGE_RELS] = dump(rels_root)
                stats["rels_updated"] = 1

        if CONTENT_TYPES_PART in names:
            content_types = parse(source, CONTENT_TYPES_PART)
            if remove_custom_property_override(content_types):
                rewritten[CONTENT_TYPES_PART] = dump(content_types)
                stats["content_types_updated"] = 1

        with zipfile.ZipFile(out_docx, "w", zipfile.ZIP_DEFLATED) as destination:
            for info in source.infolist():
                name = info.filename
                if name == CUSTOM_PART:
                    stats["custom_props_removed"] = 1
                    continue
                payload = rewritten[name] if name in rewritten else source.read(name)
                destination.writestr(name, payload)

    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_docx")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    stats = scrub(args.in_docx, args.out)
    print(f"[OK] wrote {args.out} | {stats}")


if __name__ == "__main__":
    main()
