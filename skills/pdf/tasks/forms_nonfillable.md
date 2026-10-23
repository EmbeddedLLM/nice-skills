# Place content on a flat form

Use this route for a confirmed flat page when interactive fields are not needed. An empty field listing can also indicate an unsupported form format; inspect before deciding to stamp over it. Overlays add selectable page content but do not create editable AcroForm fields.

Render the relevant page and prepare a local rectangle picker:

```sh
python scripts/box_picker_html.py application.pdf --page 1 --dpi 150 --out review/picker.html
```

Open the generated HTML locally, draw entry regions and save its JSON export. Each item names a value and uses bottom-left PDF-point rectangles:

```json
{
  "page": 1,
  "items": [
    { "name": "contact", "rect": [54, 600, 260, 618], "font_size": 10, "fit": "shrink_to_fit" },
    { "name": "consent", "kind": "check", "rect": [54, 560, 68, 574] }
  ]
}
```

Save `{"contact":"Casey Example","consent":true}` as `values.json`. Multiple pages use a `pages` array containing page/item objects. Check [coordinates](coords.md) for rotation and crop limits before using the exported geometry.

```sh
python scripts/place_text_by_boxes.py application.pdf boxes.json values.json --out completed.pdf --preview_pdf review/guides.pdf
python scripts/render_pdf.py review/guides.pdf --out_dir review/guides
python scripts/render_pdf.py completed.pdf --out_dir review/final
```

Inspect both PDFs. The preview always adds red guides; `--draw_guides` also adds them to the final output, so omit that option for delivery. Text supports `align`, `valign`, `wrap`, font and size. Shrinking has a minimum size and cannot ensure arbitrary text fits. Inspect readability instead of continually shrinking.

The helper warns and skips malformed rectangles; out-of-bounds and overlapping rectangles produce warnings but can still be drawn. Missing values become blank text/unchecked marks. Resolve unintended warnings and omissions before delivery. An invalid page reference or item-list shape fails before writing the outputs. Verify source text and required document features remain present after stamping.
