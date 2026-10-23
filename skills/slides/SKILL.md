---
name: slides
description: Create, inspect, and edit PowerPoint decks from narrative planning through editable PPTX delivery and visual validation. Use for slides, presentations, and supplied deck templates rather than standalone posters or generic theme selection.
license: See SOURCES.md and slide_templates/Template_Reuse_Permission.txt
---

# Presentations

Deliver an accurate, editable deck using local tools. Use supplied content, local shapes/SVG, licensed assets, and native charts; image generation by OpenAI or any other paid service is not required.

The office workflow uses the approved Design Office Artifacts reference, adapted for this package. [SOURCES.md](SOURCES.md) records the selected guidance, replacement scope, and retained notices.

## Select the starting point

For a read-only question, inspect the deck without changing it. For edits, preserve the input and its design unless redesign is requested. Read [template following](references/template_following.md) and [PowerPoint workflows](references/pptx-workflows.md) before changing an existing package.

For a new deck, use the user's template first or select from the six bundled categories in [template guide](references/templates.md). Preview the actual layouts and read slide notes. The supplied deck includes illustrative data that must be replaced; it is not evidence for the user's claims.

Python dependencies are in [requirements.txt](requirements.txt). Rendering needs LibreOffice Impress and Poppler. PptxGenJS is an alternative for new decks; use the destination project's pinned dependency and lockfile. It does not import an existing PPTX for editing. Resolve helper paths from this directory and keep the installed skill read-only.

## Plan and build

1. Establish audience, purpose, required slide count, format, and evidence. An N-slide request includes the cover unless stated otherwise; do not add a cover to a one-slide deliverable by habit.
2. Give each slide one purpose and arrange the story without repeated claims. Use concise subject titles or supported takeaways and plain, specific copy. Keep caveats, units, and comparison periods intact.
3. Choose layouts around the information: comparison, sequence, native table/chart, diagram, or image. Keep requested charts/tables/diagrams editable. Record citations in speaker notes and on-slide when the reader needs them.
4. Follow actual template typography and spacing. For new layouts, use a readable type hierarchy and consistent margins. Reduce unnecessary content or change layout before shrinking type. Use original logos with correct proportions.
5. Apply targeted run or OOXML edits for templates. Preserve slide order, relationships, notes, masters, layouts, embedded workbooks, and media. Duplicated charts can share data parts; clone their dependencies when independent editing is required.

Use [package tools](references/package-tools.md) for adding slides, cleanup, validation, and thumbnail generation. Cleanup and structural edits operate on copies and are not implicit permission to remove unrelated content.

## Optional Openverse imagery

When a slide needs external imagery, use the free anonymous [Openverse image API](https://api.openverse.org/v1/) with an available HTTP tool and permitted network access. Example request:

```text
GET https://api.openverse.org/v1/images/?q=forest&license=cc0,pdm,by&page_size=5&mature=false
```

Search public subject terms, inspect response warnings, and shortlist images that fit the slide's crop and resolution. Verify each license and creator at the returned source page (`foreign_landing_url`); [Openverse's metadata is not a license guarantee](https://docs.openverse.org/api/reference/made_with_ov.html). Keep the default license selection unless the brief supports other restrictions.

Download chosen originals to the project and embed them in the deck. Record title, creator, source URL, license/version/link, and changes in notes or an accompanying asset manifest; preserve required notices and ensure credits travel with PDF exports too. Use an appropriate credit slide or visible credit where needed. Stock images illustrate a claim; they do not establish its evidence or replace editable charts.

Respect rate limits and source-host terms; follow retry guidance on 429 without catalog scraping. If access fails or media cannot be verified, use suitable supplied imagery or local shapes and disclose any unmet asset requirement. No registration, paid service, or runtime API connection is required.

## Verify and deliver

```sh
python scripts/office/validate.py /absolute/final.pptx
python scripts/thumbnail.py /absolute/final.pptx /absolute/review/contact --cols 3
```

Inspect all final slides for clipping, overlap, font fallback, chart labels, remaining placeholders, and meaningful reading order. Check slide count/order, notes, data, and editability; re-render after fixes. Structural checks and LibreOffice rendering do not certify identical native PowerPoint behavior. State unavailable checks plainly.

Deliver the PPTX, requested PDF/previews, and useful editable source. Example: “Make a six-slide research briefing using the academic template.” Select six relevant layouts, replace sample evidence and chart data, preserve notes/citations, remove drafting-only slides, and verify exactly six delivered slides.
