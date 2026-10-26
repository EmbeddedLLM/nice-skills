# Map PDF fields before filling

Commands are relative to this skill directory. Use local pypdf/pdfplumber, pdf-lib, ReportLab, and Poppler as appropriate; no paid PDF editor is required.

## Determine the form type

Inspect the document's field tree and widget annotations before writing values:

```bash
python scripts/pdf_extract.py forms input.pdf --out fields.json --include_widgets
```

Match each field's name, type, page, rectangle, and visible label. A field's internal name may not describe its purpose, and one logical field can have multiple widgets. Render the relevant pages to confirm the mapping. XFA forms are not ordinary AcroForms; an incomplete field listing does not prove the document is a flat form. Inspect XFA/unsupported structures before choosing an overlay.

## Fillable fields

Use the actual field names and permitted option/export values, not a guessed label. With the existing `js/fill_form.mjs`, `values.json` is an object mapping names to values:

```json
{ "name": "Ada Lovelace", "agree": true, "delivery": "Email" }
```

- Text fields accept text; check maximum length and font coverage.
- Checkboxes use JSON `true`/`false` for this helper. A string such as `"false"` or `"/Off"` is not a boolean. When using lower-level pypdf instead, inspect the widget's real on/off appearance names rather than assuming `/Yes`.
- Radios and choice fields use an option exposed by that field. Display labels and stored export values may differ; map them explicitly.
- Signatures require a signing workflow, not a text value or a drawn imitation.

```bash
node js/fill_form.mjs --input input.pdf --values values.json --output filled.pdf
```

The helper fails without writing output if a requested name, value, or type is unsupported. Preserve editability unless flattening is requested or required by the delivery contract. Inspect stored values **before** flattening; a flattened PDF correctly has no editable fields to read back. Re-render to check appearance streams, clipping, checkbox/radio states, and printing behavior.

## Non-fillable forms

Prefer existing text/line/rectangle geometry to guessing positions from a full-page screenshot. Use `pdf_extract.py words` or pdfplumber to find labels and potential entry areas; visually verify inferred boxes, especially circles or decorative rectangles that a detector can misclassify. For scans or missing geometry, render and inspect cropped regions, then add crop offsets back to page-image coordinates.

Normalize coordinates before passing them to the existing [box placement workflow](forms_nonfillable.md). Its `rect` is `[left, bottom, right, top]` in PDF points with a bottom-left origin. Anthropic's structure-extraction example uses top-left coordinates; its `fields.json` schema is **not** accepted by our helper.

For an unrotated page with a zero-origin page box of width `W` and height `H`, an image of width `Iw` and height `Ih`, and a top-left pixel box `[x0, y0, x1, y1]`:

```text
rect = [x0 * W/Iw, H - y1 * H/Ih, x1 * W/Iw, H - y0 * H/Ih]
```

For top-left **point** coordinates, omit pixel scaling and still invert the y-axis. For crop offsets or rotated pages, use the actual page transform; the simple formula above is insufficient. See [coordinate guidance](coords.md).

Use one coordinate system per placement specification. Check that boxes stay inside the target page, do not overlap labels or other values, and accommodate the measured text. Generate a guide overlay, inspect it, then render the final stamped PDF. Overlay text is page content, not a newly interactive form field.

## Other PDF operations

Choose text extraction, table extraction, or OCR according to the actual page content. Validate extracted table headers, rows, units, and totals before treating them as structured data. For ReportLab text using built-in fonts, prefer `Paragraph` sub/superscript markup or a font with verified glyph coverage instead of assuming Unicode superscripts will render. Preserve forms, outlines, and metadata when merging pages if they are part of the requested output; page copying alone does not prove document-level structures survived.

## Bundled structure, box, and annotation tools

Install optional Python dependencies with `python -m pip install -r scripts/requirements-forms.txt` (Python 3.10+). These tools run against local libraries only.

```bash
python scripts/extract_form_structure.py input.pdf structure.json
python scripts/check_bounding_boxes.py fields.json
python scripts/create_validation_image.py 1 fields.json page-1.png review.png
python scripts/fill_pdf_form_with_annotations.py input.pdf fields.json annotated.pdf
```

The structure extractor returns candidate word boxes, horizontal lines, small rectangles, and row boundaries in top-left PDF points. Decorative rectangles are not necessarily checkboxes. Its output is evidence for building `fields.json`, not an automatically completed mapping.

These three box/annotation tools use a separate, explicit schema:

```json
{
  "pages": [{ "page_number": 1, "pdf_width": 612, "pdf_height": 792 }],
  "form_fields": [
    {
      "page_number": 1,
      "description": "Name",
      "label_bounding_box": [20, 20, 70, 40],
      "entry_bounding_box": [80, 20, 240, 40],
      "entry_text": { "text": "Ada", "font": "Helvetica", "font_size": 10 }
    }
  ]
}
```

Coordinates are top-left points. For full-page pixel coordinates, set page `units` to `pixels`, supply `image_width`/`image_height`, and retain actual `pdf_width`/`pdf_height` for font-size checking. Font size is always in points. `label_bounding_box` is optional. The checker rejects malformed/out-of-page boxes, overlaps, and entry boxes shorter than their font size; it does not measure text width or guarantee glyph coverage. It returns nonzero for failures. The image helper scales boxes to the full-page image; it can visualize overlaps to aid correction.

The annotation helper writes editable **FreeText annotations**, not interactive AcroForm fields or permanent page text. It requires a new output, checks the full specification before writing, and rejects rotated, cropped, or offset PDF page boxes that require a different transform. Normalize those inputs first, or use an editor that supports their geometry. Renderer support for annotation appearances varies: inspect the output in the target viewer before delivery. For permanent text overlays continue using `place_text_by_boxes.py` and its different bottom-left specification.

For AcroForms, the existing `pdf_extract.py forms --include_widgets` now reports text/checkbox/radio/button/choice/signature kinds, all located widgets, on/off appearance names, and choice export/display pairs. Existing `js/fill_form.mjs` covers filling and flattening, avoiding a second filler with a different value schema or a process-wide pypdf monkeypatch. Use the actual options it exposes; unsupported fields require a deliberate specialized workflow.
