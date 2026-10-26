#!/usr/bin/env python3
"""End-to-end check that true redaction works (PyMuPDF path).

Builds a tiny PDF containing a secret phrase, redacts the phrase, and then
verifies both that `pdftotext` can no longer extract it and that rendered
pixels visibly changed.

Usage:
  python redact_smoketest.py  # uses work/_pdf_redact_smoke
  python redact_smoketest.py --workdir work/_pdf_redact_smoke_custom
"""

from __future__ import annotations

import argparse
import sys
import subprocess
from pathlib import Path

from PIL import Image, ImageChops

SCRIPT_DIR = Path(__file__).resolve().parent
SECRET = "TOP SECRET"


def make_fixture(path: Path) -> None:
    """A one-page PDF with a secret line and a public line (ReportLab keeps
    the fixture dependency-free)."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    pdf = canvas.Canvas(str(path), pagesize=letter)
    _, top = letter
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(inch, top - inch, "Redaction Smoke Test")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(inch, top - 1.5 * inch, f"{SECRET}: project-aurora")
    pdf.drawString(inch, top - 1.8 * inch, "Public line")
    pdf.showPage()
    pdf.save()


def render(pdf: Path, out_dir: str, dpi: int, cwd: Path) -> None:
    subprocess.check_call(
        [sys.executable, str(SCRIPT_DIR / "render_pdf.py"), str(pdf),
         "--out_dir", out_dir, "--dpi", str(dpi)],
        cwd=str(cwd),
    )


def extracted_text(pdf: Path) -> str:
    proc = subprocess.run(
        ["pdftotext", str(pdf), "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    return (proc.stdout or "").lower()


def images_differ(first: Path, second: Path) -> bool:
    before = Image.open(first).convert("RGB")
    after = Image.open(second).convert("RGB")
    if before.size != after.size:
        return True
    return ImageChops.difference(before, after).getbbox() is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", default="work/_pdf_redact_smoke")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    source = workdir / "input.pdf"
    redacted = workdir / "redacted.pdf"

    make_fixture(source)
    render(source, "before", args.dpi, workdir)
    subprocess.check_call(
        [sys.executable, str(SCRIPT_DIR / "pdf_redact.py"), "text", str(source), str(redacted),
         "--text", SECRET, "--ignore_case", "--whole_word"],
        cwd=str(workdir),
    )
    render(redacted, "after", args.dpi, workdir)

    if SECRET.lower() in extracted_text(redacted):
        raise SystemExit("FAIL: the redacted phrase still extracts with pdftotext")

    before_png = workdir / "before" / "page-1.png"
    after_png = workdir / "after" / "page-1.png"
    if not (before_png.exists() and after_png.exists()):
        raise SystemExit("FAIL: render outputs are missing")
    if not images_differ(before_png, after_png):
        raise SystemExit("FAIL: rendered pixels are unchanged (redaction may have failed)")

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
