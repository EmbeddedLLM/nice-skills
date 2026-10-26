# Change an existing workbook

A successful edit changes the intended result and keeps the rest of the workbook usable. Use [local.md](../local.md) for loading, recalculation, and tool limitations.

## Establish a before-state

Read the requested cells and the calculations or charts that consume them. Record relevant sheet names, formulas, validations, table ranges, formats, hidden regions, links, and print settings. Inspect an available preview if appearance matters. Keep the input file so that both structural and visual differences can be checked later.

Choose the editor after identifying the features that must survive. An XLSM file, pivot cache, signed package, or external-data connection can require a more capable round trip than a plain grid. Do not accept a library's successful save as proof that these features survived.

## Apply the smallest complete change

Update the requested values or formulas and extend dependent ranges when necessary. A new table row may need a formula, validation rule, chart reference, and conditional format as well as its values. Follow the neighboring model's conventions unless the user requested a redesign. Keep unrelated sheet ordering, names, protection, and presentation intact.

For inserted periods, inspect translated formulas at both ends of the new range. Check mixed references and named ranges explicitly. Avoid pasting calculated values over formulas that are supposed to respond to later edits.

## Compare and deliver

Reopen the saved file and compare the intended edit region and a representative unaffected region against the before-state. Recalculate when needed; confirm the affected output changes for a disposable test input. Check print views or chart placement after layout changes. A pre-existing unrelated defect belongs in the handoff, not in an unrequested repair.

Adapted for the local toolchain from Design Office Artifacts' spreadsheet preservation guidance; see [SOURCES.md](../SOURCES.md).
