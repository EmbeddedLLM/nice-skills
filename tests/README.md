# Skill script contract tests

Adapted from [jiahuei/agent-skills PR #8](https://github.com/jiahuei/agent-skills/pull/8), at commit [`21a311b7768c03d2d7a8bfd0c2ddfdc4c232346a`](https://github.com/jiahuei/agent-skills/commit/21a311b7768c03d2d7a8bfd0c2ddfdc4c232346a). The suites run real helpers against synthetic temporary fixtures, checking exit codes, report shapes, output contents, preservation, and failure paths. They do not use external accounts or paid APIs.

The CI workflow runs on pull requests targeting `main`, pushes to `main`, and `v*` tags. Formatting runs separately in [lint.yml](../.github/workflows/lint.yml) on every push. A separate media job executes real Chromium capture and FFmpeg encoding; missing prerequisites fail that job instead of skipping its tests.

Additional case ideas and selected archived helpers come from the [local](https://github.com/jiahuei/agent-skills/blob/235e920a4e494b74b46af67f813167699257c039/.github/workflows/local-skills.yml) and [media](https://github.com/jiahuei/agent-skills/blob/235e920a4e494b74b46af67f813167699257c039/.github/workflows/media-skills.yml) workflows reviewed at revision `235e920a4e494b74b46af67f813167699257c039`. Tests target this repository's interfaces and synthetic fixtures. The archive's golden outputs, unrelated engines, paid adapters, and absent skill paths were not imported. Presenter provider-ledger tests are retained with source attribution and remain mock-only.

## Run locally

Use Python 3.12 and Node.js 24, as in [CI](../.github/workflows/ci.yml):

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r tests/requirements.txt
npm ci --prefix skills/pdf/js --no-audit --no-fund
npm ci --prefix skills/slides/pptxgenjs_helpers --no-audit --no-fund
python -m unittest discover -s tests -p 'test_*.py' -v
python -m unittest discover -s tools -p 'test_*.py' -v
python skills/skill-creator/scripts/test_quick_validate.py
python skills/pdf/scripts/test_interpreter.py
python skills/create-motion-videos/scripts/test_prepare_runtime.py
python skills/presenter-video/tests/test_provider_job.py
```

Install Poppler (`pdftoppm`, `pdftotext`, `pdfinfo`, `pdffonts`) for PDF tests. CI also installs LibreOffice Writer, Impress, and Calc, DejaVu fonts, FFmpeg/ffprobe, and jq. Its Ubuntu 24.04 jobs install the distribution FFmpeg/jq and fail fast when they are older than the asserted minimums (FFmpeg 6.1, jq 1.7); raise those minimums deliberately with their runtime checks. The Python lock includes the document, PDF, slide, and font libraries needed for collection. Missing optional tools (LibreOffice, Pandoc, Playwright, or slide Node peers) skip their dependent cases; required Python imports and Poppler must be installed. Browser capture also needs a matching Playwright Chromium installation if Playwright is installed. LaTeX and OCR tests exercise argument/dependency checks without requiring their full toolchains. Server lifecycle tests require POSIX process groups and permission to bind loopback sockets.

`requirements.in` takes direct pins from the skill manifests. `requirements.txt` locks the resolved Python environment; the existing skill package lockfiles supply Node dependencies, avoiding a duplicate test-only Node package. Regenerate the Python lock intentionally with `uv pip compile --python-version 3.12 tests/requirements.in -o tests/requirements.txt` (generated using uv 0.12.7). `SKILL_NODE_MODULES` can point to an alternative directory containing all slide helper peers.

To run one case:

```sh
PYTHONPATH=tests python -m unittest test_pdf_skill_scripts.PreflightTests -v
```

## Coverage

| Suite | Scope |
| --- | --- |
| `test_documents_skill_scripts.py` | Consolidated Word toolkit: edits, comments, revisions, fields, tables, audits, OOXML validators, and rendering |
| `test_pdf_skill_scripts.py` | Inspect/extract/edit/redact, preflight, forms, rendering/comparison, batch and conversion helpers, Node form/extraction tools, smoke flows |
| `test_slides_skill_scripts.py` | OPC safety, slide edits and validators, LibreOffice process handling, thumbnails, nine PptxGenJS helper modules |
| `test_vector_art_scripts.py` | SVG parsing, style routing/extension, conversion, optimization, pixel art, text outlines, render CLI |
| `test_utility_skill_scripts.py` | Skill scaffolding/validation, metadata for every published skill, GIF easing, seeded Canvas art, page inspection |
| `test_portable_skill_scripts.py` | Local frontend export, themes, spreadsheet caches/recalculation, GIF composition/timing, motion wrappers and asset integrity, server argument checks |
| `test_server_lifecycle.py` | Multiple servers, noisy logs, occupied ports, failed startup, signal handling, and descendant cleanup |
| `test_explainer_skill.py` | Explicit paid opt-in, supplied narration, caption timing, real still-scene video, and invalid-input/output preservation |
| `test_presenter_skill.py` | Standalone supplied-footage editing/delivery without credentials, finalizer failures and concurrent output preservation, synthetic optional-generation job progression |
| `test_presenter_segments.py` | Finite timing inputs, overlapping spans, feasible pause segmentation, and supported generation routes |
| `test_media_skill_packaging.py` | Independent bundled links and retained Lanshu notices in both archive adaptations |
| `test_skill_script_inventory.py` | Explicit script ownership, pinned vendored boundary, test syntax and CI discovery |
| `test_skill_provenance.py` | Retained notice hashes, pinned source records, replacement scope, and portable links in the adapted research/office guides |

Skill-local regressions cover PDF interpreter propagation, skill metadata edge cases, motion runtime copying/reuse, and bounded provider-job recovery using mocks. `script_inventory.json` assigns every maintained script to a suite, including imported package initializers. It records test ownership rather than branch or line coverage. A newly added helper must have a corresponding test and inventory entry.

The portable suite also checks actual recalculated spreadsheet values, formula errors versus literal text, legitimate empty-string caches, macro/external-link rejection, and a motion skill copied outside the repository. The new media skills keep local production usable without provider credentials. Tests use synthetic tones and images, not real likenesses or generated speech.

## Homepage verification

The homepage packaging suite runs in normal test discovery and in the Pages build:

```sh
python -m unittest discover -s tests -p 'test_*site*.py' -v
```

The suites check complete catalog coverage, theme choices, repository links, local assets, repeatable builds, production and multiple-preview snapshots, updates and closure cleanup, fork filtering, API pagination, idempotent bot comments, exact commit links, invalid inputs, and the workflow permission boundaries. Synthetic Git repositories include untrusted Python and symlink inputs to verify that previews use only the trusted builder and never publish unrelated files. API calls are mocked; no tests publish Pages or post real comments. The media job also builds the site and runs the homepage browser checks using its existing pinned Playwright Core and Chromium:

```sh
python tools/build_site.py
node --test tests/media/site.test.cjs
SITE_PATH=/nice-skills/pr-preview/5/ node --test tests/media/site.test.cjs
```

The browser suite checks all 51 theme choices, saved and invalid preferences, blocked storage, combined search/category filtering, empty-state reset, requirements disclosure, keyboard access, JavaScript-disabled reading, and overflow at 1440, 768, 390, and 320 pixels. It serves the site under repository and nested preview URL prefixes (`SITE_PATH` selects the base path). Set `SITE_SCREENSHOTS` to a local output directory to retain full-page screenshots. Localhost binding and a working Chromium installation are required; these checks do not deploy to GitHub Pages.

## Browser and video integration

The `Local motion rendering` job uses Node 24, the single-dependency [media package lock](media/package-lock.json), Playwright Core 1.63.0 and its matching Chromium revision, and the minimum-version FFmpeg asserted above. It runs independently from the office tests, without API credentials or remote scene assets:

```sh
npm ci --prefix tests/media --no-audit --no-fund
node tests/media/node_modules/playwright-core/cli.js install --with-deps chromium
python -m unittest discover -s tests/media -p 'test_*.py' -v
```

Browser installation needs network/system-package permissions. Test execution uses only local synthetic scenes. It verifies asynchronous drawing and readiness, forward/reverse/fresh-context repeatability, stateful-scene rejection, complete MP4 decoding, dimensions/FPS/duration, silent output, temporal sample grouping, and preservation/cleanup after browser, asset, network-policy, encoder, or cancellation failures. The tiny fixtures keep runtime bounded. Python test code uses only the standard library.

`tests/media/` deliberately has no `__init__.py`: normal discovery does not launch browser tests or silently skip them. CI explicitly discovers this directory and the inventory test checks that invocation exists. These tests establish technical behavior, not the quality of every bundled demo or the visual quality of a production film. Full agent production, human playback/listening, and live paid pilots remain separate, explicitly reported activities.

The only excluded script tree is `skills/create-motion-videos/assets/lemo/`: pinned upstream source and demos. The motion suite verifies its manifest hashes and catalog integrity; it does not execute every upstream demo or prove rendered-film quality. Browser/agent execution and visual review remain separate from helper contracts.

Tests write generated artifacts to temporary directories. Registry mutations run against a copied skill. CI checks tracked skill files after the tests; a developer's existing edits are permitted locally.

## Changes from the source tests

- Run Word tests once against `documents`; this repo consolidated `docx` and `documents`. Remap `pdfs` to `pdf`, and the seeded generator from `templates/` to `assets/`.
- Omit tests for absent plugin-creator, skill-installer, library, imagegen, visualize, openai-docs, motion-video, explainer-video, and presenter-video packages. Test the local replacements where they exist rather than introducing those upstream implementations.
- Adapt validator library calls to this repo's `PackageValidator.check_*` API and literal slide-error patterns. Remove the nonexistent `part_text` helper assertion. Preserve rejection, whitespace, report, and archive-preservation checks.
- Update stale CLI wording assertions to this repo's diagnostics. An unfinished skill scaffold must fail validation, and names must match their directory; no OpenAI-specific UI file is generated here.
- Fix an invalid LibreOffice fixture that called `save()` on a paragraph instead of its document. Preserve this repo's documented JPEG thumbnails and existing six-column clamping behavior; exercise column validation without an external renderer so missing LibreOffice cannot mask the result.
- Replace the source inventory's substring matching with explicit script ownership. The original `unittest --list` check used an unsupported option, and a clean-tree assertion could reject legitimate developer edits without detecting writes during a suite; CI now checks for changes after execution.
- Retain the real LibreOffice conversion assertion that exposed invalid `--outdir=PATH` syntax. The converter now passes `--outdir` and its directory separately, with a local executable fixture covering paths containing spaces.
- Retain the encrypted-PDF assertion that exposed a real preflight defect. Add regressions for wrong and empty passwords, and strengthen the authenticated-file checks. The helper now records encryption and authenticates before reading protected content.

Formatting and these contracts do not establish that a skill works end to end in an agent. Report the actual environment and skipped paths with each change.

## Optional reference-corpus audit

CI runs the synthetic tests under `tools/`. The audit commands require an explicitly supplied local reference corpus; no corpus is bundled or fetched by CI:

```sh
python tools/check_remediation.py --corpus /path/to/reference-corpus
python tools/measure_similarity.py --corpus /path/to/reference-corpus --by-skill
```

The scoped checker uses byte comparison, ungated difflib, and shingle passes. [remediation.json](../tools/remediation.json) identifies the 62 upstream replacements and their new supporting helper. The default thresholds are difflib 0.35 or shingle containment 0.30. Missing files, an ineffective corpus, invalid thresholds, or an unreviewed match fail the check.

The small `safeOuterShadow` option factory has a reviewed compatibility match for its preserved API defaults and native option keys. The checker reports it, verifies its exact content hash, and requires a new review after any change. Do not add filler or unnecessary machinery just to lower a score. Similarity measures cannot establish license rights or authorship.

The two attributed Apache-2.0 skill-creator helpers are outside this replacement scope. The scoped check must not be described as a clean audit of the entire repository. Keep local audit reports outside the published skill directories. Manual agent exercises and target-application visual checks are separate from deterministic CI.

## Source-adaptation regression coverage

`test_source_adaptations.py` checks all 48 Hallmark token exports and notices, offline UI retrieval/data validation (including six upstream semantic suites run in an isolated subprocess from `tests/design_research/`), and raster-deck placement, notes, counts, and failure preservation. `test_browser_gif.py` runs real FFmpeg/ffprobe against synthetic videos/screenshots, including output preservation after a rejected size budget. `test_sound_design.py` renders every one of the 237 bundled presets and checks deterministic seeds, cue alignment, decoded WAV shape, clipping, and invalid-input preservation. NumPy/SciPy/Numba pins are included in the existing test lock; JIT disk caching is disabled.

The seven `test_game_*.py` suites adapt Apache-2.0 upstream synthetic regressions for all nine game helpers (see `skills/game-development/SOURCES.md`). They check static project/layout contracts, asset reports/preview sheets, generated Ebitengine project files, and macOS packaging failure preservation without downloading an engine, launching a game, signing, or publishing. They do not prove engine/runtime compatibility or gameplay quality.

All are discovered by the existing top-level CI command. The Markdown link check ignores fenced/inline code so language indexing expressions are not mistaken for documentation links. No agent behavioral or visual-quality pass is implied by these tests.

`test_material_catalogues.py` verifies the per-skill external-material indexes, portable paths, source-field conventions, and named collection membership against the existing data. It preserves all existing runtime catalogues and provenance manifests.
