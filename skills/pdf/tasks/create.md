# Design a new PDF deliverable

Start with its audience, reading task, content sources, page size and editing requirements. Ask about missing decisions that affect the result, such as a print specification or whether an editable companion is needed. Do not make source-format choices merely because a converter is available.

For a prose report, organize sections around findings and their supporting evidence. Put units, dates, definitions and source references close to figures. Use typography and spacing to distinguish headings, body text and captions. Choose graphics for their explanatory purpose: bars for category comparisons, lines for change over time, tables for exact lookup, diagrams for relationships. Keep node meanings and connector labels consistent. Read labels at final size.

Select an authoring route that fits these needs:

- ReportLab Platypus handles flowing paragraphs/tables; canvas is appropriate for fixed placements such as labels and certificates. Core requirements pin it.
- Native office source is useful when collaborators need editable paragraphs, tables or slides. Preserve that source and export PDF as a separate artifact.
- HTML supports browser layout; add deliberate print rules and verify pagination.
- TeX suits mathematical typesetting and cross-references when its toolchain is available. Markdown requires a chosen export engine and styling source.

The [conversion guide](convert.md) documents commands and prerequisites. No sibling skill or unpublished template is required. Use assets with appropriate redistribution rights; preserve their notices when bundling them.

Build a representative page containing the longest heading, dense table and smallest diagram labels. Export and inspect it before completing the document. Then review a montage for pacing and every page at reading scale for clipping, widows, bad table breaks, image quality, missing glyphs and unexpected blanks. Check searchable text, links, page numbering and any requested accessibility features separately. Rendering alone cannot establish tagging or reading order.

Deliver the final PDF and any requested editable source. Report generation and verification tools used, and limitations such as an unavailable print/viewer test. Keep review artifacts until the user no longer needs them; do not delete their working files as an automatic finishing step.
