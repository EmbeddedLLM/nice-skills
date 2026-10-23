#!/usr/bin/env python3
"""Compare one PDF rendered by two backends, retaining both render sets.

The summary records per-page differences in the same schema as compare_renders.
Anti-aliasing differences need human interpretation; nonzero pixel differences
alone do not indicate a broken PDF.
"""

import argparse
import json
from pathlib import Path

from compare_renders import compare_pages, diff_images, page_pngs, render


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("input_pdf", type=Path)
    cli.add_argument("--out_dir", type=Path, required=True)
    cli.add_argument("--dpi", type=int, default=200)
    for flag, default in (("--engine_a", "pdftoppm"), ("--engine_b", "pdfium")):
        cli.add_argument(flag, choices=("pdftoppm", "pdfium"), default=default)
    options = cli.parse_args()
    rendered = []
    for backend in (options.engine_a, options.engine_b):
        directory = options.out_dir / f"render_{backend}"
        render(options.input_pdf, directory, options.dpi, backend)
        rendered.append(page_pngs(directory))
    records = compare_pages(*rendered, options.out_dir / "diff")
    report = dict(input_pdf=str(options.input_pdf), dpi=options.dpi,
                  engine_a=options.engine_a, engine_b=options.engine_b,
                  pages=len(records), per_page=records,
                  changed_pages=sum(bool(r.get("missing") or r.get("changed")) for r in records))
    target = options.out_dir / "summary.json"
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
