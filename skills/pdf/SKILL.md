---
name: pdf
description: Read, extract, create, edit, fill, OCR, redact, and validate local PDFs with structural and rendered checks. Use when a PDF is the input or requested deliverable, including interactive forms.
license: See SOURCES.md for provenance
---

# PDF processing

Use local PDF libraries and command-line tools. No Acrobat subscription, cloud OCR, or paid document API is required. Preserve the source and write requested results to a separate workspace path.

The office workflow uses the approved Design Office Artifacts reference, adapted for this package. [SOURCES.md](SOURCES.md) records the selected guidance, replacement scope, and retained notices.

## Tools and task routing

Resolve paths from this skill directory. [requirements.txt](requirements.txt) pins the core Python toolset. Optional tiers are [redaction](requirements-redaction.txt), [browser conversion](requirements-browser.txt), and [OCR](requirements-ocr.txt). Poppler supplies `pdftoppm`/`pdfinfo`; optional conversion routes need LibreOffice, Pandoc, LaTeX, or a local browser as documented in their task guides. OCR also needs Tesseract and language data. Install only the tools for the selected route. Node form/extraction tools have their own [manifest](js/package.json) and lockfile; copy that directory to a writable runtime and use `npm ci`.

| Operation | Guide |
| --- | --- |
| Inspect/read or extract text, tables, images, annotations | [Read/review](tasks/read_review.md), [extraction](tasks/extract.md) |
| Merge, split, rotate, crop, watermark, encrypt, repair | [Editing](tasks/edit.md) |
| Form mapping and field validation | [Field mapping](tasks/form_field_mapping.md), [interactive forms](references/interactive-forms.md) |
| Nonfillable forms and coordinate overlays | [Stamping](tasks/forms_nonfillable.md), [coordinates](tasks/coords.md) |
| Searchable scans | [OCR](tasks/ocr.md) |
| Remove underlying sensitive content | [Redaction](tasks/redact.md) |
| Generate or convert | [Creation](tasks/create.md), [conversion](tasks/convert.md) |
| Compare, preflight, batch | [Comparison](tasks/compare.md), [preflight](tasks/preflight.md), [batch](tasks/batch.md) |
| JavaScript tools or renderer disagreements | [Node helpers](tasks/js_tools.md), [renderer parity](tasks/parity.md) |

For new prose-heavy reports, a local document authoring tool followed by conversion may handle pagination better than manual drawing. Use ReportLab for deliberate programmatic layouts. Either route must produce the requested PDF; no sibling skill is needed.

## Operate and verify

1. Inspect page count, geometry, rotation, text/scanned content, forms, annotations, encryption, and signatures relevant to the task. Keep missing passwords, illegible scans, and ambiguous field mappings explicit.
2. Render relevant input pages, perform the selected operation, and render the final output:

   ```sh
   python scripts/render_pdf.py /absolute/input.pdf --out_dir /absolute/review --dpi 200
   python scripts/compare_renders.py /absolute/before.pdf /absolute/after.pdf --out_dir /absolute/diff --dpi 200
   ```

3. Inspect every authored/changed page and confirm unaffected content remains intact. Extraction success is not layout proof. For forms verify logical values as well as appearances; for redaction verify removal from extractable content, annotations, and metadata as relevant.
4. Reopen the final PDF and check page order, dimensions, requested text/fields, and any structural invariants. Deliver requested files and disclose unsupported or unverified behavior.

Example: “Fill this application without flattening it.” Map named fields, validate values and checkbox states, write a new PDF, reopen the field tree, inspect widget values/appearances, and render the completed form. If names are ambiguous, resolve them rather than stamping text and claiming an interactive result.
