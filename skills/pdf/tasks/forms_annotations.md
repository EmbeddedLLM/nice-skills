# Fill fields without changing the intended form behavior

First identify whether the PDF has AcroForm fields, XFA data, annotations, or only page graphics. These require different operations. Decide whether the recipient must continue editing fields. Flattening removes that ability and is appropriate only when the requested deliverable allows it.

Inspect and map the actual fields:

```sh
python scripts/pdf_extract.py forms application.pdf --include_widgets --out review/fields.json
```

Match field names, types, widgets and page locations to the requested answers. Use [field mapping](form_field_mapping.md) and [interactive form details](../references/interactive-forms.md) for ambiguous labels or multiple widgets. Do not infer answers from nearby content when user intent is missing.

Prepare the local [Node runtime](js_tools.md), then fill using a JSON file:

```sh
node js/fill_form.mjs --input application.pdf --values values.json --output completed.pdf
```

The helper validates names, types, text limits and listed choices before saving. Invalid input fails the entire request without writing a partial result. Keep `--flatten` off for interactive delivery; add it only for an agreed fixed copy. Unsupported XFA or unusual fields require an appropriate tool or an explicit limitation, not a claim that a flat overlay preserves form functionality.

Reopen the unflattened output and compare field values, field count, widget pages and retained unrelated content. Render each changed page and check long values, checkboxes, radio groups and clipping. When flattening, verify text/marks in the page appearance and confirm the fields are no longer interactive; do not expect field extraction to return values from a flattened file.

FreeText annotations are another distinct output. `fill_pdf_form_with_annotations.py` adds those from validated geometry; it does not create form fields. Use it only when review annotations are wanted. For flat page content see [stamping](forms_nonfillable.md). For stored values that render incorrectly, follow [debugging](forms_debugging.md).
