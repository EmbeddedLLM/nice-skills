#!/usr/bin/env python3
"""Delete every comment from a DOCX, anchors and parts alike.

For the "clean final" deliverable. Four things have to go together, or Word
either shows ghosts or refuses the file:

* the anchors in every story part — `w:commentRangeStart`, `w:commentRangeEnd`,
  and the `w:commentReference` run that follows a range;
* the note parts themselves — `word/comments.xml` plus
  `word/commentsExtended.xml` on files written by newer Word;
* the relationships that point at those parts;
* the `[Content_Types].xml` overrides declaring them.

Story parts means the main document and every numbered header and footer,
because comments anchored in a header are easy to forget.

    python scripts/comments_strip.py in.docx --out out.docx
"""

from __future__ import annotations

import argparse
import re
import zipfile

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"w": W_NS, "rel": REL_NS, "ct": CT_NS}

MAIN_PART = "word/document.xml"
RELS_PART = "word/_rels/document.xml.rels"
CONTENT_TYPES_PART = "[Content_Types].xml"
COMMENT_PARTS = ("word/comments.xml", "word/commentsExtended.xml")

ANCHOR_TAGS = ("commentRangeStart", "commentRangeEnd", "commentReference")
COMMENT_REL_TYPES = frozenset({
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
    "http://schemas.microsoft.com/office/2011/relationships/commentsExtended",
})
HEADER_OR_FOOTER = re.compile(r"word/(?:header|footer)\d+\.xml$")


def stats_template() -> dict[str, int]:
    return {
        "markup_removed": 0,
        "comments_part_removed": 0,
        "comments_extended_part_removed": 0,
        "rels_updated": 0,
        "content_types_updated": 0,
    }


def parse(archive: zipfile.ZipFile, name: str) -> etree._Element:
    return etree.fromstring(archive.read(name))


def dump(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def story_parts(archive: zipfile.ZipFile) -> list[str]:
    """Main document first, then any numbered headers and footers."""
    extra = [n for n in archive.namelist() if HEADER_OR_FOOTER.match(n)]
    return [MAIN_PART, *extra]


def drop_anchors(root: etree._Element) -> int:
    removed = 0
    for tag in ANCHOR_TAGS:
        for element in reversed(root.xpath(f".//w:{tag}", namespaces=NS)):
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
                removed += 1
    return removed


def drop_comment_relationships(rels_root: etree._Element) -> bool:
    dropped = False
    for relationship in list(rels_root.findall(f"{{{REL_NS}}}Relationship")):
        if relationship.get("Type") in COMMENT_REL_TYPES:
            rels_root.remove(relationship)
            dropped = True
    return dropped


def drop_comment_overrides(content_types: etree._Element) -> bool:
    dropped = False
    declared = {f"/{part}" for part in COMMENT_PARTS}
    for override in list(content_types.findall(f"{{{CT_NS}}}Override")):
        if (override.get("PartName") or "") in declared:
            content_types.remove(override)
            dropped = True
    return dropped


def strip_comments(in_docx: str, out_docx: str) -> dict[str, int]:
    stats = stats_template()

    with zipfile.ZipFile(in_docx, "r") as source:
        names = source.namelist()
        rewritten: dict[str, bytes] = {}

        for part in story_parts(source):
            root = parse(source, part)
            count = drop_anchors(root)
            if count:
                stats["markup_removed"] += count
                rewritten[part] = dump(root)

        if RELS_PART in names:
            rels_root = parse(source, RELS_PART)
            if drop_comment_relationships(rels_root):
                stats["rels_updated"] = 1
                rewritten[RELS_PART] = dump(rels_root)

        if CONTENT_TYPES_PART in names:
            content_types = parse(source, CONTENT_TYPES_PART)
            if drop_comment_overrides(content_types):
                stats["content_types_updated"] = 1
                rewritten[CONTENT_TYPES_PART] = dump(content_types)

        with zipfile.ZipFile(out_docx, "w", zipfile.ZIP_DEFLATED) as destination:
            for info in source.infolist():
                name = info.filename
                if name in COMMENT_PARTS:
                    key = ("comments_part_removed" if name.endswith("comments.xml")
                           else "comments_extended_part_removed")
                    stats[key] = 1
                    continue
                payload = rewritten[name] if name in rewritten else source.read(name)
                destination.writestr(name, payload)

    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_docx")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    stats = strip_comments(args.in_docx, args.out)
    print(f"[OK] wrote {args.out} | {stats}")


if __name__ == "__main__":
    main()
