#!/usr/bin/env python3
"""Set fixed unmerged-table widths or audit their saved OOXML declarations.

CLI: table_geometry.py report.docx (0: consistent; 1: geometry findings).
Python: apply_table_geometry(table, column_widths_from_weights([1, 2], 9000)).
Requires python-docx and lxml. Widths use DXA/twips, not EMUs. Geometry is a
local convention: table width, grid and cells agree; indent matches start cell
margin. This does not predict pagination or validate merged table layouts.
"""
import argparse
import math

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement

from word_package import DOCUMENT, Package, tag

DEFAULT_CONTENT_WIDTH_DXA = 9360
DEFAULT_CELL_MARGINS_DXA = {"top": 80, "bottom": 80, "start": 120, "end": 120}
DEFAULT_TABLE_INDENT_DXA = 120


def length_to_dxa(length):
    return round(length.twips if hasattr(length, "twips") else float(length))


def section_content_width_dxa(section):
    return length_to_dxa(section.page_width) - sum(length_to_dxa(value) for value in (section.left_margin, section.right_margin))


def exact_column_widths(widths_dxa, total_width_dxa=DEFAULT_CONTENT_WIDTH_DXA):
    values = list(map(int, widths_dxa))
    if not values or min(values) <= 0:
        raise ValueError("column widths must be nonempty and positive")
    values[-1] = int(total_width_dxa) - sum(values[:-1])
    if values[-1] <= 0:
        raise ValueError("adjusted final column must be positive")
    return values


def column_widths_from_weights(weights, total_width_dxa=DEFAULT_CONTENT_WIDTH_DXA):
    values = list(map(float, weights))
    if not values or any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("weights must be nonempty, finite and positive")
    return exact_column_widths([round(total_width_dxa * v / sum(values)) for v in values], total_width_dxa)


def _set(parent, local, **attributes):
    node = parent.find(tag(local))
    if node is None:
        node = OxmlElement("w:" + local)
        parent.append(node)
    for key, value in attributes.items():
        node.set(tag(key), str(value))
    return node


def apply_table_geometry(table, column_widths_dxa, *, table_width_dxa=None, indent_dxa=None, cell_margins_dxa=None):
    widths = list(map(int, column_widths_dxa))
    if not widths or min(widths) <= 0:
        raise ValueError("column_widths_dxa must contain positive widths")
    total = sum(widths) if table_width_dxa is None else int(table_width_dxa)
    if sum(widths) != total:
        raise ValueError("column widths must sum to table_width_dxa")
    # Validate every physical row before modifying the table; python-docx's row.cells
    # repeats merged cells and therefore cannot establish that the table is unmerged.
    rows = table._tbl.findall(tag("tr"))
    for row in rows:
        cells = row.findall(tag("tc"))
        if len(cells) != len(widths) or any(c.find(".//" + tag(name)) is not None for c in cells for name in ("gridSpan", "vMerge")):
            raise ValueError("apply_table_geometry expects unmerged rows matching the grid")
    margins = {**DEFAULT_CELL_MARGINS_DXA, **(cell_margins_dxa or {})}
    if any(int(value) < 0 for value in margins.values()):
        raise ValueError("cell margins cannot be negative")
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    _set(table._tbl.tblPr, "tblW", type="dxa", w=total)
    _set(table._tbl.tblPr, "tblInd", type="dxa", w=margins["start"] if indent_dxa is None else int(indent_dxa))
    grid = table._tbl.tblGrid
    for node in list(grid):
        grid.remove(node)
    for width in widths:
        column = OxmlElement("w:gridCol")
        column.set(tag("w"), str(width))
        grid.append(column)
    for row in rows:
        height = row.find(tag("trPr") + "/" + tag("trHeight"))
        if height is not None:
            height.getparent().remove(height)
        for cell, width in zip(row.findall(tag("tc")), widths):
            properties = cell.get_or_add_tcPr()
            _set(properties, "tcW", type="dxa", w=width)
            padding = _set(properties, "tcMar")
            for side in DEFAULT_CELL_MARGINS_DXA:
                _set(padding, side, type="dxa", w=int(margins[side]))


def audit_docx_tables(path):
    root = Package(path).xml(DOCUMENT)
    count = 0
    for number, table in enumerate(root.iter(tag("tbl")), 1):
        def declared(local):
            node = table.find(tag("tblPr") + "/" + tag(local))
            return (node.get(tag("type")), int(node.get(tag("w"), 0))) if node is not None else (None, None)
        width_type, width = declared("tblW")
        indent_type, indent = declared("tblInd")
        width = width or 0
        grid = [int(node.get(tag("w"), 0)) for node in table.findall(tag("tblGrid") + "/" + tag("gridCol"))]
        margins = [int(node.get(tag("w"), 0)) for node in table.findall(".//" + tag("tcMar") + "/" + tag("start"))]
        expected = margins[0] if margins else DEFAULT_TABLE_INDENT_DXA
        print(f"table {number}: tblW={width_type}:{width} tblInd={indent_type}:{indent} grid_sum={sum(grid)} grid={grid}")
        problems = []
        if width_type != "dxa" or width <= 0:
            problems.append("table width is missing or not DXA")
        if indent_type != "dxa" or indent is None:
            problems.append("table indent is missing or not DXA")
        elif indent != expected:
            problems.append(f"table indent should match start cell margin ({expected} DXA) so the visible border aligns with body text")
        if len(set(margins)) > 1:
            problems.append("start cell margins are inconsistent within the table")
        if sum(grid) != width:
            problems.append("grid column sum does not equal table width")
        for problem in problems:
            print("  ISSUE: " + problem)
        count += len(problems)
        for number, row in enumerate(table.findall(tag("tr")), 1):
            cells = [cell.find(tag("tcPr") + "/" + tag("tcW")) for cell in row.findall(tag("tc"))]
            values = [int(node.get(tag("w"), 0)) if node is not None else 0 for node in cells]
            print(f"  row {number}: tcW={values} sum={sum(values)}")
            if values != grid:
                count += 1
                print("  ISSUE: row cell widths do not match grid columns")
    print(f"ISSUES: {count}" if count else "OK: all tables have matching tblW, tblInd, tblGrid, and tcW")
    return count


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("docx")
    raise SystemExit(int(bool(audit_docx_tables(cli.parse_args().docx))))
