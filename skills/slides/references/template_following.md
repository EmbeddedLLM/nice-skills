# Preserve and adapt a presentation

The approved presentation, design-system and format-capability guidance listed in [SOURCES.md](../SOURCES.md) is the basis for this workflow. Use it when an existing file supplies the content, visual rules, or editable structure for a deliverable.

## Establish the preservation contract

Determine which parts of the supplied material are authoritative. A deck might provide facts for a new narrative, reusable slides for a quarterly update, or a brand system that must survive editing. Ask about an unresolved distinction only when it changes what you will deliver. Keep a working copy and record the required slide count, aspect ratio, audience, protected text, data, logos and notices.

Record editing requirements individually: selectable text, native tables, chart-data changes, reusable layouts and theme switching. Matching a screenshot cannot establish these capabilities. If only a PDF or image is available, explain that reconstruction cannot recover its original Office relationships. Obtain the editable source when preserving those relationships is essential.

## Inspect appearance and structure together

Render the source into a contact sheet and inspect representative slides at full size, including crowded charts and non-Latin text. Inventory every slide before a whole-deck redesign. Capture the actual colours, font roles, margins, recurring positions, crop treatment and content hierarchy. Verify font availability in the production environment and document substitutions.

Inspect slide-to-layout and layout-to-master relationships, placeholders, theme parts, speaker notes, embedded workbooks and media. `python-pptx` can inspect many of these objects; package XML supplies the relationships it does not expose. Identify which styling is inherited, which is a local override, and which is baked into images. A theme file alone does not show that visible objects use it.

## Choose the smallest editing operation

Use the original package when the task requires its masters or editable objects. Replace text in the appropriate runs or placeholders, update actual table cells, and keep chart series and embedded workbook values synchronized. Duplicate only layouts needed for the new content. Independently editable chart copies need independent data dependencies; merely cloning slide XML can leave them shared.

Scope a change to the slide unless all consumers of a layout or master should change. Retain required footers and notices. Remove sample content and unused placeholders deliberately without deleting protected brand elements. Do not build a fresh deck with matching RGB values and describe it as preserving the source master. PptxGenJS builds new decks; it does not import supplied PPTX files.

For a new visual direction, assign semantic colour roles, a short type scale and consistent spacing before applying decoration. Choose layouts by the reasoning task: comparisons, evidence, sequence or recommendation. Preserve factual qualifiers and units when rewriting. If content overflows, change composition or split it when the brief permits; reducing text until unreadable is not a fit.

## Verify the required capabilities

Compare the final deck with the source for text, figures, order, notes and required objects. Render all final slides and inspect clipping, glyphs, crops, contrast, chart labels and connector positions. A shared-layout edit requires reviewing every affected slide. Re-render after fixes.

Inspect package relationships after saving. On a copy, test representative text, table and chart-data edits in the receiving application when available. If theme switching matters, test an actual theme change and inspect local RGB overrides, charts and image assets separately. A render checks appearance; it cannot prove that a chart's data can be edited.

Deliver the editable file plus requested previews. Identify reconstructed or rasterized elements, font substitutions and any checks that could not be run. Keep the original available for comparison; remove drafts only when authorized.
