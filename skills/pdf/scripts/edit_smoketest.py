#!/usr/bin/env python3
"""Generate a local pagination fixture, check its text, and render its first page.

Requires the PDF skill's Python dependencies and a render backend. --workdir is
created when absent; generated fixtures and diagnostic renders remain there.
"""

import argparse
from pathlib import Path
import subprocess
import sys

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

SCRIPTS = Path(__file__).resolve().parent


def write_two_page_pdf(path):
    drawing = Canvas(str(path), pagesize=(612, 792))
    for number in (1, 2):
        drawing.drawString(54, 720, f"Synthetic page {number}")
        drawing.showPage()
    drawing.save()


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--workdir", type=Path, default=Path("work/_pdf_edit_smoke"))
    cli.add_argument("--dpi", type=int, default=150)
    options = cli.parse_args()
    options.workdir.mkdir(parents=True, exist_ok=True)
    original, result = (options.workdir / name for name in ("in.pdf", "paginated.pdf"))
    write_two_page_pdf(original)
    before = original.read_bytes()
    steps = [
        ("pdf_edit.py", "paginate", original, "-o", result, "--format", "Sheet {page}/{total}"),
        ("render_pdf.py", result, "--out_dir", options.workdir / "render",
         "--pages", "1", "--dpi", options.dpi),
    ]
    for script, *arguments in steps:
        subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, arguments)], check=True)
    pages = PdfReader(result).pages
    if len(pages) != 2 or any(f"Sheet {n}/2" not in p.extract_text() for n, p in enumerate(pages, 1)):
        raise RuntimeError("Pagination text or page count is incorrect")
    if original.read_bytes() != before:
        raise RuntimeError("Pagination modified the source")
    if not (options.workdir / "render/page-1.png").is_file():
        raise RuntimeError("Pagination render is missing")
    print("[OK] edit smoke test passed")
    print(options.workdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
