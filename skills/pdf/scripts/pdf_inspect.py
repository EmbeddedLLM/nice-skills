#!/usr/bin/env python3
"""Summarize a PDF: page count, encryption, page sizes, metadata, outlines,
and whether forms, attachments, or annotations are present.

Examples:
  python pdf_inspect.py report.pdf --json > info.json
  python pdf_inspect.py report.pdf
  python pdf_inspect.py report.pdf --password "secret"

JSON output is stable enough to consume from batch tooling.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from pypdf import PdfReader

POPPLER_TOOLS = (("pdfinfo", "poppler_pdfinfo"), ("pdffonts", "poppler_pdffonts"))


def cli_output(command: list[str]) -> tuple[int, str]:
    """(returncode, combined output); 127 when the binary is missing."""
    try:
        proc = subprocess.run(command, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, check=False)
        return proc.returncode, proc.stdout
    except FileNotFoundError:
        return 127, f"[missing] {command[0]} not found\n"


def outline_size(node) -> int:
    if node is None:
        return 0
    if isinstance(node, list):
        return sum(outline_size(child) for child in node)
    return 1


def page_size_tally(reader: PdfReader, sample: int = 200) -> list[dict]:
    """Unique rounded page sizes across the first `sample` pages."""
    tally: Counter[tuple[int, int]] = Counter()
    for page in reader.pages[:sample]:
        box = page.mediabox
        tally[(round(float(box.width)), round(float(box.height)))] += 1
    return [
        {"width_pt": width, "height_pt": height, "count": count}
        for (width, height), count in sorted(tally.items(), key=lambda item: (-item[1], item[0]))
    ]


@dataclass
class PdfSummary:
    path: str
    pages: int
    encrypted: bool
    page_sizes: list[dict]
    metadata: dict
    outline_items: int
    form_fields: int
    attachments: int
    annotations: int
    poppler_pdfinfo: Optional[str] = None
    poppler_pdffonts: Optional[str] = None


def safe_metadata(reader: PdfReader) -> dict:
    try:
        metadata = reader.metadata
        if metadata:
            return {str(key): (str(value) if value is not None else None)
                    for key, value in metadata.items()}
    except Exception:
        pass
    return {}


def count_annotations(reader: PdfReader) -> int:
    total = 0
    try:
        for page in reader.pages:
            if "/Annots" in page:
                annots = page["/Annots"]
                try:
                    total += len(annots)
                except Exception:
                    total += 1
    except Exception:
        return 0
    return total


def summarize(path: Path, password: str | None = None) -> PdfSummary:
    reader = PdfReader(str(path))
    encrypted = bool(getattr(reader, "is_encrypted", False))
    if encrypted and password:
        try:
            reader.decrypt(password)
        except Exception:
            pass  # continue; parts may remain inaccessible

    try:
        outline_items = outline_size(reader.outline)
    except Exception:
        outline_items = 0

    try:
        fields = reader.get_fields()
        form_fields = len(fields) if fields else 0
    except Exception:
        form_fields = 0

    attachments = 0
    try:
        embedded = getattr(reader, "attachments", None)
        if isinstance(embedded, dict):
            attachments = len(embedded)
    except Exception:
        pass

    poppler = {}
    for binary, field in POPPLER_TOOLS:
        code, output = cli_output([binary, str(path)])
        poppler[field] = output.strip() if code == 0 else None

    return PdfSummary(
        path=str(path),
        pages=len(reader.pages),
        encrypted=encrypted,
        page_sizes=page_size_tally(reader),
        metadata=safe_metadata(reader),
        outline_items=outline_items,
        form_fields=form_fields,
        attachments=attachments,
        annotations=count_annotations(reader),
        **poppler,
    )


def human_lines(summary: PdfSummary) -> list[str]:
    lines = [
        f"PDF: {summary.path}",
        f"Pages: {summary.pages}",
        f"Encrypted: {summary.encrypted}",
    ]
    if summary.page_sizes:
        lines.append("Page sizes (pt, rounded):")
        lines += [f"  - {s['width_pt']} x {s['height_pt']} ({s['count']} page(s))"
                  for s in summary.page_sizes]
    if summary.metadata:
        lines.append("Metadata:")
        lines += [f"  {key}: {summary.metadata[key]}" for key in sorted(summary.metadata)]
    lines += [
        f"Outline items: {summary.outline_items}",
        f"Form fields: {summary.form_fields}",
        f"Attachments: {summary.attachments}",
        f"Annotations: {summary.annotations}",
    ]
    if summary.poppler_pdffonts:
        lines.append("")
        lines.append("Fonts (pdffonts, first 25 lines):")
        lines += summary.poppler_pdffonts.splitlines()[:25]
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a PDF")
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--password", default=None, help="password for encrypted PDFs")
    args = parser.parse_args()

    if not args.input_pdf.exists():
        print(f"ERROR: not found: {args.input_pdf}", file=sys.stderr)
        return 2

    summary = summarize(args.input_pdf, password=args.password)
    print(
        json.dumps(asdict(summary), indent=2, ensure_ascii=True)
        if args.json
        else "\n".join(human_lines(summary))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
