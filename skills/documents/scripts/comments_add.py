#!/usr/bin/env python3
"""Attach Word comments to paragraphs found by substring match.

`docx_ooxml_patch.py --add-comment` places one comment; review workflows usually
need several, spread over a document, in a single pass. Each `--add` is
`contains=comment text`, and the first paragraph holding that substring gets a
comment spanning the whole paragraph.

The package plumbing is handled for you: `word/comments.xml` is created when
absent and appended to when present, and both the document relationship and the
`[Content_Types].xml` override are added if missing.

Matching reads `<w:t>` *and* `<w:delText>`, so paragraphs that only exist on
the deleted side of a tracked change can still be commented.

    python scripts/comments_add.py in.docx --out out.docx \
      --add "contains=Second section needs clarification" \
      --add "Risk table=Double-check numbers"
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import zipfile

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"w": W_NS, "r": R_NS, "pr": PKG_REL_NS}

DOCUMENT_PART = "word/document.xml"
COMMENTS_PART = "word/comments.xml"
DOCUMENT_RELS_PART = "word/_rels/document.xml.rels"
CONTENT_TYPES_PART = "[Content_Types].xml"

COMMENTS_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
COMMENTS_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
)
REL_ID = re.compile(r"rId(\d+)")


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def dump(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def parse(archive: zipfile.ZipFile, name: str) -> etree._Element:
    return etree.fromstring(archive.read(name))


def revision_stamp() -> str:
    moment = dt.datetime.now(dt.timezone.utc).replace(microsecond=0, tzinfo=None)
    return moment.isoformat() + "Z"


def declare_comments_part(content_types: etree._Element) -> None:
    probe = "//*[local-name()='Override' and @PartName='/word/comments.xml']"
    if content_types.xpath(probe):
        return
    override = etree.SubElement(content_types, f"{{{CT_NS}}}Override")
    override.set("PartName", f"/{COMMENTS_PART}")
    override.set("ContentType", COMMENTS_CONTENT_TYPE)


def relate_comments_part(rels_root: etree._Element) -> None:
    existing = rels_root.xpath("//pr:Relationship", namespaces=NS)
    for relationship in existing:
        if (relationship.get("Type") == COMMENTS_REL_TYPE
                and relationship.get("Target") == "comments.xml"):
            return

    numbers = [int(match.group(1)) for relationship in existing
               if (match := REL_ID.fullmatch(relationship.get("Id", "")))]
    relationship = etree.SubElement(rels_root, f"{{{PKG_REL_NS}}}Relationship")
    relationship.set("Id", f"rId{max(numbers) + 1 if numbers else 1}")
    relationship.set("Type", COMMENTS_REL_TYPE)
    relationship.set("Target", "comments.xml")


def comments_root_or_new(existing: bytes | None) -> etree._Element:
    if existing is not None:
        return etree.fromstring(existing)
    return etree.Element(w("comments"), nsmap={"w": W_NS})


def next_comment_id(comments_root: etree._Element) -> int:
    used = []
    for comment in comments_root.xpath("//w:comment", namespaces=NS):
        try:
            used.append(int(comment.get(w("id"))))
        except (TypeError, ValueError):
            continue
    return max(used) + 1 if used else 0


def matchable_text(paragraph: etree._Element) -> str:
    """Paragraph text including deletions, so tracked documents still match."""
    return "".join(paragraph.xpath(".//w:t/text() | .//w:delText/text()", namespaces=NS))


def find_paragraph(document_root: etree._Element, needle: str, ignore_case: bool):
    wanted = needle.lower() if ignore_case else needle
    for paragraph in document_root.xpath(".//w:p", namespaces=NS):
        text = matchable_text(paragraph)
        if wanted in (text.lower() if ignore_case else text):
            return paragraph
    return None


def anchor_comment(paragraph: etree._Element, comment_id: int) -> None:
    """Wrap the whole paragraph in a comment range and add the reference run."""
    start = etree.Element(w("commentRangeStart"))
    start.set(w("id"), str(comment_id))
    paragraph.insert(0, start)

    end = etree.Element(w("commentRangeEnd"))
    end.set(w("id"), str(comment_id))
    paragraph.append(end)

    reference = etree.SubElement(etree.SubElement(paragraph, w("r")), w("commentReference"))
    reference.set(w("id"), str(comment_id))


def append_comment(comments_root: etree._Element, comment_id: int, text: str, author: str) -> None:
    comment = etree.SubElement(comments_root, w("comment"))
    comment.set(w("id"), str(comment_id))
    comment.set(w("author"), author)
    comment.set(w("date"), revision_stamp())
    etree.SubElement(etree.SubElement(etree.SubElement(comment, w("p")), w("r")), w("t")).text = text


def add_comments(in_docx: str, out_docx: str, additions: list[tuple[str, str]], author: str,
                 ignore_case: bool = False, require_all: bool = False) -> None:
    with zipfile.ZipFile(in_docx, "r") as source:
        names = source.namelist()
        document_root = parse(source, DOCUMENT_PART)
        comments_root = comments_root_or_new(
            source.read(COMMENTS_PART) if COMMENTS_PART in names else None
        )

        content_types = parse(source, CONTENT_TYPES_PART)
        declare_comments_part(content_types)

        rels_root = parse(source, DOCUMENT_RELS_PART)
        relate_comments_part(rels_root)

        comment_id = next_comment_id(comments_root)
        added = 0
        unmatched: list[str] = []

        for contains, comment_text in additions:
            paragraph = find_paragraph(document_root, contains, ignore_case)
            if paragraph is None:
                unmatched.append(contains)
                print(f"[warn] no paragraph matched contains={contains!r}")
                continue
            anchor_comment(paragraph, comment_id)
            append_comment(comments_root, comment_id, comment_text, author=author)
            comment_id += 1
            added += 1

        rewritten = {
            CONTENT_TYPES_PART: dump(content_types),
            DOCUMENT_RELS_PART: dump(rels_root),
            DOCUMENT_PART: dump(document_root),
            COMMENTS_PART: dump(comments_root),
        }

        with zipfile.ZipFile(out_docx, "w", zipfile.ZIP_DEFLATED) as destination:
            for info in source.infolist():
                name = info.filename
                payload = rewritten[name] if name in rewritten else source.read(name)
                destination.writestr(name, payload)
            if COMMENTS_PART not in names:
                destination.writestr(COMMENTS_PART, rewritten[COMMENTS_PART])

    if require_all and unmatched:
        raise SystemExit(
            f"[comments_add] {len(unmatched)} patterns were not matched: {unmatched}"
        )

    print(f"[OK] wrote {out_docx} (added_comments={added}, unmatched_patterns={len(unmatched)})")


def parse_addition(spec: str) -> tuple[str, str]:
    if "=" not in spec:
        raise SystemExit("--add must be formatted as contains=comment text")
    contains, comment_text = spec.split("=", 1)
    return contains, comment_text


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Add multiple Word comments by paragraph substring match"
    )
    ap.add_argument("in_docx")
    ap.add_argument("--out", required=True)
    ap.add_argument("--author", default="Editor")
    ap.add_argument("--add", action="append", default=[],
                    help="Add a comment: contains=comment text (repeatable)")
    ap.add_argument("--ignore_case", action="store_true",
                    help="Case-insensitive substring matching")
    ap.add_argument("--require_all", action="store_true",
                    help="Fail if any --add pattern does not match a paragraph")
    args = ap.parse_args()

    additions = [parse_addition(spec) for spec in args.add]
    if not additions:
        raise SystemExit("Provide at least one --add")

    add_comments(args.in_docx, args.out, additions, author=args.author,
                 ignore_case=args.ignore_case, require_all=args.require_all)


if __name__ == "__main__":
    main()
