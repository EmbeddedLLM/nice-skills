# Remove content from a PDF

Establish exactly what must disappear and where it may occur. Text, scanned images, annotations, attachments and metadata are distinct storage locations. The bundled PyMuPDF helper modifies page content; it does not promise complete sanitization of every document container. Preserve the original in the authorized workspace and deliver the new redacted file separately.

For searchable text:

```sh
python scripts/pdf_redact.py text source.pdf released.pdf --text "Internal example" --pages 1-3
```

Use `--ignore_case` only when intended; `--whole_word` changes matching behavior. A phrase file can be supplied with `--text_file`. Read warnings about zero matches as missing evidence, not successful removal. Install `requirements-redaction.txt`.

For an area, use `boxes` with `--boxes_json regions.json`. The simple payload is `{"items":[{"page":1,"rect":[40,70,220,95]}]}`. Rectangles use PyMuPDF's top-left point coordinates. The box picker's bottom-left coordinates must be converted before use; see [coordinates](coords.md). On scans, choose `--image_mode pixels` or `remove` according to whether intersecting image areas or entire images should be removed. Inspect collateral changes to nearby content.

Verification has two parts. Render the released PDF and inspect each removal region plus neighboring content. Separately extract text from the released file and search for the targets and their known variants. Confirm extraction itself succeeded before interpreting no matches. For image-only content, an empty text search cannot prove removal: inspect the resulting pixels.

Review annotations, attachments and metadata for copies when they are in scope. Reopen the final deliverable, confirm it is the redacted version, and report which removal checks ran. Covering text with a stamp or setting a CropBox does not remove the content beneath it.
