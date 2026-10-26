"""Survey a flat (non-fillable) PDF for the geometry a form-filler needs.

Walks each page with pdfplumber and records:
  * every word, with its bounding box (candidate field labels)
  * long horizontal rules (candidate row separators)
  * small square-ish rectangles (candidate checkboxes)
  * row bands derived from consecutive horizontal rules

The result is JSON to drive accurate field placement; every coordinate is a
*candidate* and still needs visual confirmation before filling.

Usage: python extract_form_structure.py <input.pdf> <output.json>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pdfplumber

#: A rule counts as a row separator when it spans at least this much of the page.
_ROW_RULE_MIN_SPAN = 0.5
#: Square-ish vector marks within this point range read as checkboxes.
_CHECKBOX_MIN_PT = 5
_CHECKBOX_MAX_PT = 15


def _round(value) -> float:
    return round(float(value), 1)


def _page_words(page, page_number: int) -> list[dict]:
    return [
        {
            "page": page_number,
            "text": word["text"],
            "x0": _round(word["x0"]),
            "top": _round(word["top"]),
            "x1": _round(word["x1"]),
            "bottom": _round(word["bottom"]),
        }
        for word in page.extract_words()
    ]


def _row_rules(page, page_number: int) -> list[dict]:
    rules = []
    for line in page.lines:
        horizontal = abs(float(line["top"]) - float(line["bottom"])) < 1
        spans_page = abs(float(line["x1"]) - float(line["x0"])) > page.width * _ROW_RULE_MIN_SPAN
        if horizontal and spans_page:
            rules.append({
                "page": page_number,
                "y": _round(line["top"]),
                "x0": _round(line["x0"]),
                "x1": _round(line["x1"]),
            })
    return rules


def _checkbox_marks(page, page_number: int) -> list[dict]:
    marks = []
    for rect in page.rects:
        width = float(rect["x1"]) - float(rect["x0"])
        height = float(rect["bottom"]) - float(rect["top"])
        square = abs(width - height) < 2
        if square and _CHECKBOX_MIN_PT <= width <= _CHECKBOX_MAX_PT:
            marks.append({
                "page": page_number,
                "x0": _round(rect["x0"]),
                "top": _round(rect["top"]),
                "x1": _round(rect["x1"]),
                "bottom": _round(rect["bottom"]),
                "center_x": _round((float(rect["x0"]) + float(rect["x1"])) / 2),
                "center_y": _round((float(rect["top"]) + float(rect["bottom"])) / 2),
            })
    return marks


def _row_bands(rules: list[dict]) -> list[dict]:
    bands = []
    by_page: dict[int, list[float]] = {}
    for rule in rules:
        by_page.setdefault(rule["page"], []).append(rule["y"])
    for page, heights in by_page.items():
        stops = sorted(set(heights))
        for top, bottom in zip(stops, stops[1:]):
            bands.append({
                "page": page,
                "row_top": top,
                "row_bottom": bottom,
                "row_height": round(bottom - top, 1),
            })
    return bands


def survey_pdf(pdf_path) -> dict:
    survey = {
        "coordinate_system": "top-left PDF points; candidates require visual verification",
        "pages": [],
        "labels": [],
        "lines": [],
        "checkboxes": [],
        "row_boundaries": [],
    }
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            survey["pages"].append({
                "page_number": page_number,
                "width": float(page.width),
                "height": float(page.height),
            })
            survey["labels"].extend(_page_words(page, page_number))
            survey["lines"].extend(_row_rules(page, page_number))
            survey["checkboxes"].extend(_checkbox_marks(page, page_number))
    survey["row_boundaries"] = _row_bands(survey["lines"])
    return survey


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", type=Path, help="Flat PDF to survey")
    parser.add_argument("output", type=Path, help="Destination JSON file")
    args = parser.parse_args()

    print(f"Surveying {args.input} ...")
    survey = survey_pdf(args.input)
    args.output.write_text(json.dumps(survey, indent=2), encoding="utf-8")

    print("Found:")
    print(f"  - {len(survey['pages'])} page(s)")
    print(f"  - {len(survey['labels'])} word(s)")
    print(f"  - {len(survey['lines'])} row rule(s)")
    print(f"  - {len(survey['checkboxes'])} checkbox mark(s)")
    print(f"  - {len(survey['row_boundaries'])} row band(s)")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
