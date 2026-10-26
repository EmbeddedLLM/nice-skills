---
name: vector-art
description: Create, edit, restyle, convert, and compare editable SVG illustrations, icons, and infographics, with structural validation and rendered previews. Use when vector geometry is the deliverable rather than a raster composition or video.
license: MIT; see LICENSE-buildfast.txt and references/sources.md
---

# Vector art

Deliver editable SVG and requested previews using local geometry and browser rendering. No raster-generation API or paid vector editor is required. Preserve an existing icon/logo system and user geometry during narrow edits.

## Construct

1. Establish subject, dimensions, use, source SVG, and visual constraints. Use `python scripts/route_style.py --list` or `--show <id>` to inspect the bundled 44-style library. A suggested style is advisory; the user's direction takes precedence.
2. Read only the chosen style in `styles/references/` plus [composition](reference/composition.md) as needed. Set viewBox, focal point, groups, palette, and typography before detail work.
3. Build semantic groups, reusable definitions, an accessible title, and editable geometry. Preserve source text or provide a separate outlined variant with font attribution. Embedding a bitmap is not vector reconstruction.
4. For comparable variants, freeze subject, pose, canvas, and anchor positions. Let a primary style govern geometry; secondary styles may supply color/material. Use [modes](reference/modes.md) and [SVG craft](reference/svg-craft.md) for conversions and blending.
5. Use real data for infographics and document the origin of reused assets. Never invent facts to fill the composition.

## Validate and render

[Backend setup](references/backend.md) and [requirements.txt](requirements.txt) describe the local Python/Chromium dependencies. Resolve commands from this skill directory:

```sh
python scripts/validate_svg.py /absolute/art.svg
python scripts/render_svg.py /absolute/art.svg -o /absolute/preview.png -w 1024 --analyze
```

Optimize a copy with `scripts/optimize_svg.py` when useful, then validate and render again. For variants, pass multiple SVG files and `--sheet /absolute/comparison.png`. Inspect silhouette, typography, contrast, clipping, and style; a parse check does not establish appearance. Keep original files before any in-place conversion.

Deliver SVGs, previews, attribution, and rendering limits. If fonts/browser support are missing, preserve editable source and state the unverified parts rather than claiming visual success.

Example: “Create three editable blueprint-style icons with the same grid.” Use common anchors and stroke rules, validate all three, render a comparison, and check their apparent size and alignment.
