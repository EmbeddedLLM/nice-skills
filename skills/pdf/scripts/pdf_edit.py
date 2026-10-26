#!/usr/bin/env python3
"""Write a separate PDF after selecting pages or changing document properties.

Requires pypdf; pagination also uses ReportLab, repair/optimize use PyMuPDF.
Page-preserving operations clone the document before mutation. Page subsets are
new documents; verify any outlines or forms needed in the extracted deliverable.
after ANY edit, render and visually verify the resulting file.
"""

import argparse
from io import BytesIO
import json
from pathlib import Path
import re
import warnings

from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

POSITIONS = ("br", "bc", "bl", "tr", "tc", "tl")


def parse_page_spec(spec, page_count):
    if spec is None or not spec.strip() or spec.strip().lower() == "all":
        return list(range(1, page_count + 1))
    chosen = {}
    for token in filter(None, map(str.strip, spec.split(","))):
        if "-" in token:
            start, stop = map(int, token.split("-", 1))
            if min(start, stop) < 1:
                raise ValueError("Pages must be >= 1")
            candidates = range(start, stop + 1)
        else:
            candidates = [int(token)]
        for number in candidates:
            if 1 <= number <= page_count:
                chosen[number] = None
    return list(chosen)


def position_xy(position, page_w, page_h, margin):
    code = (position or "br").strip().lower()
    if code not in POSITIONS:
        raise ValueError(f"Unsupported --position {position!r}; use br/bc/bl/tr/tc/tl")
    return ({"l": margin, "c": page_w / 2, "r": page_w - margin}[code[1]],
            margin if code[0] == "b" else page_h - margin)


def save(writer, output):
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    writer.write(str(target))
    print(target)


def page_number_overlay(page_w, page_h, label, x, y, font_size):
    from reportlab.pdfgen.canvas import Canvas
    stream = BytesIO()
    drawing = Canvas(stream, pagesize=(page_w, page_h))
    drawing.setFont("Helvetica", font_size)
    drawing.drawString(x, y, label)
    drawing.save()
    stream.seek(0)
    return stream


def crop_rectangle(page, options):
    if (options.inset is None) == (options.box is None):
        raise ValueError("Provide exactly one of --inset or --box")
    if options.box is not None:
        coordinates = tuple(map(float, options.box.split(",")))
        if len(coordinates) != 4:
            raise ValueError("--box must be left,bottom,right,top in points")
    else:
        measured = re.fullmatch(r"\s*(\d*\.?\d+)\s*(pt|in|cm|mm)\s*", options.inset)
        if measured is None:
            raise ValueError("--inset must look like '12pt' or '0.25in' or '5mm'")
        amount = float(measured[1]) * {"pt": 1, "in": 72, "cm": 72 / 2.54, "mm": 72 / 25.4}[measured[2]]
        left, bottom, right, top = map(float, page.mediabox)
        coordinates = (left + amount, bottom + amount, right - amount, top - amount)
    if coordinates[0] >= coordinates[2] or coordinates[1] >= coordinates[3]:
        raise ValueError("Crop rectangle must have positive width and height")
    return RectangleObject(coordinates)


def edit_document(options):
    command = options.cmd
    if command in ("optimize", "repair"):
        import fitz
        repair = command == "repair"
        cleaning = repair or options.recover or options.optimize_streams
        Path(options.output).parent.mkdir(parents=True, exist_ok=True)
        with fitz.open(options.input_pdf) as document:
            document.save(options.output, garbage=4 if cleaning or (not repair and options.compress_streams) else 2,
                          clean=cleaning, deflate=False if repair else options.compress_streams,
                          linear=False if repair else options.linearize, incremental=False)
        print(options.output)
        return
    if command == "merge":
        combined = PdfWriter()
        for filename in options.inputs:
            combined.append(filename)
        save(combined, options.output)
        return

    source = PdfReader(options.input_pdf)
    if command == "decrypt" and source.is_encrypted and not source.decrypt(options.password):
        raise RuntimeError("Bad password")
    total = len(source.pages)
    if command in ("split", "extract", "select"):
        if command == "select":
            groups = [(options.output, parse_page_spec(options.pages, total))]
        else:
            stem = Path(options.input_pdf).stem
            directory = Path(options.out_dir)
            directory.mkdir(parents=True, exist_ok=True)
            groups = []
            if command == "split":
                groups = [(directory / f"{stem}_p{n:03d}.pdf", [n]) for n in range(1, total + 1)]
            else:
                for token in options.ranges.split(","):
                    endpoints = [int(part.strip()) for part in token.split("-", 1)]
                    first, last = max(1, min(endpoints)), min(total, max(endpoints))
                    groups.append((directory / f"{stem}_p{first:03d}-p{last:03d}.pdf", range(first, last + 1)))
        for destination, numbers in groups:
            excerpt = PdfWriter()
            for number in numbers:
                excerpt.add_page(source.pages[number - 1])
            if command == "select":
                save(excerpt, destination)
            else:
                excerpt.write(str(destination))
        if command != "select":
            print(options.out_dir)
        return

    # A full clone retains the catalog (forms, outlines, attachments and metadata).
    result = PdfWriter(clone_from=source)
    if command == "encrypt":
        result.encrypt(options.user_password, options.owner_password, algorithm=options.algorithm)
    elif command == "fill-form":
        values = json.loads(Path(options.data).read_text(encoding="utf-8"))
        if not isinstance(values, dict):
            raise ValueError("Form values must be a JSON object")
        for page in result.pages:
            if page.get("/Annots"):
                try:
                    result.update_page_form_field_values(page, values)
                except Exception as error:
                    warnings.warn(f"Form appearance update failed; inspect stored values and rendering: {error}")
        if options.need_appearances:
            result.set_need_appearances_writer(True)
    elif command in ("rotate", "crop"):
        selection = parse_page_spec(options.pages, total)
        if command == "rotate":
            angle = int(options.angle) % 360
            if angle % 90:
                raise ValueError("angle must be 0/90/180/270")
        for number in selection:
            page = result.pages[number - 1]
            if command == "rotate":
                page.rotate(angle)
            else:
                page.cropbox = crop_rectangle(page, options)
    elif command in ("watermark", "paginate"):
        stamp = PdfReader(options.watermark).pages[0] if command == "watermark" else None
        for number, page in enumerate(result.pages, 1):
            if stamp is not None:
                page.merge_page(stamp)
                continue
            width, height = map(float, (page.mediabox.width, page.mediabox.height))
            label = options.format.format(page=options.start + number - 1, total=total)
            x, y = position_xy(options.position, width, height, options.margin)
            if options.position.endswith("r") and options.x is None:
                x -= len(label) * options.font_size * 0.45
            x = x if options.x is None else options.x
            y = y if options.y is None else options.y
            overlay = PdfReader(page_number_overlay(width, height, label, x, y, options.font_size))
            page.merge_page(overlay.pages[0])
    save(result, options.output)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="cmd", required=True)
    for name in ("merge", "split", "select", "extract", "rotate", "crop", "watermark",
                 "paginate", "encrypt", "decrypt", "optimize", "repair", "fill-form"):
        cli = commands.add_parser(name)
        if name == "merge":
            cli.add_argument("inputs", nargs="+")
        else:
            cli.add_argument("input_pdf")
        if name in ("split", "extract"):
            cli.add_argument("--out_dir", required=True)
        else:
            cli.add_argument("-o", "--output", required=True)
        if name in ("select", "rotate", "crop"):
            cli.add_argument("--pages", required=name == "select")
        if name == "extract":
            cli.add_argument("--ranges", required=True)
        elif name == "rotate":
            cli.add_argument("--angle", required=True)
        elif name == "crop":
            cli.add_argument("--inset")
            cli.add_argument("--box")
        elif name == "watermark":
            cli.add_argument("--watermark", required=True)
        elif name == "paginate":
            cli.add_argument("--position", choices=POSITIONS, default="br")
            cli.add_argument("--format", default="{page}")
            cli.add_argument("--start", type=int, default=1)
            cli.add_argument("--font_size", type=int, default=9)
            cli.add_argument("--margin", type=float, default=24)
            cli.add_argument("--x", type=float)
            cli.add_argument("--y", type=float)
        elif name == "encrypt":
            cli.add_argument("--user_password", "--user-pass", required=True)
            cli.add_argument("--owner_password", "--owner-pass")
            cli.add_argument("--algorithm", default="AES-256")
        elif name == "decrypt":
            cli.add_argument("--password", required=True)
        elif name == "optimize":
            for option in ("recover", "optimize_streams", "compress_streams", "linearize"):
                cli.add_argument("--" + option, action="store_true")
        elif name == "fill-form":
            cli.add_argument("data", help="Path to a JSON object of field values")
            cli.add_argument("--need_appearances", "--need-appearances", action="store_true")
    return parser


def main():
    edit_document(build_parser().parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
