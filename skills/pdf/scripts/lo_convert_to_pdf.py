#!/usr/bin/env python3
"""Headless LibreOffice conversion of Office documents to PDF.

Accepts DOCX/PPTX/ODT and friends.  Conversion quality varies by file —
always render the resulting PDF to images and inspect them.

Examples:
  python lo_convert_to_pdf.py report.docx --out_dir work/out
  python lo_convert_to_pdf.py deck.pptx --out_dir work/out
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def soffice_convert(source: Path, out_dir: Path) -> subprocess.CompletedProcess:
    command = [
        "soffice",
        "--headless",
        "--nologo",
        "--nolockcheck",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(source),
    ]
    print(" ".join(command))
    return subprocess.run(command, check=False, capture_output=True, text=True)


def find_output(out_dir: Path, stem: str) -> Path | None:
    """LibreOffice derives the output name from the input stem; when it
    shifts slightly, a single-PDF directory scan recovers it."""
    expected = out_dir / f"{stem}.pdf"
    if expected.exists():
        return expected
    candidates = list(out_dir.glob("*.pdf"))
    return candidates[0] if len(candidates) == 1 else None


def validate_output(out_pdf: Path) -> None:
    """The output must exist, be non-empty, and parse as a real PDF."""
    from pypdf import PdfReader

    if len(PdfReader(str(out_pdf)).pages) == 0:
        raise RuntimeError("Output PDF has zero pages")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file")
    parser.add_argument("--out_dir", required=True)
    args = parser.parse_args()

    source = Path(args.input_file)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # soffice can exit non-zero while still writing a valid file, so the
    # output's existence and readability is the primary success signal.
    proc = soffice_convert(source, out_dir)
    out_pdf = find_output(out_dir, source.stem)

    if out_pdf is None or out_pdf.stat().st_size == 0:
        raise RuntimeError(
            "no PDF came out of the LibreOffice conversion.\n"
            f"exit={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    try:
        validate_output(out_pdf)
    except Exception as exc:
        raise RuntimeError(
            "a file was produced, but it does not parse as a valid PDF.\n"
            f"exit={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        ) from exc

    if proc.returncode != 0:
        print(f"[WARN] soffice exited with code {proc.returncode}, yet the output PDF parses fine.")
    print(str(out_pdf))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
