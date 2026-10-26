#!/usr/bin/env python3
"""Add vector text or checkmarks to PDF-point rectangles (bottom-left origin).

Usage: place_text_by_boxes.py input.pdf spec.json values.json --out filled.pdf
A spec contains {"page": 1, "items": [...]} or {"pages": [...]} with each item
holding name, rect, and optional kind/font/font_size/align/valign/wrap/fit settings.
The optional --preview_pdf always includes placement guides. Invalid rectangles
are skipped with warnings; overlaps and off-page rectangles also produce warnings.
This creates page content, not interactive form fields.
"""

import argparse
from io import BytesIO
from itertools import combinations
import json
import math
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

PADDING = 1.0
MIN_FONT = 4.0


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def spec_pages(spec):
    if isinstance(spec.get("pages"), list):
        return spec["pages"]
    if "page" in spec:
        return [spec]
    raise ValueError("spec.json must contain either 'page' or 'pages'")


def valid_rect(rect):
    return (isinstance(rect, list) and len(rect) == 4
            and all(isinstance(n, (int, float)) and math.isfinite(n) for n in rect)
            and rect[2] > rect[0] and rect[3] > rect[1])


def overlap_area(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def validate_items(page_w, page_h, items):
    messages, rectangles = [], []
    for field in items:
        name, rect = str(field.get("name") or ""), field.get("rect")
        if not valid_rect(rect):
            messages.append(f"[WARN] invalid rect for {name}: {rect}")
            continue
        if rect[0] < 0 or rect[1] < 0 or rect[2] > page_w or rect[3] > page_h:
            messages.append(f"[WARN] rect out of bounds for {name}: {rect} (page {page_w}x{page_h})")
        rectangles.append((name, rect))
    for (first, a), (second, b) in combinations(rectangles, 2):
        intersection = overlap_area(a, b)
        if intersection > 1:
            messages.append(f"[WARN] overlap between {first} and {second}: {intersection:.1f} pt^2")
    return messages


def shrink_to_width(text, font, size, max_width):
    measured = stringWidth(str(text), font, size)
    return (max(MIN_FONT, size * max_width / measured * .98)
            if 0 < max_width < measured else size)


def wrap_words(text, font, size, max_width):
    return simpleSplit(" ".join(str(text).split()), font, size, max_width) or [""]


def text_x(align, x0, x1, width, text_width):
    return {"center": x0 + (width - text_width) / 2,
            "right": x1 - PADDING - text_width}.get(align, x0 + PADDING)


def draw_text_box(pdf, rect, text, *, font, size, align, valign, wrap, shrink):
    left, bottom, right, top = rect
    available = max(0, right - left - 2 * PADDING)
    capacity = max(0, top - bottom - 2 * PADDING)
    text = str(text)
    if not wrap:
        if shrink:
            size = shrink_to_width(text, font, size, available)
        lines, spacing = [text], size
        baseline = {"top": top - PADDING - size,
                    "middle": bottom + (top - bottom - size) / 2}.get(valign, bottom + PADDING)
    else:
        lines = wrap_words(text, font, size, available)
        for _ in range(20):
            if not shrink or len(lines) * size * 1.2 <= capacity or size <= MIN_FONT:
                break
            size = max(MIN_FONT, size * .92)
            lines = wrap_words(text, font, size, available)
        spacing = 1.2 * size
        baseline = bottom + PADDING + (len(lines) - 1) * spacing
        if valign == "top":
            baseline = top - PADDING - spacing
        elif valign == "middle":
            baseline += (capacity - len(lines) * spacing) / 2
    pdf.setFont(font, size)
    for index, line in enumerate(lines):
        x = text_x(align, left, right, right - left, stringWidth(line, font, size))
        pdf.drawString(x, baseline - index * spacing, line)


def draw_checkmark(pdf, rect, checked):
    if checked:
        left, bottom, right, top = rect
        width, height = right - left, top - bottom
        pdf.saveState()
        pdf.setStrokeColorRGB(0, 0, 0)
        pdf.setLineWidth(max(1, min(width, height) * .12))
        stroke = pdf.beginPath()
        for index, (x, y) in enumerate(((.2, .55), (.45, .25), (.82, .8))):
            operation = stroke.moveTo if index == 0 else stroke.lineTo
            operation(left + x * width, bottom + y * height)
        pdf.drawPath(stroke)
        pdf.restoreState()


def build_overlay(page_w, page_h, items, values, *, guides):
    output = BytesIO()
    drawing = Canvas(output, pagesize=(page_w, page_h))
    for field in items:
        box = field.get("rect")
        if not valid_rect(box):
            continue
        identifier = str(field.get("name") or "")
        if guides:
            drawing.saveState()
            drawing.setStrokeColorRGB(1, 0, 0)
            drawing.setFillColorRGB(1, 0, 0)
            drawing.setLineWidth(.75)
            drawing.rect(box[0], box[1], box[2] - box[0], box[3] - box[1])
            drawing.setFont("Helvetica", 8)
            drawing.drawString(box[0] + 2, box[3] + 2, identifier)
            drawing.restoreState()
        value = values.get(identifier)
        if str(field.get("kind", "text")).lower() in ("check", "checkbox"):
            draw_checkmark(drawing, box, bool(value))
        else:
            draw_text_box(drawing, box, "" if value is None else str(value),
                          font=field.get("font", "Helvetica"), size=float(field.get("font_size", 10)),
                          align=str(field.get("align", "left")).lower(),
                          valign=str(field.get("valign", "bottom")).lower(),
                          wrap=bool(field.get("wrap", False)),
                          shrink=str(field.get("fit", "none")).lower() == "shrink_to_fit")
    drawing.showPage()
    drawing.save()
    return output.getvalue()


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for parameter in ("input_pdf", "spec_json", "values_json"):
        cli.add_argument(parameter)
    cli.add_argument("--out", required=True)
    cli.add_argument("--preview_pdf")
    cli.add_argument("--draw_guides", action="store_true")
    options = cli.parse_args()
    instructions = spec_pages(read_json(options.spec_json))
    values = read_json(options.values_json)
    source = PdfReader(options.input_pdf)
    # Prepare all overlays before writing either result, so errors cannot leave
    # a successful-looking final file paired with a failed preview.
    outputs = [(options.out, options.draw_guides)]
    if options.preview_pdf is not None:
        outputs.append((options.preview_pdf, True))
    documents = []
    for filename, guides in outputs:
        document = PdfWriter(clone_from=source)
        for entry in instructions:
            number = int(entry["page"])
            if not 1 <= number <= len(document.pages):
                raise ValueError(f"spec references page {number}, but PDF has {len(document.pages)} pages")
            fields = entry.get("items", [])
            if not isinstance(fields, list):
                raise ValueError("spec 'items' must be a list")
            page = document.pages[number - 1]
            width, height = float(page.mediabox.width), float(page.mediabox.height)
            if filename == options.out:
                for warning in validate_items(width, height, fields):
                    print(warning)
            overlay = PdfReader(BytesIO(build_overlay(width, height, fields, values, guides=guides)))
            page.merge_page(overlay.pages[0])
        documents.append((filename, document))
    for filename, document in documents:
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        document.write(filename)
    if options.preview_pdf is not None:
        print(f"[OK] preview: {options.preview_pdf}")
    print(options.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
