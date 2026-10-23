"""Render a presentation to labelled thumbnail contact sheets.

Slides are converted through LibreOffice + Poppler, laid out in a grid, and
captioned with their XML part name (e.g. slide1.xml) so a reviewer can map
each image back to the markup.  Hidden slides get a crossed-out placeholder
unless the renderer produced pages for them.

Usage:
    python thumbnail.py deck.pptx                 # writes thumbnails.jpg
    python thumbnail.py deck.pptx out/grid --cols 4
    # large decks spill into grid-1.jpg, grid-2.jpg, ...
"""

from __future__ import annotations

import argparse
import posixpath
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from lxml import etree
from PIL import Image, ImageDraw, ImageFont

from office.helpers import SLIDE_REL_TYPE, opc_target
from office.soffice import run_soffice

NS_PRESENTATION = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_OFFICE_RELS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PACKAGE_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"

THUMB_WIDTH = 300          # px per slide cell
RENDER_DPI = 100           # pdftoppm rasterisation density
DEFAULT_COLS = 3
MAX_COLS = 6
JPEG_QUALITY = 95
CELL_GAP = 20              # px of white space around cells
BORDER = 2                 # px frame around each thumbnail
CAPTION_RATIO = 0.10       # caption font size as a fraction of cell width
CAPTION_GAP_RATIO = 0.4    # gap around caption as a fraction of font size
PLACEHOLDER_FILL = "#F0F0F0"
PLACEHOLDER_CROSS = "#CCCCCC"


# ------------------------------------------------------------- extraction

def get_slide_info(pptx_path: Path) -> list[dict]:
    """Slide parts in presentation order, with their hidden flag."""
    with zipfile.ZipFile(pptx_path, "r") as archive:
        rels = etree.fromstring(archive.read("ppt/_rels/presentation.xml.rels"))
        part_by_rid = {}
        for rel in rels.iter(f"{{{NS_PACKAGE_RELS}}}Relationship"):
            if rel.get("Type") != SLIDE_REL_TYPE:
                continue
            part = opc_target(
                rel.get("Target", ""), "ppt/presentation.xml",
                rel.get("TargetMode", ""),
            )
            if part is not None:
                part_by_rid[rel.get("Id")] = part

        presentation = etree.fromstring(archive.read("ppt/presentation.xml"))
        members = set(archive.namelist())
        info = []
        for entry in presentation.iter(f"{{{NS_PRESENTATION}}}sldId"):
            part = part_by_rid.get(entry.get(f"{{{NS_OFFICE_RELS}}}id"))
            if part is None or part not in members:
                continue
            info.append({"name": posixpath.basename(part),
                         "hidden": _is_hidden(archive, part)})
        return info


def _is_hidden(archive: zipfile.ZipFile, part: str) -> bool:
    try:
        root = etree.fromstring(archive.read(part))
    except (KeyError, etree.XMLSyntaxError):
        return False
    return root.get("show") in ("0", "false")


# ------------------------------------------------------------- rendering

def render_slide_pages(pptx_path: Path, work_dir: Path) -> list[Path]:
    """Rasterise the deck to one JPEG per rendered page inside *work_dir*."""
    pdf_path = work_dir / f"{pptx_path.stem}.pdf"
    conversion = run_soffice(
        ["--headless", "--convert-to", "pdf", "--outdir", str(work_dir),
         str(pptx_path.resolve())],
        capture_output=True, text=True,
    )
    if conversion.returncode != 0 or not pdf_path.exists():
        detail = (conversion.stderr or conversion.stdout or "").strip()
        raise RuntimeError(f"PDF conversion failed: {detail}" if detail
                           else "PDF conversion failed")

    raster = subprocess.run(
        ["pdftoppm", "-jpeg", "-r", str(RENDER_DPI), str(pdf_path),
         str(work_dir / "slide")],
        capture_output=True, text=True, timeout=60,
    )
    if raster.returncode != 0:
        raise RuntimeError("PDF-to-image conversion failed")
    return sorted(
        work_dir.glob("slide-*.jpg"),
        key=lambda path: int(path.stem.rsplit("-", 1)[1]),
    )


def _placeholder(size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGB", size, PLACEHOLDER_FILL)
    pen = ImageDraw.Draw(image)
    stroke = max(5, min(size) // 100)
    pen.line([(0, 0), size], fill=PLACEHOLDER_CROSS, width=stroke)
    pen.line([(size[0], 0), (0, size[1])], fill=PLACEHOLDER_CROSS, width=stroke)
    return image


def build_slide_list(
    slide_info: list[dict], rendered_pages: list[Path], work_dir: Path,
) -> list[tuple[Path, str]]:
    """Pair each slide with its image, inserting placeholders for hidden ones."""
    visible = sum(1 for info in slide_info if not info["hidden"])
    hidden_were_rendered = len(rendered_pages) == len(slide_info) != visible
    if not hidden_were_rendered and visible != len(rendered_pages):
        raise ValueError(
            f"Renderer produced {len(rendered_pages)} page(s) for {visible}"
            f" visible slide(s) of {len(slide_info)}; thumbnails would be"
            " mislabeled"
        )

    if rendered_pages:
        with Image.open(rendered_pages[0]) as probe:
            fallback_size = probe.size
    else:
        fallback_size = (1920, 1080)

    slides: list[tuple[Path, str]] = []
    page = 0
    for info in slide_info:
        label = info["name"] + (" (hidden)" if info["hidden"] else "")
        if info["hidden"] and not hidden_were_rendered:
            marker = work_dir / f"hidden-{info['name']}.jpg"
            _placeholder(fallback_size).save(marker, "JPEG")
            slides.append((marker, label))
        else:
            slides.append((rendered_pages[page], label))
            page += 1
    return slides


# ------------------------------------------------------------------ grids

def _compose_grid(slides: list[tuple[Path, str]], cols: int,
                  cell_width: int) -> Image.Image:
    font_size = int(cell_width * CAPTION_RATIO)
    caption_gap = int(font_size * CAPTION_GAP_RATIO)
    with Image.open(slides[0][0]) as probe:
        cell_height = int(cell_width * probe.height / probe.width)

    rows = -(-len(slides) // cols)
    grid_w = cols * cell_width + (cols + 1) * CELL_GAP
    cell_pitch = cell_height + font_size + caption_gap * 2
    grid_h = rows * cell_pitch + (rows + 1) * CELL_GAP

    grid = Image.new("RGB", (grid_w, grid_h), "white")
    pen = ImageDraw.Draw(grid)
    try:
        font = ImageFont.load_default(size=font_size)
    except Exception:
        font = ImageFont.load_default()

    for index, (image_path, caption) in enumerate(slides):
        row, col = divmod(index, cols)
        cell_x = col * cell_width + (col + 1) * CELL_GAP
        cell_y = row * cell_pitch + (row + 1) * CELL_GAP

        text_box = pen.textbbox((0, 0), caption, font=font)
        pen.text(
            (cell_x + (cell_width - (text_box[2] - text_box[0])) // 2,
             cell_y + caption_gap),
            caption, fill="black", font=font,
        )

        thumb_top = cell_y + caption_gap + font_size + caption_gap
        with Image.open(image_path) as picture:
            picture.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)
            w, h = picture.size
            offset_x = cell_x + (cell_width - w) // 2
            offset_y = thumb_top + (cell_height - h) // 2
            grid.paste(picture, (offset_x, offset_y))

        if BORDER > 0:
            pen.rectangle(
                [(offset_x - BORDER, offset_y - BORDER),
                 (offset_x + w + BORDER - 1, offset_y + h + BORDER - 1)],
                outline="gray", width=BORDER,
            )
    return grid


def create_grids(
    slides: list[tuple[Path, str]], cols: int, cell_width: int,
    output_path: Path,
) -> list[str]:
    """Write one or more grid JPEGs; return the file names written."""
    per_grid = cols * (cols + 1)
    written = []
    for sheet, start in enumerate(range(0, len(slides), per_grid), start=1):
        chunk = slides[start : start + per_grid]
        if len(slides) <= per_grid:
            target = output_path
        else:
            target = output_path.with_name(
                f"{output_path.stem}-{sheet}{output_path.suffix}"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        _compose_grid(chunk, cols, cell_width).save(
            str(target), quality=JPEG_QUALITY
        )
        written.append(str(target))
    return written


# -------------------------------------------------------------------- CLI

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a .pptx to labelled thumbnail contact sheets."
    )
    parser.add_argument("input", help="Input presentation (.pptx)")
    parser.add_argument("output_prefix", nargs="?", default="thumbnails",
                        help="Output image prefix (default: thumbnails)")
    parser.add_argument("--cols", type=int, default=DEFAULT_COLS,
                        help=f"Grid columns (default {DEFAULT_COLS}, max {MAX_COLS})")
    args = parser.parse_args()

    if args.cols < 1:
        parser.error("--cols must be positive")
    if args.cols > MAX_COLS:
        print(f"Warning: clamping columns to {MAX_COLS}")
    cols = min(args.cols, MAX_COLS)

    input_path = Path(args.input)
    if not input_path.is_file() or input_path.suffix.lower() != ".pptx":
        print(f"Error: not a PowerPoint file: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        info = get_slide_info(input_path)
        with tempfile.TemporaryDirectory() as work:
            work_dir = Path(work)
            pages = render_slide_pages(input_path, work_dir)
            if not pages and not any(entry["hidden"] for entry in info):
                print("Error: the deck contains no slides", file=sys.stderr)
                sys.exit(1)
            slides = build_slide_list(info, pages, work_dir)
            grids = create_grids(
                slides, cols, THUMB_WIDTH,
                Path(f"{args.output_prefix}.jpg"),
            )
        print(f"Created {len(grids)} grid(s):")
        for name in grids:
            print(f"  {name}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
