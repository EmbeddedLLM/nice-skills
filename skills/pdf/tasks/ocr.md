# OCR for scanned PDFs (make them searchable)

Reach for this when the PDF is image-only (a scan) and text extraction returns little or nothing.

## Golden path (ocrmypdf)

```bash
python -m pip install -r requirements-ocr.txt
python scripts/ocr_pdf.py scanned.pdf -o searchable.pdf --lang eng
```

Safe defaults in this runtime:

- `--skip-text` — pages that already contain text are not re-OCR'd
- `--deskew` — on
- `--optimize 1` — higher levels want system binaries that are unavailable here

When `ocrmypdf` truly cannot be used, fall back to the explicit fallback pipeline:

```bash
python scripts/ocr_pdf.py scanned.pdf -o searchable.pdf --lang eng --fallback
```

Verify the result:

```bash
python scripts/render_pdf.py searchable.pdf --out_dir work/_renders/ocr --pages 1
python scripts/pdf_extract.py text searchable.pdf --method pdfplumber --out work/_tmp/text.txt
```

When extraction is still poor:

- try `--force` to OCR regardless
- pre-render at a higher DPI and drive a different OCR pipeline (rare)
