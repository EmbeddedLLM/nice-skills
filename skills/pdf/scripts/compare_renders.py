#!/usr/bin/env python3
"""Compare rasterized PDF pages; write a JSON report and changed-page images.

Requires Pillow and the chosen render_pdf.py backend. Differences are evidence
for review, not a pass/fail threshold; a completed comparison exits successfully.
"""

import argparse
import json
from itertools import zip_longest
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops


def render(pdf, destination, dpi, engine):
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("render_pdf.py")), str(pdf),
         "--out_dir", str(destination), "--dpi", str(dpi), "--engine", engine],
        check=True,
    )


def page_pngs(render_dir):
    return sorted(Path(render_dir).glob("page-*.png"),
                  key=lambda p: int(p.stem.removeprefix("page-")))


def diff_images(first, second):
    """Compare RGB channels exactly, padding smaller images with white."""
    with Image.open(first) as a, Image.open(second) as b:
        extent = (max(a.width, b.width), max(a.height, b.height))
        layers = []
        for original in (a, b):
            layer = Image.new("RGB", extent, "white")
            layer.paste(original.convert("RGB"), (0, 0))
            layers.append(layer)
    delta = ImageChops.difference(*layers)
    # A luminance conversion can round a one-level blue change down to zero.
    red, green, blue = delta.split()
    maximum = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    counts = maximum.histogram()
    bounds = maximum.getbbox()
    result = dict(changed=bounds is not None, bbox=list(bounds) if bounds else None,
                  pct_changed=1 - counts[0] / (extent[0] * extent[1]),
                  max_channel=maximum.getextrema()[1])
    if bounds:
        result["diff"] = delta
    return result


def compare_pages(pages_a, pages_b, diff_dir):
    """Keep page numbering and output records common to both comparison CLIs."""
    diff_dir.mkdir(parents=True, exist_ok=True)
    for obsolete in diff_dir.glob("page-*.png"):
        obsolete.unlink()
    records = []
    for number, (left, right) in enumerate(zip_longest(pages_a, pages_b), 1):
        record = {"page": number, "a": str(left) if left else None,
                  "b": str(right) if right else None}
        if left is None or right is None:
            record["missing"] = True
        else:
            measured = diff_images(left, right)
            picture = measured.pop("diff", None)
            record.update(measured)
            if picture is not None:
                target = diff_dir / f"page-{number}.png"
                picture.save(target)
                record["diff"] = str(target)
        records.append(record)
    return records


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ("pdf_a", "pdf_b"):
        cli.add_argument(name)
    cli.add_argument("--out_dir", required=True, type=Path)
    cli.add_argument("--dpi", type=int, default=200)
    cli.add_argument("--engine", default="pdftoppm", choices=("pdftoppm", "pdfium"))
    cli.add_argument("--save_renders", action="store_true")
    options = cli.parse_args()
    locations = [options.out_dir / name for name in ("render_a", "render_b")]
    for source, folder in zip((options.pdf_a, options.pdf_b), locations):
        render(source, folder, options.dpi, options.engine)
    first, second = map(page_pngs, locations)
    records = compare_pages(first, second, options.out_dir / "diff")
    report = {"pdf_a": str(Path(options.pdf_a)), "pdf_b": str(Path(options.pdf_b)),
              "dpi": options.dpi, "engine": options.engine,
              "pages_a": len(first), "pages_b": len(second),
              "changed_pages": sum(bool(r.get("missing") or r.get("changed")) for r in records),
              "per_page": records}
    target = options.out_dir / "summary.json"
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not options.save_renders:
        for folder in locations:
            for picture in folder.glob("*.png"):
                picture.unlink()
            if not any(folder.iterdir()):
                folder.rmdir()
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
