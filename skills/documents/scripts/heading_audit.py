#!/usr/bin/env python3
"""Quick structural QA on a document's heading outline.

Three signals, cheap to compute and usually enough to explain a broken table
of contents:

* which `Heading N` styles the document actually uses;
* places where the outline drops a level (Heading 1 straight to Heading 3);
* paragraphs carrying numbering without a heading style — the shape a
  hand-numbered heading takes when it should have been styled.

This is a fast pre-render check, not a style linter; see `style_lint.py` for
formatting drift.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document

TEXT_PREVIEW = 80


@dataclass
class OutlineFindings:
    level_counts: Counter = field(default_factory=Counter)
    level_jumps: list[str] = field(default_factory=list)
    numbered_without_style: list[str] = field(default_factory=list)


def heading_level(style_name: str | None) -> int | None:
    """Level of a `Heading N` style name, or None when it is not one."""
    if not style_name:
        return None
    words = style_name.strip().lower().split()
    if len(words) < 2 or words[0] != "heading":
        return None
    try:
        return int(words[1])
    except ValueError:
        return None


def carries_numbering(paragraph) -> bool:
    """python-docx has no numbering API, so read the paragraph properties."""
    properties = paragraph._p.pPr
    return properties is not None and properties.numPr is not None


def scan(document: Document) -> OutlineFindings:
    findings = OutlineFindings()
    previous_level: int | None = None

    for position, paragraph in enumerate(document.paragraphs, start=1):
        style_name = getattr(paragraph.style, "name", None)
        level = heading_level(style_name)

        if level is not None:
            findings.level_counts[level] += 1
            if previous_level is not None and level > previous_level + 1:
                findings.level_jumps.append(
                    f"p#{position}: Heading {previous_level} → Heading {level}: "
                    f"{paragraph.text[:TEXT_PREVIEW]!r}"
                )
            previous_level = level

        elif carries_numbering(paragraph) and (paragraph.text or "").strip():
            findings.numbered_without_style.append(
                f"p#{position}: style={style_name!r} text={paragraph.text.strip()[:TEXT_PREVIEW]!r}"
            )

    return findings


def print_findings(label: str, items: list[str], limit: int) -> None:
    print(f"\n{label}")
    for item in items[:limit]:
        print(f"- {item}")
    if len(items) > limit:
        print(f"- ... ({len(items) - limit} more)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit heading hierarchy + numbering usage in a DOCX")
    ap.add_argument("docx", type=Path)
    ap.add_argument("--max_findings", type=int, default=20)
    args = ap.parse_args()

    if not args.docx.exists():
        raise FileNotFoundError(args.docx)

    findings = scan(Document(str(args.docx)))

    print("HEADING STYLE COUNTS")
    if not findings.level_counts:
        print("- (no Heading styles found)")
    else:
        for level in sorted(findings.level_counts):
            print(f"- Heading {level}: {findings.level_counts[level]}")

    if findings.level_jumps:
        print_findings("POTENTIAL HEADING LEVEL JUMPS (review)",
                       findings.level_jumps, args.max_findings)

    if findings.numbered_without_style:
        print_findings("NUMBERING WITHOUT HEADING STYLE (common TOC issue)",
                       findings.numbered_without_style, args.max_findings)

    print("\nREMINDER")
    print(
        "- TOC relies on Heading styles (Heading 1/2/3...). Avoid manual numbering + direct formatting for headings."
    )


if __name__ == "__main__":
    main()
