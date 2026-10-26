# Sources and provenance

## Repository adaptation

Imported from the user-supplied reference package without changing the 1,882-file pinned upstream asset tree. The repository adaptation adds provider-independent prerequisites, legacy production-mode guidance, and pinned Python installation tiers outside that tree. It excludes online TTS from the default installer. Original retrieval dates below are preserved and were not re-verified against the network during this migration.

**Original reference retrieval: 2026-10-20. Asset/font repair: 2026-10-21 (Asia/Kuala_Lumpur).**

This file records the sources used to build Motion Video Studio (`create-motion-videos`), the date they were fetched or consulted, and how their material is used. Retrieval dates below describe this research and packaging work; publication dates describe the original posts. Publication dates are in UTC. The original sources below were retrieved on 20 October 2026. The separately documented font sources were retrieved on 21 October 2026 in Asia/Kuala_Lumpur.

## 1. Lemo-Opuscar: primary source collection

| Field | Value |
| --- | --- |
| Project | Lemo-Opuscar |
| Creator | LemoLab / Lemomo; upstream credits LemoLab × Claude Opus 5.5 |
| Repository | [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) |
| Exact snapshot | [`b5e8ef93930b6d828f352055a689320f138237b1`](https://github.com/lemomo-ai/lemo-opuscar/tree/b5e8ef93930b6d828f352055a689320f138237b1) |
| Retrieved | **2026-10-20** |
| Local source | [assets/lemo/](assets/lemo/) |
| Included inventory | **1,882 bundled files**: 1,625 unchanged upstream files, 75 patched upstream files and 182 added font/licence files, individually identified and hashed in [upstream-manifest.json](references/upstream-manifest.json) |
| Main collection | **51 style guides** and their published source packages; `_template` is not counted as a style |
| Separate reference collection | **98 OPUSCAR cinematic references**, each with English and Chinese reusable prompts; these are separate from the 51 main styles |

### Source map

All rows in this table were fetched as part of the same pinned repository snapshot on **2026-10-20**.

| Source | Use in this skill | Bundled location |
| --- | --- | --- |
| [Upstream README](https://github.com/lemomo-ai/lemo-opuscar/blob/b5e8ef93930b6d828f352055a689320f138237b1/README.md) | Collection overview, production approach and upstream licence distinctions | [README.md](assets/lemo/README.md) |
| [All main style packages](https://github.com/lemomo-ai/lemo-opuscar/tree/b5e8ef93930b6d828f352055a689320f138237b1/styles) | Style constraints, metadata, demos, drawing engines and production examples | [styles/](assets/lemo/styles/); use the [complete style index](references/style-index.md) for individual guides |
| [OPUSCAR 98 prompt collection](https://github.com/lemomo-ai/lemo-opuscar/blob/b5e8ef93930b6d828f352055a689320f138237b1/styleboard/opuscar98_styles.json) | Bilingual cinematic reference prompts and renderer hints | [opuscar98_styles.json](assets/lemo/styleboard/opuscar98_styles.json) and the [reference index](references/opuscar98-index.md) |
| [DIRECTOR.md](https://github.com/lemomo-ai/lemo-opuscar/blob/b5e8ef93930b6d828f352055a689320f138237b1/DIRECTOR.md) | Story, treatment, shot planning and direction | [DIRECTOR.md](assets/lemo/DIRECTOR.md) |
| [TECHNIQUE.md](https://github.com/lemomo-ai/lemo-opuscar/blob/b5e8ef93930b6d828f352055a689320f138237b1/TECHNIQUE.md) | Rendering, motion, sound and production techniques | [TECHNIQUE.md](assets/lemo/TECHNIQUE.md) |
| [Shared core tools](https://github.com/lemomo-ai/lemo-opuscar/tree/b5e8ef93930b6d828f352055a689320f138237b1/core) | Local serving/capture, audio, speech, fonts and shared utilities | [core/](assets/lemo/core/), documented in [core/README.md](assets/lemo/core/README.md) |
| [Dependency manifests](https://github.com/lemomo-ai/lemo-opuscar/tree/b5e8ef93930b6d828f352055a689320f138237b1) | Reproducible local runtime setup | [package.json](assets/lemo/package.json), [package-lock.json](assets/lemo/package-lock.json), [requirements.txt](assets/lemo/requirements.txt), [requirements-voice.txt](assets/lemo/requirements-voice.txt), [requirements-music.txt](assets/lemo/requirements-music.txt) |
| [Upstream MIT licence](https://github.com/lemomo-ai/lemo-opuscar/blob/b5e8ef93930b6d828f352055a689320f138237b1/LICENSE) | Original code/documentation copyright and permission notice | [LICENSE](assets/lemo/LICENSE) |

The [machine catalogue](references/catalogue.json) records individual style IDs, source URLs and guide paths. The manifest records the exact included files and **321 omitted reference-media files**, plus a complete list of all **399 excluded upstream tracked files**. Some generated voices and other production assets are absent from the upstream repository. Missing production font binaries have now been supplied from the sources below. Source availability does not establish that every demonstration can render without preparing its media and dependencies.

## 2. Twoclipping: original public demonstrations

Creator: **zero / @twoclipping**. These sources informed the added `twoclipping:ui-morph` and `twoclipping:product-launch` variants.

| Source | Published (UTC) | Retrieved | Contribution |
| --- | --- | --- | --- |
| [UI morph loop](https://x.com/twoclipping/status/2103273003555402193) | 2026-09-24 | **2026-10-20** | Persistent UI component identity, timestamp-controlled properties, analytical springs and sampled export |
| [Product launch film](https://x.com/twoclipping/status/2103835273813496100) | 2026-09-26 | **2026-10-20** | Interface and image transitions, asynchronous seeking, glass treatments and export checks |
| [Earlier code, footage and music example](https://x.com/twoclipping/status/2102554209166000267) | 2026-09-23 | **2026-10-20** | Integration of real footage and audio with code-driven product motion |

The original post metadata and available text/media were consulted through public X pages, indexed text and X's public syndication responses. Some long-post embed text was truncated. The [API Models motion-graphics prompt archive](https://apimodels.app/claude-opus-5-5-video-prompts/motion-graphics), **retrieved 2026-10-20**, was used as an attributed secondary cross-check for the launch workflow's longer technical instructions. It is a secondary reproduction, not the original author or an independent source-code release.

The resulting [twoclipping family guide](references/twoclipping.md) is independently written. Its reusable defaults, local-audio policy, integration contract and review guidance are this skill's additions. The original full prompts, films and branding are not bundled, and no endorsement or open-source licence for the social posts is claimed. The [overlap analysis](references/twoclipping-overlap.md) explains why the family was added alongside Lemo's existing styles.

## 3. Licence and asset attribution

These statements describe the notices in the fetched snapshot, reviewed on **2026-10-20**:

- **Lemo code and documentation:** MIT, copyright **2026 LemoLab**. Preserve the bundled [licence notice](assets/lemo/LICENSE) when copying or adapting covered source.
- **Upstream demo films and stills:** the upstream [README licence section](assets/lemo/README.md#licence) identifies CC BY 4.0 terms and requests attribution to LemoLab, a repository link and identification of changes when that media is reused.
- **New films:** upstream says films made with the library need no Lemo credit. Obligations attached to separately licensed fonts, music, images, models, data or other reused materials still apply.
- **Third-party materials:** retain their own terms. Consult the selected demo's `CREDITS`, the bundled [font notices](assets/lemo/core/fonts/OFL.md), and the [Poly Haven source notices](assets/lemo/core/assets/polyhaven/SOURCES.md) where relevant. Those notices were fetched with the repository on **2026-10-20**; this date does not claim that every original external asset or model binary was separately downloaded or relicensed.
- **Package scope:** the upstream MIT notice does not establish a single blanket licence for every asset or social reference in the collection. Preserve the notices for the material actually used in a film or redistributed source project.

For production-specific attribution and completeness rules, see [sources-and-licenses.md](references/sources-and-licenses.md).

## 4. Original additions and update policy

The main skill instructions, searchable catalogue and indexes, runtime preparation helper, strict browser exporter, browser starter, and twoclipping family adaptation were assembled or authored for this skill on **2026-10-20**. The strict exporter uses the bundled Lemo local server; its additional capture, asynchronous seeking, temporal-sampling and verification logic is a new wrapper. The 2026-10-21 repair changes font references and font-fetch build steps inside `assets/lemo/`; patched files carry both upstream and bundled hashes in the manifest. All style-specific engine code retains its upstream bytes.

When deliberately updating this skill, record the new retrieval date and exact source revision here and in the manifest, refresh the catalogue, preserve source notices, and run `scripts/verify_bundle.py`. Retain the dates of unchanged references. Do not replace retrieval dates with the current date merely because the package is reopened or exported again.

## 5. Offline asset and font repair — 2026-10-21

- Restored all nine tracked shared Poly Haven JPG textures from the same pinned Lemo revision; retained its source notices.
- Bundled 105 original font binaries across 77 SIL OFL families from [google/fonts](https://github.com/google/fonts/tree/47d54ca1ebb14fd864695f1d39dc734f39017c33), retrieved 2026-10-21 (Asia/Kuala_Lumpur). Exact URLs, file hashes and family notices are in [font-replacements.json](references/font-replacements.json); usage rules are in [font-replacements.md](references/font-replacements.md).
- Replaced unavailable local/subset font URLs with bundled full fonts, preserving family aliases, and disabled demo build font downloads. Removed an unrelated external font link from an archived music-source page.
- Added style-preserving project setup, literal-asset preflight, font/model dependency checks and bundle-aware runtime reuse. The manifest now records every excluded tracked upstream file.
- Improved deterministic DOM capture and the browser starter; representative browser checks cover the starter, Whiteboard engine/stroke data, Swiss typography and restored textures. These checks do not certify every original demo or generated narration asset.

## 6. Style and craft references added 2026-10-22

Four further permissive sources extend the style vocabulary, the craft guidance and the bundled media. All four were retrieved on **2026-10-22** at the pinned commits below. Every bundled file is listed with its SHA-256 in [vendored-assets.json](references/vendored-assets.json) and verified by `tests/test_media_skill_packaging.py`. None of them is a required runtime dependency: the packages they came from are not needed to build or render a film.

| Source | Licence | Contribution | Bundled location |
| --- | --- | --- | --- |
| [yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos) at [`92aee2f586ac0715cb3cbcb6384834f98a33383d`](https://github.com/yihui-dev/awesome-opus5-5-videos/tree/92aee2f586ac0715cb3cbcb6384834f98a33383d) | MIT, copyright 2026 yihui-dev | 703 attributed community prompts for code-rendered video, with creator and original-post links | [assets/prompt-library/opus55-videos.json](assets/prompt-library/opus55-videos.json), [LICENSE-opus55-videos.txt](assets/prompt-library/LICENSE-opus55-videos.txt) |
| [Vincentwei1021/mg-styles-15](https://github.com/Vincentwei1021/mg-styles-15) at [`49052d80bfaf9fa8412cc9710530e5e95a3b8d8c`](https://github.com/Vincentwei1021/mg-styles-15/tree/49052d80bfaf9fa8412cc9710530e5e95a3b8d8c) | MIT (prompts, rubric, template, films); CC0 (paper texture, HDRI) | 15 motion-design style prompts, the independent review method, one still per style, the review prompt and the authoring template | [assets/prompt-library/mg-styles-15.json](assets/prompt-library/mg-styles-15.json) with [LICENSE-mg-styles-15.txt](assets/prompt-library/LICENSE-mg-styles-15.txt); [assets/mg-styles15/](assets/mg-styles15/) with its [LICENSE](assets/mg-styles15/LICENSE) and [asset notices](references/mg-styles15-asset-notices.md); [style-prompt-library.md](references/style-prompt-library.md) |
| [JohnHeibel/ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase) at [`0ac8bf2b31942376cb6b8c4074715595d512acd2`](https://github.com/JohnHeibel/ClaudeAnimationBase/tree/0ac8bf2b31942376cb6b8c4074715595d512acd2) | MIT, copyright 2026 John Heibel | Craft rules for hand-painted acted 2D cartoon animation, plus the runnable starter kit: brush character rig, 31 emotions, five drawn views, model sheets and headless renderer | [hand-painted-cartoon.md](references/hand-painted-cartoon.md); [assets/hand-painted-cartoon/](assets/hand-painted-cartoon/) with its [LICENSE](assets/hand-painted-cartoon/LICENSE) |
| [mexicat/pdoom-video](https://github.com/mexicat/pdoom-video) at [`fa164b74fd0b26a99375715b619c55b4a0fb3d05`](https://github.com/mexicat/pdoom-video/tree/fa164b74fd0b26a99375715b619c55b4a0fb3d05) | MIT, copyright 2026 Giacomo Magnanini | Treatment structure, lyric alignment, beat grid and deterministic scene contract for music-led films, plus the alignment and analysis pipeline itself | [music-video-and-lyrics.md](references/music-video-and-lyrics.md); [assets/lyric-alignment/](assets/lyric-alignment/) with its [LICENSE](assets/lyric-alignment/LICENSE) |

### Transformations and exclusions

- **opus55-videos:** `data/videos.json` was flattened into the bundled record set; the hosted-remake and poster URLs were dropped, `slug` became `id` and `tech_tags` became `techniques`. Entries whose creator published no full prompt are kept and marked `prompt_complete: false`, because their text is the creator's original post rather than a prompt. Prompts are reproduced verbatim, with attribution. The upstream README, site assets and remake catalogue are not bundled.
- **mg-styles-15:** the prompt body, title and reference-film line were extracted from each `prompts/*.md` into `assets/prompt-library/mg-styles-15.json`; the per-style demo paths were dropped. Bundled unchanged: the review prompt (`rubric.md`), the authoring template (`template.md`), one still per style from `docs/readme/films/`, the 4K paper texture and the 2K studio HDRI. Not bundled: the 421 MB of reference films (the stills carry the visual reference), the 64 MB of demo projects (`demos/`) and the `lib/audio` soundtrack toolkit with its 103 CC0 instrument samples, because this skill already ships a procedural audio and sampler tier in `assets/lemo/core/audio/` and the toolkit adds a numba/pedalboard dependency for a capability that is already covered. The `washi/`, `dust/` and `grain/` textures are also left out: the upstream licence section names the paper texture and the HDRI but not those three, so their provenance is unverified. The films' fonts are not in the upstream repository either; its `assets/fonts/README.md` lists them and they keep their own licences (SIL OFL, and vendor free-use terms for the Chinese display faces), so a film built from these prompts falls back to system fonts unless the user supplies matching ones. The review method is also rewritten as guidance in [style-prompt-library.md](references/style-prompt-library.md).
- **ClaudeAnimationBase:** the kit is bundled unchanged in [assets/hand-painted-cartoon/](assets/hand-painted-cartoon/): `ANIMATION_GUIDE.md`, the brush character rig and emotions (`src/clawd.js`), the painting and timing helpers (`src/core.js`), shots and transitions (`src/timeline.js`), the demo scene, the two model sheets, `studio.html`, the headless renderer and its lockfile. The repository's own `.gitignore` and `package.json` scripts were kept as published. [hand-painted-cartoon.md](references/hand-painted-cartoon.md) remains an abridged adaptation of the guide that keeps the craft rules and explains how to map them onto another brush engine, so an agent can work without the kit.
- **pdoom-video:** [music-video-and-lyrics.md](references/music-video-and-lyrics.md) is an adapted summary of `docs/TREATMENT.md` and `docs/ENGINE.md`. The `analysis/` pipeline is bundled unchanged in [assets/lyric-alignment/](assets/lyric-alignment/) — Demucs stem separation, CTC forced alignment cross-checked with Whisper, beat/downbeat/onset and loudness analysis — with its `pyproject.toml`, `uv.lock` and licence. Its own licence section excludes the song and the lyrics from MIT: the lyrics are by osmarks on an opening verse and chorus by MusicPerson, and the recording is a third-party Suno version posted by deckard. `audio/pdoom.mp3`, the lyric text and timings, and the derived `data/lyrics*.json` and `data/audio.json` timing data are therefore **not** bundled and no licence to them is claimed; a few comments in the analysis code quote short lyric fragments while explaining an alignment decision. The renderer and scene modules in `app/` are the project's own MIT work but are not bundled: they need bun, Vite and a three.js stack this skill does not use. The `app/public/plates/` stills are left out because they show lyric typography. The upstream project's shot list and motifs are described only as method.

Two of the bundles ship the dependency manifests they came with. The kit's `package.json` and the alignment pipeline's `pyproject.toml` keep their upstream version ranges, and each is accompanied by its committed lockfile (`package-lock.json`, `uv.lock`), which pins the exact resolved versions. The manifests are left unedited so their hashes stay pinned to the upstream revision; reproducibility comes from the locks, not from rewriting vendored files.

### Licence boundary

Each upstream repository publishes an MIT licence over its own code, prose and assets, and two of them extend or narrow that grant. The bundles follow the notices rather than an assumption:

- **Included under a notice that is not MIT.** The taste-skill example screenshots in the `design-taste` skill are CC BY-SA 4.0 because they adapt CC BY-SA photographs; that skill carries the per-photograph credits, the CC BY-SA legal code and a dedicated notice. In this skill, the paper texture and HDRI from mg-styles-15 are CC0, with their attribution in [mg-styles15-asset-notices.md](references/mg-styles15-asset-notices.md).
- **Excluded because they are not the upstream author's to license.** The pdoom song and lyrics belong to their authors, and the pdoom plates reproduce lyric typography, so none of them are bundled.
- **Excluded for size or duplication.** The MG reference films, demo projects, soundtrack toolkit and samples, and the pdoom `app/` renderer are redistributable but large, already covered by this skill's own renderer and audio tier, or both.
- **Excluded for unverified provenance.** The `washi/`, `dust/` and `grain/` textures are not named in the upstream licence section, so they are treated as third-party-rights items and left out.

No endorsement by any upstream author is implied.

### Verification note

`tests/test_portable_skill_scripts.py` checks that both libraries parse, that every record keeps the fields the reader prints, that ids are unique, that filters and full-record reads work, and that a standalone copy of the skill resolves the libraries from any working directory. `tests/test_media_skill_packaging.py` verifies that every bundled file in the three asset bundles matches its pinned hash, that no unlisted file was added, that each bundle names its source and licence, and that the vendored Python and JavaScript parse. No film was made with these references or the starter kit during the import, so the guidance and the kit are unverified in production.
