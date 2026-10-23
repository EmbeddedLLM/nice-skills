#!/usr/bin/env python3
"""Render PDF pages to images for visual inspection.

The default engine is poppler's `pdftoppm`; `pypdfium2` is an optional,
often faster alternative.

Examples:
  python render_pdf.py input.pdf --out_dir _renders/input
  python render_pdf.py input.pdf --out_dir _renders/input --dpi 200 --pages 1-3

Outputs are named <out_dir>/<prefix>-1.png, <out_dir>/<prefix>-2.png, ...
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

DPI_DEFAULT = 150
FORMATS = ("png", "jpeg")
ENGINES = ("pdftoppm", "pdfium")


def page_spec(spec: str) -> list[tuple[int, int]]:
    """'1-3,5,7-9' -> [(1,3),(5,5),(7,9)] (1-based inclusive ranges)."""
    ranges = []
    for piece in spec.split(","):
        piece = piece.strip()
        if not piece:
            continue
        if "-" in piece:
            first_s, last_s = piece.split("-", 1)
            first, last = int(first_s), int(last_s)
        else:
            first = last = int(piece)
        if first < 1 or last < 1 or last < first:
            raise ValueError(f"Invalid pages segment: {piece}")
        ranges.append((first, last))
    if not ranges:
        raise ValueError("Empty --pages")
    return ranges


def output_pattern(prefix: str, fmt: str) -> re.Pattern:
    return re.compile(rf"^{re.escape(prefix)}-(\d+)\.{re.escape(fmt)}$")


def remove_stale(out_dir: Path, prefix: str, fmt: str) -> None:
    """Delete previous renders for this prefix/format so runs never mix."""
    if not out_dir.exists():
        return
    pattern = output_pattern(prefix, fmt)
    for entry in out_dir.iterdir():
        if entry.is_file() and pattern.match(entry.name):
            entry.unlink(missing_ok=True)


def rendered_files(out_dir: Path, prefix: str, fmt: str) -> list[Path]:
    pattern = output_pattern(prefix, fmt)
    return [p for p in sorted(out_dir.iterdir()) if p.is_file() and pattern.match(p.name)]


def via_pdftoppm(source, out_dir, prefix, fmt, dpi, pages) -> list[Path]:
    if shutil.which("pdftoppm") is None:
        raise RuntimeError("pdftoppm not found (poppler-utils missing)")

    out_dir.mkdir(parents=True, exist_ok=True)
    remove_stale(out_dir, prefix, fmt)

    # pdftoppm accepts -f/-l per contiguous range, so disjoint ranges take
    # one invocation each; no --pages means a single whole-document run.
    for first, last in pages or [(1, 10**9)]:
        command = ["pdftoppm", f"-{fmt}", "-r", str(dpi)]
        if pages is not None:
            command += ["-f", str(first), "-l", str(last)]
        command += [str(source), str(out_dir / prefix)]
        subprocess.run(command, check=True)

    rendered = rendered_files(out_dir, prefix, fmt)
    if not rendered:
        raise RuntimeError("No images produced. Is the PDF empty or protected?")
    return rendered


def via_pdfium(source, out_dir, prefix, fmt, dpi, pages) -> list[Path]:
    try:
        import pypdfium2 as pdfium
    except Exception as exc:
        raise RuntimeError(
            "pypdfium2 is not installed. Install with: python -m pip install pypdfium2"
        ) from exc

    out_dir.mkdir(parents=True, exist_ok=True)
    remove_stale(out_dir, prefix, fmt)

    document = pdfium.PdfDocument(str(source))
    total = len(document)
    wanted = (
        range(1, total + 1)
        if pages is None
        else [n for first, last in pages for n in range(first, min(last, total) + 1)]
    )

    scale = dpi / 72.0
    rendered = []
    for number in wanted:
        out_path = out_dir / f"{prefix}-{number}.{fmt}"
        document[number - 1].render(scale=scale).to_pil().save(out_path)
        rendered.append(out_path)
    if not rendered:
        raise RuntimeError("No images produced")
    return rendered


CLI_SPEC = [
    (["input_pdf"], {}, "PDF to render"),
    (["--out_dir"], {"required": True}, "directory for the images"),
    (["--prefix"], {"default": "page"}, "output filename prefix (default: page)"),
    (["--dpi"], {"type": int, "default": DPI_DEFAULT}, f"render DPI (default: {DPI_DEFAULT})"),
    (["--fmt"], {"default": "png", "choices": list(FORMATS)}, "image format"),
    (["--pages"], {"default": None}, "1-indexed page ranges like '1-3,5,7-9'"),
    (["--engine"], {"default": "pdftoppm", "choices": list(ENGINES)}, "rendering engine"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for flags, options, help_text in CLI_SPEC:
        parser.add_argument(*flags, **options, help=help_text)
    args = parser.parse_args()

    source = Path(args.input_pdf)
    if not source.exists():
        raise SystemExit(f"Input not found: {source}")

    out_dir = Path(args.out_dir)
    pages = page_spec(args.pages) if args.pages else None
    engine = via_pdftoppm if args.engine == "pdftoppm" else via_pdfium
    rendered = engine(source, out_dir, args.prefix, args.fmt, args.dpi, pages)
    print(f"Rendered {len(rendered)} page(s) to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
