"""Attach a comment or reply to a DOCX document.

Works on an unpacked package directory or directly on a .docx/.dotx file
(which is unpacked to a scratch directory, updated, and repacked).

Usage:
    python comment.py unpacked/ "Worth another look"
    python comment.py unpacked/ "Agreed" --parent 0
    python comment.py contract.docx "Cap seems low" -o annotated.docx
    python comment.py annotated.docx "Reply" --parent 0 -o threaded.docx

Comment ids default to the lowest free id (max existing + 1); pass --id to
choose one explicitly.  Plain text is XML-escaped for you; pass --raw when
the text is already escaped (e.g. it contains &amp; or &#x2019;).

The comment is only *defined* by this script.  To make it visible, anchor it
in word/document.xml as the printed guidance shows.
"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from lxml import etree

from office.helpers import opc_target, rezip, safe_extract

TEMPLATE_DIR = Path(__file__).parent / "templates"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "w16cid": "http://schemas.microsoft.com/office/word/2016/wordml/cid",
    "w16cex": "http://schemas.microsoft.com/office/word/2018/wordml/cex",
}
NS_PACKAGE_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"

#: Satellite parts a comment thread needs: file name, relationship type,
#: and content-type override.
_COMMENT_PARTS = (
    (
        "comments.xml",
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml",
    ),
    (
        "commentsExtended.xml",
        "http://schemas.microsoft.com/office/2011/relationships/commentsExtended",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtended+xml",
    ),
    (
        "commentsIds.xml",
        "http://schemas.microsoft.com/office/2016/09/relationships/commentsIds",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.commentsIds+xml",
    ),
    (
        "commentsExtensible.xml",
        "http://schemas.microsoft.com/office/2018/08/relationships/commentsExtensible",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtensible+xml",
    ),
)

_COMMENT_FRAGMENT = (
    '<w:comment w:id="{cid}" w:author="{author}" w:date="{stamp}" w:initials="{initials}">'
    '<w:p w14:paraId="{para}" w14:textId="77777777">'
    "<w:r><w:rPr><w:rStyle w:val=\"CommentReference\"/></w:rPr><w:annotationRef/></w:r>"
    "<w:r><w:rPr><w:color w:val=\"000000\"/><w:sz w:val=\"20\"/><w:szCs w:val=\"20\"/></w:rPr>"
    '<w:t xml:space="preserve">{body}</w:t></w:r>'
    "</w:p></w:comment>"
)

_ANCHOR_GUIDANCE = """
Anchor the comment in word/document.xml (markers sit between runs, never inside one):
  <w:commentRangeStart w:id="{cid}"/>
  <w:r>...</w:r>
  <w:commentRangeEnd w:id="{cid}"/>
  <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="{cid}"/></w:r>"""

_REPLY_GUIDANCE = """
Nest the reply's markers inside parent {pid}'s (between runs, never inside one):
  <w:commentRangeStart w:id="{pid}"/><w:commentRangeStart w:id="{cid}"/>
  <w:r>...</w:r>
  <w:commentRangeEnd w:id="{cid}"/><w:commentRangeEnd w:id="{pid}"/>
  <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="{pid}"/></w:r>
  <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="{cid}"/></w:r>"""


def _fresh_hex_id() -> str:
    return f"{random.randint(0, 0x7FFFFFFE):08X}"


def _parse(path: Path) -> etree._ElementTree:
    return etree.parse(
        str(path), etree.XMLParser(remove_blank_text=False, resolve_entities=False)
    )


def _graft_fragment(part_path: Path, fragment: str) -> None:
    """Parse *fragment* with the comment namespaces in scope and append it."""
    tree = _parse(part_path)
    declarations = " ".join(f'xmlns:{prefix}="{uri}"' for prefix, uri in NS.items())
    wrapper = etree.fromstring(f"<__graft__ {declarations}>{fragment}</__graft__>")
    for child in list(wrapper):
        tree.getroot().append(child)
    tree.write(
        str(part_path), xml_declaration=True, encoding="UTF-8", standalone=True
    )


def _comment_ids(comments_path: Path) -> list[int]:
    if not comments_path.exists():
        return []
    ids = []
    for comment in _parse(comments_path).getroot().iter(f"{{{NS['w']}}}comment"):
        try:
            ids.append(int(comment.get(f"{{{NS['w']}}}id")))
        except (TypeError, ValueError):
            continue
    return ids


def _para_id_of(comments_path: Path, comment_id: int) -> str | None:
    if not comments_path.exists():
        return None
    for comment in _parse(comments_path).getroot().iter(f"{{{NS['w']}}}comment"):
        if comment.get(f"{{{NS['w']}}}id") != str(comment_id):
            continue
        for para in comment.iter(f"{{{NS['w']}}}p"):
            para_id = para.get(f"{{{NS['w14']}}}paraId")
            if para_id:
                return para_id
    return None


def _register_comment_parts(unpacked: Path) -> None:
    """Add relationship and content-type entries for the comment parts."""
    rels_path = unpacked / "word" / "_rels" / "document.xml.rels"
    if rels_path.is_file():
        tree = _parse(rels_path)
        root = tree.getroot()
        highest = 0
        known_targets = set()
        comment_types = {rel_type for _, rel_type, _ in _COMMENT_PARTS}
        for rel in root.iter(f"{{{NS_PACKAGE_RELS}}}Relationship"):
            rid = rel.get("Id", "")
            if rid.startswith("rId") and rid[3:].isdigit():
                highest = max(highest, int(rid[3:]))
            if rel.get("Type") in comment_types:
                part = opc_target(
                    rel.get("Target", ""), "word/document.xml",
                    rel.get("TargetMode", ""),
                )
                if part is not None:
                    known_targets.add(part)
        changed = False
        for filename, rel_type, _ in _COMMENT_PARTS:
            if opc_target(filename, "word/document.xml") in known_targets:
                continue
            highest += 1
            node = etree.SubElement(root, f"{{{NS_PACKAGE_RELS}}}Relationship")
            node.set("Id", f"rId{highest}")
            node.set("Type", rel_type)
            node.set("Target", filename)
            changed = True
        if changed:
            tree.write(
                str(rels_path), xml_declaration=True, encoding="UTF-8",
                standalone=True,
            )

    manifest_path = unpacked / "[Content_Types].xml"
    if manifest_path.is_file():
        tree = _parse(manifest_path)
        root = tree.getroot()
        declared = {
            node.get("PartName")
            for node in root.iter(f"{{{NS_CONTENT_TYPES}}}Override")
        }
        changed = False
        for filename, _, content_type in _COMMENT_PARTS:
            part_name = f"/word/{filename}"
            if part_name in declared:
                continue
            node = etree.SubElement(root, f"{{{NS_CONTENT_TYPES}}}Override")
            node.set("PartName", part_name)
            node.set("ContentType", content_type)
            changed = True
        if changed:
            tree.write(
                str(manifest_path), xml_declaration=True, encoding="UTF-8",
                standalone=True,
            )


def add_comment(
    unpacked_dir,
    text: str,
    comment_id: int | None = None,
    author: str = "User",
    initials: str = "U",
    parent_id: int | None = None,
    raw: bool = False,
) -> tuple[int, str, str]:
    """Add *text* as a comment under an unpacked DOCX; return (id, paraId, msg)."""
    unpacked_dir = Path(unpacked_dir)
    body = text if raw else xml_escape(text)
    author = xml_escape(author, {'"': "&quot;"})
    initials = xml_escape(initials, {'"': "&quot;"})

    word_dir = unpacked_dir / "word"
    if not word_dir.is_dir():
        raise FileNotFoundError(f"{word_dir} not found (not an unpacked DOCX?)")

    comments_path = word_dir / "comments.xml"
    existing_ids = _comment_ids(comments_path)
    if comment_id is None:
        comment_id = max(existing_ids, default=-1) + 1
    if comment_id < 0:
        raise ValueError("Comment id must be non-negative")
    if comment_id in existing_ids:
        raise ValueError(f"Comment id {comment_id} is already taken")

    parent_para = None
    if parent_id is not None:
        parent_para = _para_id_of(comments_path, parent_id)
        if parent_para is None:
            raise ValueError(f"Parent comment {parent_id} not found")

    para_id, durable_id = _fresh_hex_id(), _fresh_hex_id()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for filename, _, _ in _COMMENT_PARTS:
        part = word_dir / filename
        if not part.exists():
            shutil.copy(TEMPLATE_DIR / filename, part)
    _register_comment_parts(unpacked_dir)

    _graft_fragment(
        comments_path,
        _COMMENT_FRAGMENT.format(
            cid=comment_id, author=author, stamp=stamp,
            initials=initials, para=para_id, body=body,
        ),
    )

    threading = f' w15:paraIdParent="{parent_para}"' if parent_para else ""
    _graft_fragment(
        word_dir / "commentsExtended.xml",
        f'<w15:commentEx w15:paraId="{para_id}"{threading} w15:done="0"/>',
    )
    _graft_fragment(
        word_dir / "commentsIds.xml",
        f'<w16cid:commentId w16cid:paraId="{para_id}" w16cid:durableId="{durable_id}"/>',
    )
    _graft_fragment(
        word_dir / "commentsExtensible.xml",
        f'<w16cex:commentExtensible w16cex:durableId="{durable_id}" w16cex:dateUtc="{stamp}"/>',
    )

    kind = "reply" if parent_id is not None else "comment"
    return comment_id, para_id, f"Added {kind} id={comment_id} (paraId={para_id})"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Attach a comment to a DOCX (unpacked directory or packed file)."
    )
    parser.add_argument("input", help="Unpacked DOCX directory OR a .docx/.dotx file")
    parser.add_argument("text", help="Comment text (XML-escaped unless --raw)")
    parser.add_argument("--raw", action="store_true",
                        help="Text is already XML-escaped; insert verbatim")
    parser.add_argument("--id", type=int, dest="comment_id",
                        help="Comment id (default: lowest free id)")
    parser.add_argument("--author", default="User", help="Author name")
    parser.add_argument("--initials", default="U", help="Author initials")
    parser.add_argument("--parent", type=int, help="Parent comment id (a reply)")
    parser.add_argument("-o", "--output",
                        help="Output .docx path (packed input only; fresh path)")
    args = parser.parse_args()

    src = Path(args.input)
    try:
        if src.is_dir():
            if args.output:
                parser.error("--output applies to packed input; directories are edited in place")
            comment_id, _, message = add_comment(
                src, args.text, comment_id=args.comment_id, author=args.author,
                initials=args.initials, parent_id=args.parent, raw=args.raw,
            )
            print(message)
        elif src.is_file() and src.suffix.lower() in (".docx", ".dotx"):
            if not args.output:
                parser.error("Packed input requires --output with a new path")
            out = Path(args.output)
            if out.exists() or out.is_symlink():
                parser.error("Choose a new output path")
            with tempfile.TemporaryDirectory() as staging:
                staging_dir = Path(staging)
                with zipfile.ZipFile(src) as archive:
                    safe_extract(archive, staging_dir)
                comment_id, _, message = add_comment(
                    staging_dir, args.text, comment_id=args.comment_id,
                    author=args.author, initials=args.initials,
                    parent_id=args.parent, raw=args.raw,
                )
                rezip(staging_dir, out)
            print(message)
            print(f"Wrote {out} (comment defined; anchor it in word/document.xml)")
        else:
            print(
                f"Error: {src} is neither a directory nor a .docx/.dotx file",
                file=sys.stderr,
            )
            sys.exit(1)
    except (FileNotFoundError, ValueError, zipfile.BadZipFile,
            etree.XMLSyntaxError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    guidance = _REPLY_GUIDANCE if args.parent is not None else _ANCHOR_GUIDANCE
    print(guidance.format(cid=comment_id, pid=args.parent))


if __name__ == "__main__":
    main()
