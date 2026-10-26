# Read a PDF with page evidence

Identify the reader's question first: a summary, a precise quotation, a numerical comparison, or a review of design needs different coverage. Confirm the document version and expected scope. For an exhaustive review, cover every page; for a specific question, locate likely pages then inspect their surrounding context.

Start with structure and searchable content:

```sh
python scripts/pdf_inspect.py source.pdf --json
python scripts/pdf_extract.py text source.pdf --out review/text.txt
python scripts/render_pdf.py source.pdf --pages 2-4 --out_dir review/pages --dpi 160
```

Commands resolve from this skill directory. Python dependencies are pinned in `requirements.txt`; rendering additionally needs the chosen backend. Use [preflight](preflight.md) if a file cannot be opened or text extraction is empty. Scanned pages may need [OCR](ocr.md); do not equate an empty extraction with an empty document.

Read rendered figures and tables alongside the extracted text. Verify table headers, units, legends, footnotes, and column order before quoting values. Distinguish printed page labels from one-based file page numbers. A quotation must match the page, including qualifiers that extraction may put elsewhere.

Organize a report around the user's questions, findings and evidence. Cite page locations for important claims. Flag unreadable portions and unsupported inferences. If a surprising result changes the requested scope, ask a focused question while continuing independent reading. Do not silently expand a short summary into an exhaustive audit.
