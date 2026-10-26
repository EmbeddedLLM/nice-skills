---
name: theme-factory
description: Select, preview, customise and apply cohesive colour themes to websites, dashboards, reports and slide decks. Use for palette selection, primary-button colour improvements, theme comparisons, CSS design tokens, PowerPoint colour schemes and HTML theme guides. Includes 50 Color Hunt/Coolors-inspired themes across ten moods plus the user's exact Lavender palette, source snapshots, contrast checks and offline exports.
---

# Theme Factory

Create a coherent applied theme, with special attention to the primary button. The bundled guide and Python standard-library CLI work offline without a paid palette service, provider API, or sibling skill.

Optional web material direction: browse 48 attributed [Hallmark recipes](references/hallmark/cobalt.md) with `python scripts/hallmark.py list --query "technical"`, inspect one with `show cobalt`, or export its tokens with `css cobalt --output new-tokens.css`. Export refuses an existing CSS file and writes the retained license beside it. These recipes are separate from the 51 existing cross-format palettes; fonts are names/fallbacks, not downloaded assets. Inspect actual text/background pairs in the destination browser. See [SOURCES.md](SOURCES.md).

## Choose and apply

1. Identify the destination, visual mood and any locked brand colours from the request. Proceed with a reasonable choice when context suffices; do not require a questionnaire.
2. Use the commands below to inspect the matching mood. Select for visual fit, not likes alone. Read [selection.md](references/selection.md) for the mood map and button guidance.
3. Show the selected colours in context using the bundled HTML guide or the actual artifact. Keep website and slide comparisons on the same layout. For a shortlist, show three to five genuinely distinct choices, their primary buttons and exact HEX values.
4. Export the selected theme and apply it using the destination artifact's local authoring tools. A CSS file or Office XML alone does not complete a requested website or slide deck. No particular hosting platform or artifact skill is required.
5. Check actual text/background and control pairs after any changes. Render and inspect normal, hover, focus and selected states. For decks, inspect the rendered slides and chart labels. Fix defects before delivery.
6. Save user-facing deliverables with the environment's supported persistence workflow. Preserve an existing artifact's identity when updating it. Report the applied choice and meaningful checks concisely.

Resolve `ROOT` below to the directory containing this SKILL.md; do not use a literal placeholder in commands. The Python script uses only the standard library and works from any current directory.

```bash
python3 ROOT/scripts/themes.py list
python3 ROOT/scripts/themes.py list --mood natural
python3 ROOT/scripts/themes.py show 'Olive Garden'
python3 ROOT/scripts/themes.py show USR-01
python3 ROOT/scripts/themes.py export NAT-01 --format both --out /absolute/output/olive
python3 ROOT/scripts/themes.py export Lavender --format both --out /absolute/output/lavender
python3 ROOT/scripts/themes.py export --all --format both --out /absolute/output/themes
python3 ROOT/scripts/themes.py guide --out /absolute/output/theme-guide.html
python3 ROOT/scripts/themes.py contrast '#FFFFFF' '#606C38'
python3 ROOT/scripts/themes.py verify
```

`list` accepts `--json`; `show` returns the complete selected record. `export` supports `web`, `office`, `both` and `json`. Every export includes its record and source notice. Existing identical files are reused; differing files require intentional `--overwrite`. `--all` includes all 51 themes.

## Keep the palette and its application distinct

- Use `source_colors` for the exact observed reference swatches. Use `colors` and `web.tokens` for the curated application. Added neutrals and shades are adaptations, not source values.
- Preserve all nine Lavender values and original roles. Its primary **accent** is lavender, while its primary **button** is ink. Respect `action` and `on-action` overrides in web exports and use their hover overrides. Do not silently replace Lavender with Coolors' Soft Lavender.
- For the original cross-format palettes, use the bundled guide as the single data source. The CLI extracts both JSON script blocks from it; do not create a second manifest that can drift. Read only selected records, not the full HTML or all tokens, into model context.
- Do not assume a good-looking swatch set guarantees usable interface colours. Give the page a quiet canvas, a readable ink colour, one clear primary action and softer supporting accents.
- Read [application.md](references/application.md) for CSS wiring, Office slots, custom themes and validation limits.

## Refresh or customise when requested

Preserve the user's stated constraints. For new colours, work on a copy of the selected record, recompute all dependent tokens and Office slots, then validate the actual result. If updating this skill, update the guide's JSON and any affected presentation text together; run `verify` and inspect its interactive previews. Do not edit source swatches to disguise an adaptation.

Research current popularity only when requested. Browse the named source pages, record the observation date, exact colours, displayed likes and ranking scope. State access limitations rather than inventing ranks. Read [SOURCES.md](SOURCES.md) before making source or reuse claims. The bundled counts are a dated snapshot, not an exhaustive ranking or live data.

## Scope

This skill supplies colour decisions, applied roles, previews and exports. Preserve existing typography, or assign available heading/body fonts and a consistent type scale when a reusable theme needs them. Record substitutions, check language coverage, and re-render after font changes because wrapping can shift. Layout and imagery follow the artifact's purpose. No third-party font files, presentation masters or full UI templates are supplied. Do not claim the community references are MIT/Apache-licensed or certified royalty-free assets.

Example: “Apply Lavender to this offline dashboard while preserving its typefaces.” Export the exact Lavender record, wire semantic tokens including its ink primary button, and inspect normal/hover/focus states. An unknown theme name or conflicting output file should be resolved explicitly; do not silently replace it with another palette or overwrite the user's work.
