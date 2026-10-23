#!/usr/bin/env python3
"""Redact or anonymize text in a DOCX while keeping the layout intact.

The approach is paragraph-scoped OOXML surgery:

1. join every `<w:t>` in a paragraph into one string;
2. match the rules against that joined string, so a match spanning two runs is
   still found;
3. substitute a fixed-length mask (or a length-matched replacement), which keeps
   line breaks and pagination where they were;
4. write the result back across the original run segmentation, so run
   boundaries and their formatting survive.

Parts covered: `document.xml`, `footnotes.xml`, `endnotes.xml`, every header
and footer, and `comments.xml` when `--include_comments` is passed.

This is a practical "make it shareable" tool, not cryptographic anonymization:
text inside images, charts, embedded objects, and the deleted side of tracked
changes is out of reach.

    python scripts/redact_docx.py in.docx out.docx --emails --phones
    python scripts/redact_docx.py in.docx out.docx --pattern "Acme Corp" --replacement "[REDACTED]"
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

try:
    from docx_ooxml_patch import unzip_docx, zip_docx
except Exception:
    # Standalone fallback so a lone copy of this script still runs.
    import os
    import shutil
    import zipfile

    def unzip_docx(docx_path: Path, out_dir: Path) -> None:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(docx_path, "r") as archive:
            archive.extractall(out_dir)

    def zip_docx(in_dir: Path, out_docx_path: Path) -> None:
        if out_docx_path.exists():
            out_docx_path.unlink()
        with zipfile.ZipFile(out_docx_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for root, _dirs, files in os.walk(in_dir):
                for name in files:
                    absolute = Path(root) / name
                    archive.write(absolute, absolute.relative_to(in_dir).as_posix())


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_PATTERN = re.compile(
    r"(?:(?:\+?\d{1,3}[\s-]?)?(?:\(\d{3}\)|\d{3})[\s-]?)\d{3}[\s-]?\d{4}", re.I
)
ALWAYS_SCANNED = ("document.xml", "footnotes.xml", "endnotes.xml")
COMMENTS_PART_NAME = "comments.xml"
DEFAULT_MASK_CHAR = "█"


@dataclass(frozen=True)
class RedactionRule:
    pattern: re.Pattern[str]
    label: str


@dataclass
class Substitution:
    """How one match is rewritten."""

    mask_char: str = DEFAULT_MASK_CHAR
    replacement: str | None = None
    preserve_length: bool = True

    def text_for(self, length: int) -> str:
        if not self.preserve_length:
            return self.replacement if self.replacement is not None else self.mask_char * length
        if self.replacement is None:
            return self.mask_char * length
        # Repeat or trim the label so the result is exactly `length` characters.
        repeats = length // max(1, len(self.replacement)) + 1
        return (self.replacement * repeats)[:length]


def qn(local: str) -> str:
    return f"{{{W_NS}}}{local}"


def scannable_parts(unzipped: Path, include_comments: bool) -> list[Path]:
    word = unzipped / "word"
    parts = [word / name for name in ALWAYS_SCANNED if (word / name).exists()]
    parts.extend(sorted(word.glob("header*.xml")))
    parts.extend(sorted(word.glob("footer*.xml")))
    if include_comments and (word / COMMENTS_PART_NAME).exists():
        parts.append(word / COMMENTS_PART_NAME)
    return parts


def keep_spaces(text_node: etree._Element) -> None:
    """Word drops edge whitespace unless the node says to preserve it."""
    text = text_node.text or ""
    if text.startswith(" ") or text.endswith(" "):
        text_node.set(XML_SPACE, "preserve")


def non_overlapping_spans(text: str, rules: list[RedactionRule]) -> list[tuple[int, int]]:
    """All rule matches, earliest first, longer wins ties, overlaps dropped."""
    candidates = []
    for rule in rules:
        for match in rule.pattern.finditer(text):
            if match.start() != match.end():
                candidates.append((match.start(), match.end()))

    candidates.sort(key=lambda span: (span[0], -(span[1] - span[0])))

    chosen: list[tuple[int, int]] = []
    covered_until = -1
    for start, end in candidates:
        if start < covered_until:
            continue
        chosen.append((start, end))
        covered_until = end
    return chosen


def redact_paragraph(paragraph: etree._Element, rules: list[RedactionRule],
                     substitution: Substitution) -> int:
    text_nodes = list(paragraph.xpath(".//w:t", namespaces=NS))
    if not text_nodes:
        return 0

    segments = [node.text or "" for node in text_nodes]
    joined = "".join(segments)
    if not joined:
        return 0

    spans = non_overlapping_spans(joined, rules)
    if not spans:
        return 0

    characters = list(joined)
    for start, end in reversed(spans):
        characters[start:end] = list(substitution.text_for(end - start))
    redacted = "".join(characters)

    if substitution.preserve_length and len(redacted) != len(joined):
        raise RuntimeError("Internal error: expected length-preserving rewrite")

    # Pour the result back into the same node boundaries, segment by segment.
    offset = 0
    for node, segment in zip(text_nodes, segments, strict=True):
        node.text = redacted[offset:offset + len(segment)]
        keep_spaces(node)
        offset += len(segment)

    return len(spans)


class Redactor:
    def __init__(self, rules: list[RedactionRule], substitution: Substitution,
                 include_comments: bool) -> None:
        self.rules = rules
        self.substitution = substitution
        self.include_comments = include_comments

    def process_part(self, part: Path) -> tuple[int, int]:
        tree = etree.parse(str(part), etree.XMLParser(remove_blank_text=False))
        paragraphs_touched = redactions = 0

        for paragraph in tree.getroot().xpath(".//w:p", namespaces=NS):
            count = redact_paragraph(paragraph, self.rules, self.substitution)
            if count:
                paragraphs_touched += 1
                redactions += count

        tree.write(str(part), xml_declaration=True, encoding="UTF-8", standalone="yes")
        return paragraphs_touched, redactions

    def run(self, input_docx: Path, output_docx: Path) -> dict:
        stats = {
            "file": str(input_docx),
            "parts_processed": 0,
            "paragraphs_touched": 0,
            "matches_redacted": 0,
        }

        with tempfile.TemporaryDirectory(prefix="docx_redact_") as staging:
            work = Path(staging)
            unzip_docx(input_docx, work)

            for part in scannable_parts(work, self.include_comments):
                touched, redactions = self.process_part(part)
                stats["paragraphs_touched"] += touched
                stats["matches_redacted"] += redactions
                stats["parts_processed"] += 1

            zip_docx(work, output_docx)

        return stats


def compile_rules(args: argparse.Namespace) -> list[RedactionRule]:
    rules: list[RedactionRule] = []

    if args.emails:
        rules.append(RedactionRule(pattern=EMAIL_PATTERN, label="email"))
    if args.phones:
        rules.append(RedactionRule(pattern=PHONE_PATTERN, label="phone"))
    for index, pattern in enumerate(args.pattern or [], start=1):
        rules.append(RedactionRule(pattern=re.compile(pattern), label=f"custom_{index}"))

    if not rules:
        raise SystemExit(
            "No redaction rules specified. Use --emails/--phones and/or --pattern REGEX."
        )
    return rules


def main() -> None:
    ap = argparse.ArgumentParser(description="Redact/anonymize text in a DOCX (OOXML patch).")
    ap.add_argument("input_docx", type=Path)
    ap.add_argument("output_docx", type=Path)

    rules_group = ap.add_argument_group("rules")
    rules_group.add_argument("--emails", action="store_true", help="Redact email addresses")
    rules_group.add_argument("--phones", action="store_true", help="Redact phone-like numbers")
    rules_group.add_argument("--pattern", action="append",
                             help="Custom regex to redact (can be repeated)")

    output_group = ap.add_argument_group("output")
    output_group.add_argument(
        "--mask_char",
        default=DEFAULT_MASK_CHAR,
        help=f"Mask character for length-preserving redaction (default: {DEFAULT_MASK_CHAR})",
    )
    output_group.add_argument(
        "--replacement",
        default=None,
        help="Optional replacement string. If --preserve_length (default), it will be "
             "repeated/truncated to match each match's length.",
    )
    output_group.add_argument(
        "--no_preserve_length",
        action="store_true",
        help="Disable length preservation (may cause layout drift)",
    )
    output_group.add_argument(
        "--include_comments",
        action="store_true",
        help="Also redact word/comments.xml (if present)",
    )

    args = ap.parse_args()

    redactor = Redactor(
        rules=compile_rules(args),
        substitution=Substitution(
            mask_char=args.mask_char,
            replacement=args.replacement,
            preserve_length=not args.no_preserve_length,
        ),
        include_comments=args.include_comments,
    )
    stats = redactor.run(args.input_docx, args.output_docx)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
