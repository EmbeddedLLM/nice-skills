#!/usr/bin/env python3
"""Triage a PDF and surface actionable warnings.

Not a print-prepress checker — a high-signal diagnostic for the failure
modes that matter in programmatic PDF work: corruption/xref damage,
encryption, likely-scanned pages, XFA forms, and unembedded fonts.

Golden path:
  python pdf_preflight.py suspect.pdf
  python pdf_preflight.py suspect.pdf --json > preflight.json

The warnings drive the follow-up: normalize on corruption/xref/font issues,
OCR when the file looks scanned.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
from pypdf import PdfReader

# Base-14 fonts need no embedding; everything else should be embedded.
BASE14 = {
    "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
    "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
    "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
    "Symbol", "ZapfDingbats",
}


@dataclass
class Report:
    path: str
    ok_open: bool
    encrypted: bool
    pages: int
    likely_scanned: bool
    xfa_present: bool
    warnings: list[str] = field(default_factory=list)
    pdffonts_excerpt: str | None = None


def unembedded_font_rows(pdf: Path) -> str | None:
    """pdffonts rows for non-embedded, non-base14 fonts (header included)."""
    proc = subprocess.run(["pdffonts", str(pdf)], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, check=False)
    if proc.returncode != 0:
        return None
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if len(lines) <= 2:
        return None
    flagged = []
    for line in lines[2:]:
        columns = line.split()
        if len(columns) < 6:
            continue
        # Column positions shift between poppler releases; the "emb" column
        # is the first bare yes/no token.
        emb = next((token for token in columns if token in ("yes", "no")), None)
        if emb == "no" and columns[0] not in BASE14:
            flagged.append(line)
    return "\n".join([lines[0], *flagged[:20]]) if flagged else None


def has_xfa(reader: PdfReader) -> bool:
    try:
        acroform = reader.trailer["/Root"].get("/AcroForm")
        return bool(acroform) and "/XFA" in acroform
    except Exception:
        return False


def seems_scanned(doc: fitz.Document, sample: int = 10) -> bool:
    # Heuristic: most sampled pages carry almost no text yet hold images.
    count = min(doc.page_count, sample)
    if count <= 0:
        return False
    low_text = sum(
        1 for i in range(count)
        if len((doc.load_page(i).get_text("text") or "").strip()) < 20
    )
    with_images = sum(
        1 for i in range(count) if doc.load_page(i).get_images(full=True)
    )
    return (low_text / count) >= 0.7 and (with_images / count) >= 0.7


def run_preflight(pdf: Path, password: str | None = None) -> Report:
    warnings: list[str] = []
    pages = 0
    encrypted = False
    xfa = False

    # Structure via pypdf.
    try:
        reader = PdfReader(str(pdf))
        # Encrypted readers refuse page access until authentication succeeds.
        # Record encryption first so that a locked file is still identified.
        encrypted = reader.is_encrypted
        if encrypted and not reader.decrypt(password or ""):
            raise ValueError("Encrypted PDF: a valid password is required")
        pages = len(reader.pages)
        xfa = has_xfa(reader)
        if xfa:
            warnings.append(
                "XFA form present: many libraries cannot fill or render XFA reliably")
    except Exception as exc:
        warnings.append(f"pypdf could not read the file: {type(exc).__name__}: {exc}")

    # Openability and the scanned heuristic via PyMuPDF.
    ok_open = True
    scanned = False
    try:
        with fitz.open(str(pdf)) as doc:
            encrypted = encrypted or bool(doc.is_encrypted)
            if doc.is_encrypted and not doc.authenticate(password or ""):
                raise ValueError("Encrypted PDF: a valid password is required")
            pages = pages or doc.page_count
            scanned = seems_scanned(doc)
            if scanned:
                warnings.append(
                    "PDF looks scanned/image-only: run OCR (ocr_pdf.py) "
                    "before text extraction")
    except Exception as exc:
        ok_open = False
        warnings.append(
            "PyMuPDF could not open it (possible corruption/xref issue): "
            f"{type(exc).__name__}: {exc}")

    fonts = unembedded_font_rows(pdf)
    if fonts:
        warnings.append(
            "Non-embedded fonts detected (pdffonts): rendering may vary across viewers")

    return Report(
        path=str(pdf),
        ok_open=ok_open,
        encrypted=encrypted,
        pages=int(pages),
        likely_scanned=bool(scanned),
        xfa_present=bool(xfa),
        warnings=warnings,
        pdffonts_excerpt=fonts,
    )


def print_human(report: Report) -> None:
    print(f"PDF: {report.path}")
    print(f"Pages: {report.pages}")
    print(f"Encrypted: {report.encrypted}")
    print(f"Openable (PyMuPDF): {report.ok_open}")
    print(f"Likely scanned: {report.likely_scanned}")
    print(f"XFA present: {report.xfa_present}")
    if report.warnings:
        print("\nWarnings:")
        for warning in report.warnings:
            print(f"- {warning}")
    if report.pdffonts_excerpt:
        print("\nFonts excerpt (pdffonts):")
        print(report.pdffonts_excerpt)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("--password", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.input_pdf.exists():
        print(f"ERROR: not found: {args.input_pdf}", file=sys.stderr)
        return 2

    report = run_preflight(args.input_pdf, password=args.password)
    if args.json:
        print(json.dumps(asdict(report), indent=2, ensure_ascii=True))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
