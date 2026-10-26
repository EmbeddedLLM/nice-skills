---
name: spreadsheets
description: Create, inspect, analyze, and edit local spreadsheets while preserving formulas, formats, and data meaning, with explicit recalculation and cache checks. Use for XLSX, XLSM, CSV, and TSV work rather than a proprietary spreadsheet runtime.
license: See SOURCES.md for provenance
---

# Spreadsheets

Use local openpyxl and optional LibreOffice. No Excel subscription, Google Sheets account, OpenAI artifact runtime, or paid analysis API is required. [requirements.txt](requirements.txt) pins the Python dependencies.

The office workflow uses the approved Design Office Artifacts reference, adapted for this package. [SOURCES.md](SOURCES.md) records the selected guidance, replacement scope, and retained notices.

## Inspect and choose the edit boundary

Read [local workflow](local.md) before editing. Identify sheets, ranges, types, formulas, cached values, named ranges, tables, charts, links, and macros. Read-only questions should leave the workbook unchanged. Preserve the original and update only the requested inputs and affected dependencies.

Load formulas with `data_only=False` and inspect caches separately with `data_only=True`; never save the cache-only load as the editable workbook. Use `keep_vba=True` when appropriate, but verify important macro/extension features with a compatible application. Legacy `.xls` needs a proper reader or conversion. CSV/TSV cannot preserve workbook formulas, styling, or multiple tabs.

## Build understandable calculations

Keep source data and assumptions identifiable; let calculations feed outputs without duplicated logic. Roles can share one sheet. Use a separate audit area only when useful, and keep it independent of the calculations it checks.

- Store dates, numbers, percentages, and currencies as typed values. Preserve identifiers and leading zeros. Label units, periods, populations, sources, and assumptions.
- Keep adjustable assumptions in cells and use formulas for results that must respond to edits. Anchor references deliberately; quote sheet names and test copied formulas at boundaries.
- Distinguish missing values, real zero, and not-applicable. Do not hide broken prerequisites with blanket `IFERROR(...,0)`. Preserve deliberate zero overrides.
- Aggregate amounts by sum, balances by period endpoint, and rates from their components. Do not average or sum incompatible percentages.
- Choose functions supported by the actual target engine. Test missing/duplicate keys, thresholds, dates, and scenarios. For complex modeling use [financial models](templates/financial_models.md); for charts read [charts](features/charts.md).
- Preserve the existing layout on narrow edits. For new work, make inputs and outputs legible with restrained formatting, useful widths, and clear number formats.

## Recalculate and verify

openpyxl writes formulas but does not calculate them. Calculation-on-open flags and old caches are not proof of fresh results.

```sh
python scripts/recalculate.py /absolute/input.xlsx --output /absolute/recalculated.xlsx --timeout 60
python scripts/recalculate.py /absolute/recalculated.xlsx --check-only
```

The helper uses an isolated LibreOffice profile and temporary copy, refuses existing outputs, and rejects external links/macros. Exit `0` means implemented cache checks passed; `2` reports formula errors/unverifiable caches; `1` reports refusal or execution failure. It does not certify preservation of every Excel feature.

Independently check representative results and totals, edit disposable test inputs to verify dependency updates, inspect formula locations before/after, and scan typed error cells. Review rendered/printed sheets where appearance changed. If LibreOffice or another compatible calculation engine is unavailable, deliver only with an explicit recalculation limitation; do not replace formulas with fabricated cached values.

Example: “Update monthly actuals and extend the forecast one quarter.” Preserve actuals, copy period-aware formulas, test the first new period and a changed assumption, reconcile totals, and report any unavailable native-feature checks.
