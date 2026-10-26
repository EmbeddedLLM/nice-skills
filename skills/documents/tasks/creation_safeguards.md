# Creation and editing safeguards

Paths below are relative to this skill directory, not a fixed container installation path. The guidance here is written for this package's own tools; `python-docx` remains the ordinary creation path.

## Pick the operation before the library

| Task | Local route |
| --- | --- |
| Create a document | Use the existing [python-docx workflow](create_edit.md); `docx` on npm is an alternative for a JavaScript project. |
| Edit a supplied document/template | Preserve its styles, sections, relationships, and unaffected XML. Use run-level edits or the existing OOXML helpers for unsupported features. |
| Extract content | Use an available DOCX reader or Pandoc; text extraction cannot establish visual fidelity. |
| Redline or comment | Use the existing [tracked-change](../ooxml/tracked_changes.md) and [comment](../ooxml/comments.md) helpers, followed by structural and visual checks. |

The npm `docx` package authors new documents; it is not an existing-document editing API. Convert legacy `.doc` files using LibreOffice when needed, preserving the source. For `.dotx` templates, retain template content types and extension unless the requested output is a normal `.docx`.

## JavaScript creation details

Check the project's installed `docx` version and API before using these options. Do not assume dependencies are preinstalled.

- Set page dimensions and margins explicitly. DOCX page dimensions use DXA/twips: 1 inch = 1440. Letter portrait is 12240 × 15840; test how the installed library handles landscape to avoid swapping twice.
- Set both table column widths and corresponding cell widths in DXA; make their sums consistent with the intended table width and available page area.
- Use semantic numbering/bullets and built-in heading levels. A heading's appearance alone does not put it in the outline or table of contents.
- Use separate paragraphs for paragraph breaks and put a page-break element inside a paragraph. Use tabs with alignment/leaders for aligned labels rather than repeated spaces or punctuation.
- Set an explicit supported image type. Check image dimensions and aspect ratio.
- Use clear cell shading for background fills, not an unintended solid foreground pattern. Use paragraph borders for horizontal rules rather than empty layout tables.

## Preserve existing document structure

Work on a new output file. Text visible as one phrase can span multiple runs, hyperlinks, fields, or revisions. Identify the actual run boundaries before replacing text; merge runs only when their formatting and semantics permit it. Assigning whole-paragraph text can discard formatting and inline content.

When editing package XML, use a parser that preserves namespace declarations and whitespace needed by OOXML. Keep unrelated ZIP members intact. If extracting, reject traversal, absolute paths, and symlink entries before writing them; removing unsafe files after extraction is too late. Repack into a fresh archive with `[Content_Types].xml` at its root, so deleted members cannot linger from an old output archive.

## Redlines and comments

Each requested tracked edit needs real insertion/deletion markup with unique IDs, author, and timestamp. Deletions use `w:delText`; ordinary `w:t` is not a tracked deletion. Enabling tracking in settings does not retroactively mark a direct XML replacement as a revision.

A deleted paragraph mark represents a join with the following paragraph. Accepting only deleted text can leave an empty paragraph or numbered bullet. Check both the revision markup and the accepted result; a converter's accepted view can differ from Word's interpretation. The existing accept/reject helper is not a complete Word revision engine.

Comments need content, relationships, content-type entries, and range/reference anchors in the body. Modern reply/resolution metadata adds further parts. Reuse the existing helpers for supported operations, and preserve unsupported metadata during unrelated edits. A comment entry without an anchor may exist in the ZIP but remain invisible.

Compare the original and edited text, inventory expected revisions/comments, and confirm that unrelated content survived. Render using `render_docx.py`, inspect the actual generated page filenames, and re-render after fixes. Passing XML parsing or text extraction is not a substitute for layout review.

For executable normalization, comments/replies, LibreOffice acceptance, and structural/redline checks, use the [package tools](package_tools.md).
