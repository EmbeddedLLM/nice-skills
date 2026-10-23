---
name: canvas-design
description: Compose static posters, covers, and graphic artwork for PNG or PDF delivery with deliberate typography and spatial hierarchy. Use for a fixed visual composition rather than editable SVG tooling, procedural exploration, or multipage documents.
license: Apache-2.0; see LICENSE.txt and SOURCES.md
---

# Canvas design

Create the requested composition using supplied images, local fonts, and drawing primitives. An image-generation API, paid stock library, or hosted design tool is not required.

## Compose and export

1. Establish required wording, canvas size, viewing context, background/transparency, and any print constraints. Preserve supplied brand and reference requirements.
2. Choose a focal point, reading order, margins, palette, and type hierarchy. Use negative space and alignment to organize supporting material. A text-heavy poster is valid when the content calls for it.
3. Draw with an available local tool such as Pillow, SVG/CairoSVG, or ReportLab. Use the project's installed versions or create a project-local environment with recorded versions. These tools are alternatives, not a required stack.
4. Measure text with the actual font and weight. Check glyph coverage, line wrapping, image aspect ratio, and intentional crops. Keep font/asset notices when redistributing them.
5. Export at the requested dimensions. Inspect the complete image and details at intended viewing size; rasterize a PDF for review. Correct clipping, weak hierarchy, poor contrast, and cramped spacing before adding decoration.

If a requested photograph or branded asset is missing, use a suitable supplied/licensed substitute only within the brief, or identify the missing input. Do not silently replace a required photograph with a generated one. Keep editable source or the generator available alongside the final deliverable when requested.

## Optional Openverse imagery

For a photographic or illustrative focal point, use the free anonymous [Openverse image API](https://api.openverse.org/v1/) through an available HTTP tool when network access is permitted. Example:

```text
GET https://api.openverse.org/v1/images/?q=botanical&license=cc0,pdm,by&page_size=5&mature=false
```

Use public subject terms and inspect warnings and actual candidates. Verify the creator, license, and notices at the original source page; [Openverse advises checking its metadata](https://docs.openverse.org/api/reference/made_with_ov.html). Keep the default license selection unless other restrictions fit the brief. Download selected originals locally and check resolution at the intended print/display size before cropping or composing. A stock image must not replace a specified logo or photograph without an appropriate change to the brief.

Deliver required credits with the artwork: title, creator, source URL, license/version/link, retained notices, and modifications. Use a readable credit line or an accompanying credits file that travels with the PNG/PDF; do not rely only on image metadata.

Respect host terms, rate limits, and retry guidance on 429; avoid catalog scraping. On unavailable access or unverifiable media, continue with suitable supplied assets or local drawing and state any missing requirement. No account or paid service is needed, and offline composition remains available.

Example: “Make an A4 workshop poster from this title, schedule, and logo.” Deliver a readable PDF with the exact schedule and undistorted logo, plus a PNG if requested. Check page dimensions and fonts; claim print bleed, embedded fonts, or color-profile compliance only if verified.
