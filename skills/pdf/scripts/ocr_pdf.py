#!/usr/bin/env python3
"""Turn a scanned PDF into a searchable one.

Primary engine: ocrmypdf (best quality).
Fallback engine: pdftoppm + tesseract, page by page, merged afterwards.

Golden path:
  python ocr_pdf.py scanned.pdf -o searchable.pdf --lang eng

Defaults stay conservative so already-textual PDFs are not damaged: with
text present, the input is copied through unless --force is passed.  Only
options that work in this runtime are used — no OCRmyPDF features requiring
extra system binaries.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter

TEXT_SAMPLE_PAGES = 3
TEXT_MIN_CHARS = 40
FALLBACK_DPI = 300


def looks_textual(pdf: Path) -> bool:
    """Heuristic: any sampled page extracting a non-trivial text run makes
    the PDF "already has text"."""
    try:
        with fitz.open(str(pdf)) as doc:
            for index in range(min(doc.page_count, TEXT_SAMPLE_PAGES)):
                if len((doc.load_page(index).get_text("text") or "").strip()) >= TEXT_MIN_CHARS:
                    return True
    except Exception:
        return False  # unreadable input is not assumed to contain text
    return False


def rendered_page_number(path: Path) -> int:
    match = re.search(r"-(\d+)\.(?:png|jpg|jpeg)$", path.name)
    return int(match.group(1)) if match else 10**9


def fallback_ocr(source: Path, destination: Path, *, lang: str, force: bool,
                 dpi: int, keep_tmp: bool) -> None:
    if not force and looks_textual(source):
        shutil.copyfile(source, destination)
        print(f"[OK] input already has text; copied to {destination} (pass --force to OCR anyway)")
        return

    for binary, hint in (("pdftoppm", "poppler-utils missing"), ("tesseract", "install tesseract")):
        if shutil.which(binary) is None:
            raise SystemExit(f"{binary} not found ({hint}); cannot run fallback OCR")

    workspace = Path(tempfile.mkdtemp(prefix="ocr_fallback_", dir=str(destination.parent)))
    try:
        render_prefix = workspace / "page"
        subprocess.check_call(
            ["pdftoppm", "-png", "-r", str(dpi), str(source), str(render_prefix)])
        images = sorted(workspace.glob("page-*.png"), key=rendered_page_number)
        if not images:
            raise SystemExit(
                "Fallback OCR: no rendered images produced (is the PDF empty/protected?)")

        page_pdfs = []
        for image in images:
            out_base = workspace / f"ocr_{rendered_page_number(image):04d}"
            subprocess.check_call(["tesseract", str(image), str(out_base), "-l", lang, "pdf"])
            page_pdfs.append(out_base.with_suffix(".pdf"))

        writer = PdfWriter()
        for page_pdf in sorted(page_pdfs):
            for page in PdfReader(str(page_pdf)).pages:
                writer.add_page(page)
        with open(destination, "wb") as fh:
            writer.write(fh)

        if len(PdfReader(str(destination)).pages) == 0:
            raise SystemExit("Fallback OCR produced a PDF with zero pages")
        print(str(destination))
    finally:
        if keep_tmp:
            print(f"[INFO] temp dir kept: {workspace}")
        else:
            shutil.rmtree(workspace, ignore_errors=True)


def ocrmypdf_run(source: Path, destination: Path, *, lang: str, force: bool,
                 deskew: bool, optimize: int, jobs: int) -> None:
    command = ["ocrmypdf", "--language", lang, "--jobs", str(jobs), "--optimize", str(optimize)]
    if deskew:
        command += ["--deskew"]
    if not force:
        command += ["--skip-text"]
    command += [str(source), str(destination)]
    print(" ".join(command))
    subprocess.check_call(command)


CLI_SPEC = [
    (["input_pdf"], {}, "scanned input PDF"),
    (["-o", "--output"], {"required": True}, "output searchable PDF"),
    (["--lang"], {"default": "eng"}, "Tesseract language code(s), e.g. 'eng' or 'eng+spa'"),
    (["--force"], {"action": "store_true"}, "OCR even when text already exists"),
    (["--fallback"], {"action": "store_true"},
     "use the pdftoppm+tesseract pipeline instead of ocrmypdf"),
    (["--jobs"], {"type": int, "default": 2}, "parallel jobs for ocrmypdf"),
    (["--optimize"], {"type": int, "choices": [0, 1], "default": 1},
     "OCRmyPDF optimization level (0 or 1); higher levels need extra system tools"),
    (["--dpi"], {"type": int, "default": FALLBACK_DPI},
     "DPI for the fallback renderer (pdftoppm+tesseract)"),
    (["--keep_tmp"], {"action": "store_true"},
     "keep temporary files for debugging (fallback)"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for flags, options, help_text in CLI_SPEC:
        parser.add_argument(*flags, **options, help=help_text)
    # The ocrmypdf path honors deskew; the fallback path ignores it.
    try:
        parser.add_argument("--deskew", action=argparse.BooleanOptionalAction,
                            default=True, help="deskew pages (default: on)")
    except Exception:
        parser.add_argument("--deskew", action="store_true",
                            help="deskew pages (ocrmypdf only)")
    args = parser.parse_args()

    source = Path(args.input_pdf)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        raise SystemExit(f"input not found: {source}")

    if args.fallback:
        fallback_ocr(source, destination, lang=args.lang, force=args.force,
                     dpi=args.dpi, keep_tmp=args.keep_tmp)
        return 0

    if shutil.which("ocrmypdf") is None:
        raise SystemExit(
            "ocrmypdf not found. Install it with: python -m pip install ocrmypdf\n"
            "Or re-run with --fallback to use pdftoppm+tesseract."
        )
    ocrmypdf_run(
        source, destination,
        lang=args.lang, force=args.force,
        deskew=bool(getattr(args, "deskew", True)),
        optimize=args.optimize, jobs=args.jobs,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
