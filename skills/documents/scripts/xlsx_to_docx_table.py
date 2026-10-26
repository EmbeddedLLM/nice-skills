#!/usr/bin/env python3
"""Turn one XLSX worksheet into a plain DOCX table.

The minimum useful converter for reports: read the used range of a sheet,
build a grid table, bold the leading rows, copy basic cell alignment, and size
columns from a content-length heuristic.

Deliberately out of scope: formulas (values are read data-only), merged cells,
conditional formatting, charts, and rich number formats. Number formatting is
approximated; when exact appearance matters, export the range as an image
instead.

    python scripts/xlsx_to_docx_table.py data.xlsx table.docx --title "Table: Results"
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches
from openpyxl import load_workbook

# Column-width heuristic: inches per character, with a floor and a ceiling.
INCHES_PER_CHAR = 0.12
MIN_COLUMN_INCHES = 0.8
MAX_COLUMN_INCHES = 3.0
MIN_CHARS_FOR_WIDTH = 4

ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
}


@dataclass
class SheetGrid:
    """Formatted cell text plus the widest entry per column."""

    rows: list[list[str]]
    column_widths: list[float]
    title: str

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.column_widths)


def is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def format_value(cell) -> str:
    """Approximate what Excel would display for one cell."""
    value = cell.value
    if value is None:
        return ""
    if isinstance(value, (bool, int)):
        return str(value)
    if isinstance(value, float):
        number_format = (cell.number_format or "").lower()
        if "%" in number_format:
            return f"{value * 100:.2f}%"
        if "$" in number_format:
            return f"${value:,.2f}"
        return f"{value:g}"
    if isinstance(value, (dt.datetime, dt.date)):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return str(value)


def used_bounds(worksheet) -> tuple[int, int]:
    """Last row/column holding content; the sheet's own maxima include padding."""
    last_row = last_column = 0
    for row in worksheet.iter_rows():
        for cell in row:
            if not is_blank(cell.value):
                last_row = max(last_row, cell.row)
                last_column = max(last_column, cell.column)
    return last_row, last_column


def column_width(character_counts: list[int]) -> list[float]:
    return [
        max(MIN_COLUMN_INCHES, min(MAX_COLUMN_INCHES, INCHES_PER_CHAR * max(count, MIN_CHARS_FOR_WIDTH)))
        for count in character_counts
    ]


def read_grid(worksheet, sheet_label: str) -> SheetGrid:
    rows_count, cols_count = used_bounds(worksheet)
    if rows_count == 0 or cols_count == 0:
        raise RuntimeError("Sheet appears empty")

    widest = [0] * cols_count
    rows: list[list[str]] = []
    for row_index in range(1, rows_count + 1):
        formatted = []
        for col_index in range(1, cols_count + 1):
            text = format_value(worksheet.cell(row=row_index, column=col_index))
            formatted.append(text)
            widest[col_index - 1] = max(widest[col_index - 1], len(text))
        rows.append(formatted)

    return SheetGrid(rows=rows, column_widths=column_width(widest), title=sheet_label)


def mark_as_header_row(row) -> None:
    """Flag a row so it repeats across pages and is exposed as a table header."""
    properties = row._tr.get_or_add_trPr()
    if properties.find(qn("w:tblHeader")) is None:
        properties.append(OxmlElement("w:tblHeader"))


def build_document(grid: SheetGrid, worksheet, title: str | None, header_rows: int) -> Document:
    document = Document()
    if title:
        document.add_paragraph(title)

    table = document.add_table(rows=grid.row_count, cols=grid.column_count)
    table.style = "Table Grid"
    table.autofit = False

    for row_index in range(grid.row_count):
        for col_index in range(grid.column_count):
            source = worksheet.cell(row=row_index + 1, column=col_index + 1)
            target = table.cell(row_index, col_index)
            target.width = Inches(grid.column_widths[col_index])

            paragraph = target.paragraphs[0]
            paragraph.text = grid.rows[row_index][col_index]

            alignment = getattr(source.alignment, "horizontal", None)
            if alignment in ALIGNMENTS:
                paragraph.alignment = ALIGNMENTS[alignment]

            if row_index < header_rows:
                for run in paragraph.runs:
                    run.bold = True

        if row_index < header_rows:
            mark_as_header_row(table.rows[row_index])

    return document


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert an XLSX sheet to a DOCX table")
    ap.add_argument("xlsx", type=Path)
    # The positional output came first; --out is accepted because callers assume it.
    ap.add_argument("out_docx", type=Path, nargs="?", default=None)
    ap.add_argument("--out", type=Path, default=None, help="Output DOCX path (alias)")
    ap.add_argument("--sheet", default=None, help="Sheet name (default: active)")
    ap.add_argument("--header_rows", type=int, default=1, help="How many top rows to bold")
    ap.add_argument("--title", default=None, help="Optional title paragraph above the table")
    args = ap.parse_args()

    out_path = args.out or args.out_docx
    if out_path is None:
        raise RuntimeError("Missing output path. Provide a positional out_docx or --out.")
    if not args.xlsx.exists():
        raise FileNotFoundError(args.xlsx)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    workbook = load_workbook(args.xlsx, data_only=True)
    worksheet = workbook[args.sheet] if args.sheet else workbook.active

    grid = read_grid(worksheet, worksheet.title)
    build_document(grid, worksheet, args.title, args.header_rows).save(str(out_path))

    print(f"[OK] Wrote {out_path} (rows={grid.row_count}, cols={grid.column_count}, "
          f"sheet={grid.title!r})")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - the CLI reports and exits
        if os.environ.get("DOCS_DEBUG") == "1":
            raise
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(2)
