# PPTX creation and template editing

Paths are relative to this skill directory.

## Choose the workflow

Use PptxGenJS for new editable decks. For an existing deck or template, inventory its slide order, layouts, masters, fonts, media, charts, and notes before editing. Render a contact sheet to select actual template layouts; a text dump does not show their design. Preserve the input and save to a new output.

PptxGenJS does not import an existing deck for editing. Use targeted OOXML changes or python-pptx where it supports the required feature. For plain text substitutions, modify the appropriate runs rather than assigning `text_frame.text`, which can discard run formatting. Convert legacy `.ppt` separately; preserve `.potx` template type unless creating a normal presentation is intended.

## New decks: PptxGenJS details

Check the installed version's options and dimensions. Do not assume dependencies are preinstalled or extrapolate compatibility from one upstream runtime.

For the optional bundled `pptxgenjs_helpers`, copy that directory to a writable runtime and use its pinned `package.json`/lockfile with `npm ci`. Its text measurement uses skia-canvas for font shaping and linebreak for Unicode break opportunities; code highlighting uses Prism; equation rendering uses MathJax. Native canvas installation can require a platform-specific binary. Ordinary template editing with Python does not require this JavaScript tier.

- Set layout before adding slides; `LAYOUT_16x9` and `LAYOUT_WIDE` have different physical dimensions despite the same aspect ratio. Base all coordinates on the chosen dimensions.
- Pass six-digit RGB colors without `#`. Use the property-specific transparency/opacity option rather than eight-digit hex. Construct fresh nested option objects for each shape; libraries may mutate them.
- Keep shadow offsets nonnegative and choose direction with the angle. Use the supported `charSpacing` option rather than CSS `letterSpacing`.
- Use real bullet/paragraph options and intentional paragraph spacing. Set text margins explicitly when aligning text to graphics. Put speaker notes in the notes API, not on-slide text boxes.
- Prefer native charts when the requested chart has a PowerPoint-native representation. Supply data, units, labels, and palette deliberately. An image is appropriate for an unsupported visualization or when explicitly requested, but does not preserve editable chart data.
- For stacked bars/columns, use a supported internal data-label position; avoid `outEnd`. For combo charts with secondary axes, declare both category and value axis configurations with matching IDs. Validate the actual generated chart XML and compatibility, not only whether it renders in LibreOffice.
- Use a fresh presentation instance per output. Keep icons/media in a supported format with the required MIME prefix for data URIs, and verify aspect ratio and raster quality.

### Helper contracts and limits

`calcTextBox(size, {lines})` estimates height analytically. Supply `{text, w, fontFace}` to estimate wrapped height, or `{text, h, fontFace}` to find a fitting width. Geometry and padding are inches; font sizes, margins and paragraph spacing are points. Returned `margins` are inches. Arrays of runs are measured as separate paragraph entries, including their local size, weight, indentation and spacing; do not use that estimate as a model of multiple inline spans on a single line. Skia resolves installed fonts; a requested family name does not guarantee that font exists. Inspect actual glyphs after export.

`autoFontSize(text, fontFace, {w, h, minFontSize, maxFontSize})` searches the allowed size range. `mode: "shrink"` and `mode: "enlarge"` also require a reference `fontSize`. A minimum size is returned when no size in the interval fits; verify the resulting height and change the layout instead of assuming a fit guarantee. Per-run explicit sizes remain fixed during this search.

Layout helpers inspect PptxGenJS shape rectangles and crop viewports in inches. Alignment/distribution move only the selected objects. Overlap reports suppress containment by default; they cannot establish reading order or account for every rotation, group transform or transparent region. Review warnings against rendered slides. `sanitizeSvg` normalizes SVG for embedding, including namespace and relative-unit handling; it is not a security sanitizer for untrusted markup.

## Template editing and package integrity

Plan add/delete/reorder operations before changing individual slide content. Duplicating an already-edited slide duplicates that edited content. Slide order comes from `ppt/presentation.xml` and its relationships, not slide filenames.

Copying `slideN.xml` alone is insufficient: maintain slide IDs, presentation relationships, content types, layout/master links, notes, and slide relationships. A duplicated slide can still share chart, embedded-workbook, or SmartArt parts with the original. Clone and reconnect those parts when independently editable copies are required. The public python-pptx API does not provide a general slide-duplication operation.

Preserve namespace mappings and schema ordering during XML edits. Do not indiscriminately pretty-print or reorder package XML. Reject unsafe archive paths before extraction and rebuild a fresh ZIP rooted at `[Content_Types].xml`. Remove unreferenced parts only after the final relationship graph is known; never delete media merely because one slide no longer uses it.

Map the supplied content to template groups: if a four-person layout receives three people, remove the unused person's whole visual group, including photo, labels, and decoration. Use one paragraph per list item and preserve its paragraph/run properties and inherited bullets. Preserve significant whitespace in text nodes.

## Design and verification

Respect the actual brand/template and choose layout from the information: comparisons, a sequence, a diagram, or a key number. Use graphics when they explain the content; no mandatory decoration or image generation is needed. Keep a clear hierarchy and consistent spacing. Check font availability and leave room for fallback metrics; a LibreOffice preview is not proof of identical rendering in PowerPoint.

Render every slide and inspect overflow, clipping, alignment, contrast, leftover placeholders, and template decorations affected by text wrapping. Re-render after fixes. Compare against the input's structure and content to distinguish inherited issues from regressions.

Structural checks should include relationship targets, content types, slide IDs, chart axis references, and expected notes/media; the validators under `scripts/` cover them (see [package tools](package-tools.md)). Rendering with LibreOffice and opening with python-pptx do not certify complete PowerPoint compatibility, so never claim that either proves a chart is valid in PowerPoint.
