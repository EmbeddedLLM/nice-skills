# Layout for an editable financial model

This is a design guide, not a workbook template or accounting policy. Read [financial model reasoning](../domain_guidance/financial_models.md) for calculation decisions. Preserve an existing model's conventions before applying new visual choices.

## Make the calculation route visible

Arrange source values, assumptions, calculations, and decision outputs so that a reader can follow the model. These roles may share a sheet. Add a separate schedule when its size, refresh cadence, or dependencies make that useful, not merely to satisfy a standard tab count.

Keep actual and projected periods identifiable. Place currency and scale in headings. Use appropriate number formats without changing the underlying precision. Choose a consistent convention for zero, negative values, and multiples; explain any display that hides a distinction the reader needs.

## Give formatting a specific meaning

Use the supplied input/formula/link colours when the workbook already has them. For a new model, establish a small legend before assigning roles. Do not reuse an input colour as decoration or make a review warning depend only on a fill colour. Preserve native formulas and hyperlinks regardless of how they are coloured.

Set readable column widths and align related periods and totals. A restrained rule can separate a subtotal; repeated heavy boxes rarely help trace a calculation. Avoid merged cells in ranges that must sort, expand, or feed charts. Report titles may use a wider narrative region without altering the calculation grid.

## Check the artifact the reader receives

Confirm that input edits update the intended outputs after a real calculation pass. Check source references and independent reconciliations. Inspect the printed layout if delivery includes a PDF: repeating labels, page breaks, and legible scales matter more than fitting every period onto a single page.

Record unavailable calculation or viewer checks. A styled workbook and a formula-cache scan establish different things.

Adapted from the permitted spreadsheet design reference in Design Office Artifacts; complete source and license records are in [SOURCES.md](../SOURCES.md).
