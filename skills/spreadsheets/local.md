# Local spreadsheet workflow

Use openpyxl for editing, optional project-installed pandas for tabular analysis, and LibreOffice for recalculation. This package requires no proprietary spreadsheet runtime.

## Read first, choose the edit boundary

Before modifying a supplied workbook, inspect sheet names, dimensions, merged cells, styles, formulas, named ranges, tables, charts, and external links. Honor the requested tab names, headers, formulas and template conventions. When the task is to update inputs, update the designated inputs; change formulas only when the request requires it. Keep the original file untouched.

For an existing model, load formulas and cached values separately:

```python
from openpyxl import load_workbook

formulas = load_workbook("input.xlsx", data_only=False, keep_links=True)
cached = load_workbook("input.xlsx", data_only=True, keep_links=True)
# Read original cached values from `cached`; make edits only in `formulas`.
```

Never deliver a workbook saved from a `data_only=True` load: its formulas were replaced in memory by cached results. Use `keep_vba=True` when working with `.xlsm`, but do not assume every macro feature or signature survives — openpyxl is not a lossless editor for arbitrary Excel extensions; verify feature preservation or pick a compatible editor when the input needs one.

CSV/TSV files are plain tables: no formulas, formatting, macros or multiple sheets. Preserve identifiers, leading zeros, date conventions and delimiters deliberately. pandas helps with cleaning and aggregation, but writing a DataFrame over an existing workbook replaces layout and formulas. Legacy `.xls` needs a proper reader or conversion route, not openpyxl.

## Author an editable model

- Use formulas for anything that should respond when inputs change; keep assumptions in labeled cells and reference them.
- Before filling a large grid, check a few representative formulas against independently computed expectations — ranges, signs, units, dates, cross-sheet references, not just syntax.
- Quote sheet names containing spaces (`quote_sheetname` helps) and write only to the top-left anchor of merged ranges.
- Keep sources, assumptions, calculations and outputs understandable without forcing each role onto its own sheet. Cite sourced values and mark user-provided assumptions where readers will find them.
- Preserve existing number formats. For new work: show units, store percentages as fractions, distinguish inputs from formulas with a legend, use readable fonts and column widths. Add illustrative rows only to a requested blank template, never to a real dataset being edited.
- Prefer functions the **actual** target application and calculation engine support. Newer functions, prefixes, dynamic arrays and spill metadata vary by version; test with realistic values instead of copying a stale function blacklist or silently replacing a required formula.

## Recalculate and verify

openpyxl writes formula expressions but never calculates them. Calculation-on-open flags are requests to the next application, not evidence of current results, and an error-free cache scan proves neither business logic nor freshness.

The bundled helper covers ordinary, self-contained `.xlsx` workbooks:

```bash
python scripts/recalculate.py input.xlsx --output recalculated.xlsx --timeout 60
```

It works on a temporary copy with an isolated LibreOffice profile, leaves the input untouched, refuses to overwrite an existing output, and rejects workbooks with external links or macros. Read the JSON report and exit status: `0` = checked formula caches passed, `2` = formula errors or unverifiable caches found (a diagnostic workbook may be saved — fix and recheck before delivery), `1` = recalculation failed or was refused.

To inspect an existing file's cached results without recalculating:

```bash
python scripts/recalculate.py input.xlsx --check-only
```

Missing cache entries are reported separately from typed spreadsheet errors, and ordinary text mentioning `#REF!` is not itself an error cell. Review representative outputs against known answers and compare formula locations before and after.

External workbook links need special care: saving through openpyxl can clear their cached values, and another application may fail to resolve or may rewrite the links. Keep the original, obtain the linked sources or use a compatible editing workflow, and don't collapse links to fixed values unless that is what the user asked for. The helper has no destructive force mode.

LibreOffice conversion can alter unsupported Excel features even in plain `.xlsx`. Don't use it to certify preservation of complex charts, data models, signatures or other application-specific extensions: check the features that matter, inspect rendered/printed output when layout matters, and state plainly any verification that could not be performed. Deliver the spreadsheet — not a claim that unperformed checks passed.
