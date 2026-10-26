# Sources and notices

## Upstream source

| Field | Value |
| --- | --- |
| Project | taste-skill (published as `design-taste-frontend`, "tasteskill v2") |
| Creator | Leonxlnx |
| Repository | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) |
| Exact snapshot | [`6010f91a9935f1c167dfc500fb1a475681892e6b`](https://github.com/Leonxlnx/taste-skill/tree/6010f91a9935f1c167dfc500fb1a475681892e6b) |
| Retrieved | 2026-10-22 |
| Upstream skill directory | `skills/taste-skill/` |
| Licence | MIT, copyright 2026 Leonxlnx; full text in [LICENSE.txt](LICENSE.txt) |

The `SKILL.md` run, the eleven `references/` guides, the five `scripts/` programs and their `scripts/lib/` modules, the `library/` data, the shared `assets/` foundation and stage, and `evals/evals.json` are upstream material, redistributed under its MIT notice. The inspiration, house rules and citations behind them are documented in [references/research.md](references/research.md).

## Local changes

- Added implementation guidance for YAGNI, reuse, approach validation, user buy-in for speculative robustness, and simplification while preserving the requested visual quality and existing stack.
- Renamed the skill to `design-taste` in the frontmatter so the name matches its directory.
- Added the `license` frontmatter field, [SOURCES.md](SOURCES.md), and this notice placement.
- Corrected three statements that described a scene library and `assets/scenes/demo/<id>.html` pages this snapshot does not contain. The shared stage is bundled; the draw deals no scroll scenes, and `references/scenes.md` §8 is the documented route when it deals none. Upstream already describes `library/scenes.json` as unreleased.
- Replaced the upstream installer instructions in `README.md` with a copy-the-folder note. The upstream `install.sh`, `.claude-plugin/`, `.codex-plugin/`, `.agents/` and `.github/` metadata target a plugin marketplace and were dropped; nothing in the run needs them.
- Bundled the four example screenshots in `examples/v2/` as design references, with the per-photograph credits and the CC BY-SA 4.0 legal code, and pointed `SKILL.md` at them. They are not MIT; see [NOTICE-examples.md](NOTICE-examples.md). Each file is pinned by hash in [examples/vendored-assets.json](examples/vendored-assets.json).

## Excluded material

- `assets/sponsors/`, `assets/taste-skill-wordmark*`, `assets/readme-*` — repository marketing images and third-party sponsor marks. They play no part in the workflow.
- `CHANGELOG.md`, `.gitattributes`, `.gitignore`, `.github/` — repository metadata.

## Included third-party media

`examples/v2/` holds four screenshots of pages this skill built, plus the upstream `CREDITS.md`, which credits 23 photographs and films. The screenshots crop and composite openly licensed photographs, so they are adaptations of them:

| Files | Licence |
| --- | --- |
| `examples/v2/coffee-storefront.webp`, `coffee-roast.webp`, `coffee-questions.webp`, `night-dates.webp` | CC BY-SA 4.0 — see [NOTICE-examples.md](NOTICE-examples.md) and [examples/v2/CREDITS.md](examples/v2/CREDITS.md) |
| `examples/v2/CREDITS.md` | upstream credits, reproduced unchanged |
| `examples/v2/LICENSE-CC-BY-SA-4.0.txt` | the canonical Creative Commons legal code, retrieved from creativecommons.org on 2026-10-22 |

The underlying photographs remain under their own licences (CC BY 2.0/3.0, CC BY-SA 2.0/3.0/4.0, CC0 or public domain) as listed per photograph. Nothing else in this skill changes licence: `SKILL.md`, `references/`, `scripts/`, `library/` and `assets/` stay MIT.

## Network, browser and asset access

- `scripts/inspect.mjs` and `scripts/scenes.mjs` drive a locally installed Chrome, Edge or Chromium over the DevTools protocol using Node's built-in WebSocket; nothing is installed and no account is used.
- `scripts/assets.mjs` queries Openverse, Wikimedia Commons, the Art Institute of Chicago, the Metropolitan Museum of Art, Internet Archive and NASA over their public APIs. No key or account is needed. Downloaded media keeps its own licence, and `--get` writes the credit record.
- `library/photos.json` stores Lorem Picsum references to Unsplash photographs, under the Unsplash licence. Only URLs are bundled, not image files.
- `library/sites.json` and `references/research.md` record observations, scores and measurements taken from public gallery sites; no site's code, imagery or fonts are bundled.
- Dealt type systems and the shared scroll-scene stage load fonts and (when a scene is built) GSAP/Lenis from pinned CDN URLs at page runtime. Every scene degrades to its finished composition when a CDN fails. Vendor those files locally for a fully offline page.

## Verification note

The upstream package passed its own tests and blind evaluations as documented in its `README.md` and `references/research.md`. This repository added the regression checks in `tests/test_design_taste_scripts.py`; they establish that the vendored scripts and library still behave as documented in this snapshot. They do not re-run the upstream blind evaluations, and no page was built or critiqued in an agent for this import.
