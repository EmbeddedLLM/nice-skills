# Task: verify a render (DOCX → PNG)

## The reason for this step

Every tool in this package can exit 0 and still leave you with a document that looks broken. Rendering is the only check that sees the result the reader sees, so it is not optional before delivery.

## Use the packaged renderer

It sets up its own LibreOffice profile and writable `HOME`, and writes `page-<N>.png` per page:

```bash
python render_docx.py work/report.docx --output_dir work/pages
```

- `--verbose` — print the LibreOffice command and everything it emitted; the first thing to try when no images appear.
- `--emit_pdf` — additionally keep `<input_stem>.pdf` in the output directory. Off by default so intermediate PDFs are not mistaken for deliverables.

If you need the raw `soffice` / `pdftoppm` invocation instead, it is in `troubleshooting/libreoffice_headless.md`.

## Success criteria

- a PNG exists for every page;
- the page count matches what the document should have;
- the pages you inspect look correct.

Do not read stderr as a verdict: LibreOffice emits alarming lines such as `error : Unknown IO error` on perfectly good conversions. When `--emit_pdf` was used, also confirm the PDF exists and is not empty.

## What to look for in the images

- clipped text — headings and table cells are where it hides;
- objects drawn on top of each other;
- tables that wrapped, shifted, or lost borders;
- substituted fonts;
- header/footer placement and page-break positions.

## Known limits of the render

- **Comments** frequently do not draw at all in headless LibreOffice output. Check them structurally instead.
- **Field codes** — page numbers, TOC entries — can show cached or placeholder values. If the reader needs them correct, update fields before the final render or confirm in Word.
- **Mixed sections** with different page sizes or orientations: DPI is derived from the first section, so later pages may look mis-scaled. Override with `--dpi`.

## Before handing over

- the DOCX carries no leftover placeholder text or internal citation tokens;
- every page of the final render reads correctly;
- `work` holds only the outputs the user asked for.
