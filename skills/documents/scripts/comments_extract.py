#!/usr/bin/env python3
"""Export classic Word comments and their paragraph anchors as UTF-8 JSON.

Usage: comments_extract.py review.docx --out feedback.json
Requires lxml and the bundled word_package module. Reads body/header/footer
anchors; snippets identify surrounding paragraphs, not exact selected ranges.
Threaded-comment extension metadata is not interpreted. Input is never written.
"""
import argparse
import json
from pathlib import Path

from word_package import Package, tag, text_of


def paragraph_content(paragraph):
    symbols = {tag("tab"): "\t", tag("br"): "\n", tag("cr"): "\n"}
    return "".join((node.text or "") if node.tag == tag("t") else symbols.get(node.tag, "")
                   for node in paragraph.iter()).strip()


def extract(in_docx):
    package = Package(in_docx)
    comments = {}
    if "word/comments.xml" in package.parts:
        for entry in package.xml("word/comments.xml").iter(tag("comment")):
            identifier = entry.get(tag("id"))
            if identifier is None:
                continue
            lines = [paragraph_content(p) for p in entry.findall(tag("p"))]
            comments[identifier] = {
                "id": identifier,
                **{key: entry.get(tag(key)) for key in ("author", "date", "initials")},
                "resolved": entry.get(tag("done")) == "1",
                "text": "\n".join(line for line in lines if line) or text_of(entry).strip(),
                "anchors": [],
            }
    for part in package.stories():
        grouped = {}
        for paragraph in package.xml(part).iter(tag("p")):
            for location, marker_name in (("start", "commentRangeStart"), ("end", "commentRangeEnd")):
                for marker in paragraph.iter(tag(marker_name)):
                    identifier = marker.get(tag("id"))
                    if identifier in comments:
                        grouped.setdefault(identifier, []).append({
                            "where": location, "text": paragraph_content(paragraph)[:200]})
        for identifier, paragraphs in grouped.items():
            comments[identifier]["anchors"].append({"part": part, "paragraphs": paragraphs})
    ordered = sorted(comments, key=lambda key: (0, int(key)) if key.isdecimal() else (1, key))
    return {"file": str(in_docx), "comment_count": len(comments),
            "comments": [comments[key] for key in ordered]}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("in_docx")
    cli.add_argument("--out", required=True)
    options = cli.parse_args()
    payload = extract(options.in_docx)
    Path(options.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {options.out} ({payload['comment_count']} comments)")


if __name__ == "__main__":
    main()
