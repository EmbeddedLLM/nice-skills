# Task: moving tables between Word and Excel

## Goal

Get tabular data from a spreadsheet into a document, or out again, without anyone re-typing it.

## XLSX → Word table

```bash
python scripts/xlsx_to_docx_table.py work/results.xlsx work/table.docx --title "Table: Results"
```

The output path may be positional or given as `--out`. Other switches: `--sheet` picks a worksheet (default: the active one) and `--header_rows` says how many leading rows to bold (default 1).

Kept, on a best-effort basis:

- cell values, read data-only so formulas contribute their cached results;
- horizontal alignment per cell;
- header rows in bold;
- column widths, estimated heuristically.

Not kept: merged cells, formulas themselves, charts, conditional formatting, and elaborate number formats.

## Word table → CSV

```bash
python scripts/docx_table_to_csv.py work/report.docx --table_index 0 --out work/table0.csv
```

`--table_index` selects which table in the document (default 0).

## Table review checklist for the rendered pages

- the table fits inside the margins with no column clipped;
- the header row is visually distinct;
- numbers line up consistently, decimals above all;
- no cell wraps in a way that hurts readability.

## Pitfalls

- Word does not adopt Excel's column widths. Verify visually and adjust.
- Multi-line cells and merged cells survive the round trip badly; simplify the source sheet before converting.
