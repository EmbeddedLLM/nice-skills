#!/usr/bin/env python3
"""Compare DOCX text and rendered PNG pages in a reproducible output directory.

Usage: render_and_diff.py before.docx after.docx --outdir comparison
Requires lxml, Pillow, and the bundled render_docx.py prerequisites. --render_py
can select an equivalent local renderer. Rendering runs in fresh staging folders;
failed or empty renders do not publish a success summary. Existing generated
comparison outputs are replaced after successful analysis. Other files survive.
Differences are exact RGB pixels, not a visual significance score.
"""
import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

from word_package import DOCUMENT, Package, tag, text_of


def body_text(docx_path):
    lines = [text_of(node) for node in Package(docx_path).xml(DOCUMENT).iter(tag("p"))]
    return "\n".join(line for line in lines if line) + "\n"


def compare(left, right, folder):
    changed = []
    for number in sorted(left.keys() | right.keys()):
        if number not in left or number not in right:
            changed.append(number)
            continue
        with Image.open(left[number]) as a, Image.open(right[number]) as b:
            size = (max(a.width, b.width), max(a.height, b.height))
            canvases = []
            for original in (a, b):
                canvas = Image.new("RGB", size, "white")
                canvas.paste(original.convert("RGB"), (0, 0))
                canvases.append(canvas)
            difference = ImageChops.difference(*canvases)
            # Different page dimensions are a structural change even if both are white.
            if a.size != b.size or difference.getbbox():
                changed.append(number)
                folder.mkdir(exist_ok=True)
                difference.save(folder / f"diff-page-{number}.png")
    return changed


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("a_docx")
    cli.add_argument("b_docx")
    cli.add_argument("--outdir", required=True, type=Path)
    cli.add_argument("--render_py", default=str(Path(__file__).resolve().parents[1] / "render_docx.py"))
    options = cli.parse_args()
    options.outdir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="docx-comparison-", dir=options.outdir.parent) as temporary:
        staging = Path(temporary)
        pages = []
        texts = []
        for label, source in (("a", options.a_docx), ("b", options.b_docx)):
            destination = staging / (label + "_render")
            destination.mkdir()
            subprocess.run([sys.executable, options.render_py, source, "--output_dir", str(destination)], check=True)
            rendered = {int(match[1]): image for image in destination.iterdir()
                        if (match := re.fullmatch(r"page-(\d+)\.png", image.name))}
            if not rendered:
                raise RuntimeError(f"Renderer produced no page PNGs for {source}")
            pages.append(rendered)
            text = body_text(source)
            texts.append(text)
            (staging / f"text_{label}.txt").write_text(text, encoding="utf-8")
        changed = compare(*pages, staging / "diff_pages")
        difference = difflib.unified_diff(*(text.splitlines(keepends=True) for text in texts), fromfile="a", tofile="b")
        (staging / "text_diff.txt").write_text("".join(difference), encoding="utf-8")
        summary = {"a_docx": str(Path(options.a_docx).resolve()), "b_docx": str(Path(options.b_docx).resolve()),
                   "pages_a": len(pages[0]), "pages_b": len(pages[1]),
                   "changed_pages": changed, "num_changed_pages": len(changed)}
        (staging / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        options.outdir.mkdir(exist_ok=True)
        for name in ("a_render", "b_render", "diff_pages", "text_a.txt", "text_b.txt", "text_diff.txt", "summary.json"):
            destination = options.outdir / name
            if destination.is_dir():
                shutil.rmtree(destination)
            elif destination.exists():
                destination.unlink()
            if (staging / name).exists():
                shutil.move(str(staging / name), destination)
    print(f"[OK] wrote {options.outdir}")
    print(f"[summary] changed_pages={changed}")


if __name__ == "__main__":
    main()
