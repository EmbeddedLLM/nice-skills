---
name: documents
description: Create, inspect, edit, redline, and comment on Word DOCX files while preserving document structure and verifying rendered pages. Use when the Word artifact, formatting, revisions, or comments are part of the task.
license: See SOURCES.md for provenance and bundled notices
---

# Word documents

Produce the requested DOCX with accurate content and readable pages. Use Python and local Office-compatible tools; Microsoft Office, Google Workspace, and paid authoring APIs are not required. Pure drafting does not require this file-format workflow.

The office workflow uses the approved Design Office Artifacts reference, adapted for this package. [SOURCES.md](SOURCES.md) records the selected guidance, replacement scope, and retained notices.

## Prerequisites and paths

Resolve bundled paths from this directory. Work on a copy in the user's workspace. Python dependencies are pinned in [requirements.txt](requirements.txt); install only in a project-local environment. Rendering needs LibreOffice Writer (`soffice`) and Poppler (`pdftoppm`, `pdfinfo`) on PATH. If unavailable, perform supported structural checks and explicitly report that layout remains unverified.

## Select the operation

| Task | Read |
| --- | --- |
| Create or edit while preserving a template | [Creation safeguards](tasks/creation_safeguards.md), [create/edit](tasks/create_edit.md) |
| Inspect without changing the file | [Read/review](tasks/read_review.md) |
| Redlines and clean copies | [Tracked changes](ooxml/tracked_changes.md), [revision lifecycle](tasks/clean_tracked_changes.md) |
| Comments, replies, package validation | [Package tools](tasks/package_tools.md), [comments](tasks/comments_manage.md) |
| Tables and spreadsheet imports | [Tables](tasks/tables_spreadsheets.md); `scripts/table_geometry.py` for explicit cell/grid widths |
| Equations | [Equations](tasks/equations.md) |
| Fields, captions, navigation | [Fields](tasks/fields_update.md), [captions](tasks/captions_crossrefs.md), [TOC](tasks/toc_workflow.md) |
| Forms, sections, templates | [Content controls](tasks/forms_content_controls.md), [sections](tasks/sections_layout.md), [style packs](tasks/templates_style_packs.md) |
| Privacy, redaction, accessibility | [Metadata](tasks/privacy_scrub_metadata.md), [redaction](tasks/redaction_anonymization.md), [accessibility](tasks/accessibility_a11y.md) |
| Comparison, assembly, troubleshooting | [Diffing](tasks/compare_diff.md), [merging](tasks/multi_doc_merge.md), [LibreOffice](troubleshooting/libreoffice_headless.md) |

Read only the relevant guide. Specialized audits and transformations are optional operations, not automatic finalization steps.

## Author and preserve

1. Inspect the input's sections, styles, runs, tables, fields, comments, revisions, images, and links before editing. Keep the original and preserve unaffected parts.
2. Write for the intended reader, with a clear purpose and supported claims. Use semantic title/heading styles and deliberate spacing. Match the supplied template before introducing a new design.
3. Use `python-docx` for supported content and targeted OOXML patches for revisions, comments, and fields. Avoid replacing whole paragraphs when that would discard run formatting or anchors.
4. Keep tables readable: widths fit the page, padding is consistent, rows can grow, headers repeat where needed, and captions stay with their objects. Measure images and text rather than forcing fixed heights.
5. Preserve editable equations when requested; an equation image is a disclosed fallback, not native math. Do not accept revisions, remove comments, flatten fields, scrub metadata, or alter protection unless that operation is requested.

## Verify and deliver

```sh
python render_docx.py /absolute/input.docx --output_dir /absolute/review
python scripts/a11y_audit.py /absolute/input.docx --out_json /absolute/a11y.json
```

Render after meaningful layout edits and inspect every final page for clipping, overlap, broken glyphs, spacing, tables, and headers/footers. Re-render changed output after fixes. [Render verification](tasks/verify_render.md) explains expected artifacts; `--emit_pdf` retains a PDF when useful.

Rendering does not prove comments are preserved. Check their parts, anchors, relationships, and content types structurally, and verify revision counts/intent separately. Reopen the final file and confirm requested content, page count, links, and fields. Deliver the DOCX and any requested secondary outputs; keep internal QA images separate.

Example: “Revise the supplied proposal with tracked replacements and a comment on the missing deadline.” Preserve its template, mark only the requested replacement, keep the deadline unresolved, inspect revision/comment XML, and render all pages. Do not substitute a clean copy for requested redlines.
