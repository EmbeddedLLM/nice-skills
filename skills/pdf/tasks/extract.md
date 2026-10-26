# Extract reusable content

Decide what must be preserved in the extraction: exact wording, reading order, cell structure, geometry, or embedded file bytes. No single output representation preserves all of these. Inspect a sample page before processing the full file.

The wrapper `scripts/pdf_extract.py` offers the following routes:

| Output needed       | Example                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------- |
| Searchable text     | `python scripts/pdf_extract.py text source.pdf --method pdfplumber --out review/text.txt`   |
| Word positions      | `python scripts/pdf_extract.py words source.pdf --method pymupdf --out review/words.csv`    |
| Character positions | `python scripts/pdf_extract.py chars source.pdf --out review/chars.csv`                     |
| Candidate tables    | `python scripts/pdf_extract.py tables source.pdf --out_dir review/tables --format csv`      |
| Embedded images     | `python scripts/pdf_extract.py images source.pdf --out_dir review/images`                   |
| Attached files      | `python scripts/pdf_extract.py attachments source.pdf --out_dir review/attachments`         |
| Annotation records  | `python scripts/pdf_extract.py annotations source.pdf --out review/annotations.json`        |
| Form definitions    | `python scripts/pdf_extract.py forms source.pdf --include_widgets --out review/fields.json` |

Use `--help` on the selected subcommand for page filtering and backend choices. Core Python dependencies are pinned in `requirements.txt`; some routes need optional PyMuPDF or Poppler. Missing tools or encrypted inputs require explicit resolution, not a fabricated empty result.

Word/character coordinates use top-left conventions; they are not directly interchangeable with ReportLab overlay coordinates. Consult [coordinates](coords.md) before using them to place or remove content.

Table detection is heuristic. Check headers, merged cells, negative signs, decimal separators, units and totals against rendered pages. A CSV with plausible rows is not proof of correct cell boundaries. For scans, [OCR](ocr.md) may recover text but still require table reconstruction. Keep uncertain cells marked rather than silently guessing values.

Image extraction returns stored assets, which can differ from their clipped or transformed page appearance. Use rendered page regions when the request is about what a reader sees. Inspect attachments before treating them as relevant sources; extraction does not authorize executing their contents.
