# Local Node helpers

The `js/` package pins pdf-lib for AcroForm work and PDF.js for a second text extraction route. Prepare a writable copy of that package with `npm ci`; it needs Node compatible with `package.json`, registry access or an existing package cache, and no paid service. Do not install into a read-only published skill directory. Run the commands below from the prepared package's parent directory.

```sh
node js/extract_form_fields.mjs --input application.pdf
node js/fill_form.mjs application.pdf values.json completed.pdf
node js/extract_text_pdfjs.mjs --input application.pdf > review.txt
```

The fill command also accepts `--input`, `--values` (alias `--fields`) and `--output`. `--flatten` is optional and removes interactivity. A mapping such as `{"contact":"Casey Example","consent":true,"tier":"Basic"}` uses field names found during inspection; choices must exist in that specific form. Validation failure writes no result. Existing output paths are overwritten only after a successful fill/save, so choose a separate destination.

PDF.js writes text items in page order with blank lines separating pages. This is a cross-check for extractable text, not a reconstruction of tables or reading order. Errors exit nonzero; capture stderr separately from the text file.

If Node dependencies are unavailable, Python text extraction remains usable. Python `pdf_edit.py fill-form application.pdf values.json -o completed.pdf` is an alternative AcroForm backend, but verify its accepted field values and appearance behavior separately. Neither route should be described as equivalent to an unavailable end-to-end viewer check.
