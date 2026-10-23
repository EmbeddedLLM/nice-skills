# Task: read or review a DOCX

## What a review actually covers

| Area               | Look for                                                                           |
| ------------------ | ---------------------------------------------------------------------------------- |
| Layout             | page breaks in odd places, margins, anything clipped or overlapping                |
| Typography         | heading levels that match the outline, one font family per role, even line spacing |
| Tables and figures | alignment, cells too narrow to read, content cut off                               |
| Redlines           | tracked insertions and deletions visible and attributed                            |
| Comments           | present in the package, whether or not they draw                                   |

## Main route: DOCX → PNG

### Packaged renderer

This is the path to take by default. It manages the container-safe LibreOffice profile and writable `HOME` for you and names output `page-<N>.png`.

```bash
python render_docx.py work/report.docx --output_dir work/pages
```

Useful switches: `--verbose` echoes the LibreOffice invocation and its output when a conversion misbehaves; `--emit_pdf` also keeps `<input_stem>.pdf` in the output directory for debugging or archival.

### By hand, only while debugging

If you must drive `soffice` yourself, give it a private profile and a writable home — see `troubleshooting/libreoffice_headless.md` for the exact recipe. The manual route produces `<basename>-<N>.png` from `pdftoppm`, not `page-<N>.png`, so downstream tools that expect the packaged naming will not find your files.

## Judging the run

Success means: one image per page, the page count matches the document, and the pages you read look right.

Ignore stderr. LibreOffice prints things like `error : Unknown IO error` on conversions that worked. File existence plus your own eyes outrank it.

Then go through **every** page rather than sampling one, watching for:

- text clipped at cell or frame boundaries;
- tables that wrapped to a second page unexpectedly;
- a font that silently substituted;
- headers and footers on the wrong side or the wrong page.

## Redlines render; comments do not

Tracked insertions and deletions usually survive the trip to PDF. Comments usually do not, particularly through headless LibreOffice. So:

- a render with no comment bubbles proves nothing either way;
- verify comments structurally (`ooxml/comments.md`), or run `pandoc --track-changes=all` and confirm the comment markup is there.

## Long documents

Render the whole thing, then read in priority order: title page, contents, every section carrying a table or figure, appendices. Spot-check the rest.
