#!/usr/bin/env python3
"""Arrange supplied PNG/JPEG files into a Pillow contact sheet.

Inputs may be directories, shell-style patterns, or filenames. Matches are sorted
within each input; repeated paths appear only once. --out names the saved image.
"""

import argparse
import glob
from pathlib import Path

from PIL import Image

RASTER_SUFFIXES = {".png", ".jpg", ".jpeg"}


def gather_images(items):
    by_identity = {}
    for token in items:
        location = Path(token)
        candidates = (location.iterdir() if location.is_dir()
                      else map(Path, glob.glob(token)))
        for match in sorted(candidates):
            if match.is_file() and match.suffix.lower() in RASTER_SUFFIXES:
                by_identity.setdefault(match.resolve(), match)
    return list(by_identity.values())


def compose_montage(image_paths, destination, *, cols=4, tile_max_w=800,
                    margin=10, background=(255, 255, 255)):
    if not image_paths:
        raise ValueError("No images provided")
    if cols < 1 or tile_max_w < 1 or margin < 0:
        raise ValueError("Columns and tile width must be positive; margin must be nonnegative")
    pictures = []
    for filename in image_paths:
        with Image.open(filename) as original:
            picture = original.convert("RGB")
        if picture.width > tile_max_w:
            picture = picture.resize((tile_max_w, max(1, round(picture.height * tile_max_w / picture.width))))
        pictures.append(picture)
    width = max(p.width for p in pictures)
    height = max(p.height for p in pictures)
    row_count = (len(pictures) - 1) // cols + 1
    sheet = Image.new("RGB", (cols * (width + margin) + margin,
                              row_count * (height + margin) + margin), background)
    for slot, picture in enumerate(pictures):
        x = margin + (slot % cols) * (width + margin) + (width - picture.width) // 2
        y = margin + (slot // cols) * (height + margin) + (height - picture.height) // 2
        sheet.paste(picture, (x, y))
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("inputs", nargs="+")
    cli.add_argument("--out", required=True)
    for option, value in (("cols", 4), ("tile_max_w", 800), ("margin", 10)):
        cli.add_argument("--" + option, type=int, default=value)
    options = cli.parse_args()
    compose_montage(gather_images(options.inputs), options.out, cols=options.cols,
                    tile_max_w=options.tile_max_w, margin=options.margin)
    print(options.out)


if __name__ == "__main__":
    main()
