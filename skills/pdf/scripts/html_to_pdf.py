#!/usr/bin/env python3
"""Headless-Chromium HTML-to-PDF rendering (Playwright).

A strong fit for reports built from modern CSS templates.  Keep local assets
(CSS/images) relative to the HTML file, and always re-render the produced
PDF to images for inspection.

Example: python html_to_pdf.py report.html -o report.pdf --format A4
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

# Playwright expects canonical page-format casing; accept loose spellings.
PAGE_FORMAT_ALIASES = {
    "letter": "Letter",
    "legal": "Legal",
    "tabloid": "Tabloid",
    "a3": "A3",
    "a4": "A4",
    "a5": "A5",
}

CLI_SPEC = [
    (["input_html"], {}, "HTML file to render"),
    (["-o", "--output"], {"required": True}, "where the PDF is written"),
    (["--format"], {"default": "Letter"}, "page format, e.g. Letter or A4"),
    (["--scale"], {"type": float, "default": 1.0}, "render scale, 0.1-2.0"),
    (["--landscape"], {"action": "store_true"}, "landscape orientation"),
    (["--timeout_ms"], {"type": int, "default": 60_000}, "navigation timeout in ms"),
]


def parse_cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for flags, options, help_text in CLI_SPEC:
        parser.add_argument(*flags, **options, help=help_text)
    return parser.parse_args(argv)


def render_pdf(html_file: Path, pdf_file: Path, *, page_format: str, scale: float,
               landscape: bool, timeout_ms: int) -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(html_file.as_uri(), wait_until="networkidle", timeout=timeout_ms)
            page.pdf(
                path=str(pdf_file),
                format=page_format,
                scale=scale,
                landscape=landscape,
                print_background=True,
                prefer_css_page_size=True,
            )
        finally:
            browser.close()


def cli(argv=None) -> int:
    args = parse_cli(argv)
    html_file = Path(args.input_html).resolve()
    if not html_file.exists():
        raise SystemExit(f"input HTML not found: {html_file}")
    pdf_file = Path(args.output)
    pdf_file.parent.mkdir(parents=True, exist_ok=True)
    render_pdf(
        html_file,
        pdf_file,
        page_format=PAGE_FORMAT_ALIASES.get(str(args.format).strip().lower(), args.format),
        scale=args.scale,
        landscape=args.landscape,
        timeout_ms=args.timeout_ms,
    )
    print(str(pdf_file))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
