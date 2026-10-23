#!/usr/bin/env python3
"""Build a one-page watermark PDF (text on a diagonal) for `pdf_edit.py watermark`.

Examples:
  python make_watermark_pdf.py --text "CONFIDENTIAL" --out watermark.pdf
  python make_watermark_pdf.py --text "DRAFT" --angle 45 --font_size 72 --opacity 0.12 --out wm.pdf

Notes:
  - Built with ReportLab; the output is an ordinary vector PDF.
  - Opacity uses a PDF transparency state, which most viewers handle.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas

PAGE_SIZES = {"letter": letter, "a4": A4}


def stamp(out_path: Path, args) -> None:
    width, height = PAGE_SIZES[args.pagesize]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(out_path), pagesize=(width, height))

    try:
        pdf.setFillAlpha(args.opacity)
    except Exception:
        # Older ReportLab builds lack transparency; fall back to solid ink.
        pass

    center_x = args.center_x if args.center_x is not None else width / 2.0
    center_y = args.center_y if args.center_y is not None else height / 2.0
    pdf.setFont(args.font, args.font_size)
    pdf.saveState()
    pdf.translate(center_x, center_y)
    pdf.rotate(args.angle)
    pdf.drawCentredString(0, 0, args.text)
    pdf.restoreState()

    pdf.showPage()
    pdf.save()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--pagesize", choices=sorted(PAGE_SIZES), default="letter")
    parser.add_argument("--font", default="Helvetica-Bold")
    parser.add_argument("--font_size", type=int, default=72)
    parser.add_argument("--angle", type=float, default=45.0)
    parser.add_argument("--opacity", type=float, default=0.12)
    parser.add_argument("--center_x", type=float, default=None,
                        help="points; default: page center")
    parser.add_argument("--center_y", type=float, default=None,
                        help="points; default: page center")
    args = parser.parse_args()

    if not 0.0 <= args.opacity <= 1.0:
        raise SystemExit("--opacity must be in [0,1]")

    out_path = Path(args.out)
    stamp(out_path, args)
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
