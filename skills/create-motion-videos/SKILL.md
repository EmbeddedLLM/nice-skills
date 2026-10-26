---
name: create-motion-videos
description: Create and revise code-rendered explainer videos, motion graphics, product launches, short films and UI animation loops using every Lemo-Opuscar style plus twoclipping-inspired UI morph and product-launch variants. Use for videos or MP4s made with HTML, CSS, SVG, Canvas, WebGL or Three.js; Whiteboard, Swiss Motion, Lemo, Opus-style videos, animated explainers, local rendering without paid video services, browsing styles, and adapting a personal video style. Includes 59 Lemo style guides and 98 OPUSCAR film-style references, deterministic browser rendering, narration, captions and editable source. Not for routine conversion or trimming of an existing video.
---

# Motion Video Studio

Produce the user's film from editable code, then deliver the actual video and the source needed to change it. Treat the selected style as art direction; build the story around the user's topic.

The destination agent may have no access to OpenAI, Anthropic, Minimax, or other paid providers. Use local code rendering, supplied assets, procedural imagery/audio, and optional offline speech. Upstream provider/model names describe provenance, not prerequisites. Optional `agents/openai.yaml` is discovery metadata, not an API dependency.

For documentary/evidence films or music-led product edits, read [evidence and editing](references/evidence-and-editing.md). It covers the eight new style guides, source/claim tracking, real-product capture, and beat-phase verification.

## Orient and load only what is needed

Use the directory containing this file as `SKILL_DIR`. Keep bundled source read-only. The bundled Lemo snapshot includes documented font-path patches; consult references/font-replacements.md before changing typography. Create a separate writable runtime and film project in the task's workspace; never generate films inside this skill.

1. Read [style-index.md](references/style-index.md) for the 59 Lemo styles and the added twoclipping family. Resolve English, Chinese or slug names with `python3 "$SKILL_DIR/scripts/styles.py" list --query "<name or purpose>"`.
2. Load exactly the chosen STYLE.md using `styles.py show lemo:<slug>`. For twoclipping, read [twoclipping.md](references/twoclipping.md) and choose `ui-morph` or `product-launch`.
3. For a cinematic reference, search [opuscar98-index.md](references/opuscar98-index.md), then run `styles.py show opuscar:<number>`. Use its reusable style prompt, not its example film's characters, shot sequence or timing. These 98 references are separate from the 59 style guides: 51 include earlier source packages, and eight additions are guide-only.
4. When the user names an effect by feel or asks for a style outside this catalogue, search the bundled prompt libraries before choosing: `python3 "$SKILL_DIR/scripts/prompt_library.py" list --query "<effect>"`. Read [style-prompt-library.md](references/style-prompt-library.md) for the two libraries, the vocabulary of techniques, how to write a checkable style prompt and the independent review loop. Name the technique back to the user in one line before building to it. For the fifteen MG styles, look at `assets/mg-styles15/stills/<id>.webp` before you decide: each is a still from the film that prompt produced, so it shows what the style actually looks like. `assets/mg-styles15/rubric.md` is the ready-made independent review prompt, and `template.md` is the skeleton for writing a new style prompt.
5. Pick the craft reference that matches the deliverable. An acted 2D cartoon (a character wants something, tries, reacts) follows [hand-painted-cartoon.md](references/hand-painted-cartoon.md) and can be built on the bundled kit in `assets/hand-painted-cartoon/`: read its `ANIMATION_GUIDE.md` for the drawing API, then `npm install` and `node render.mjs --sheet=...` to check poses, or expose `window.render(t)` and render with `scripts/render.mjs`. A film cut to supplied music follows [music-video-and-lyrics.md](references/music-video-and-lyrics.md) for the treatment, word-level lyric sync and beat grid, and can reuse the bundled alignment pipeline in `assets/lyric-alignment/` (Demucs stems, CTC alignment cross-checked with Whisper, beat and onset analysis; heavy optional dependencies, instructions in its `pyproject.toml`).
6. Read [workflow.md](references/workflow.md) for direction, timing, voice, review and delivery. Read [runtime.md](references/runtime.md) before setup or rendering. Consult upstream [DIRECTOR.md](assets/lemo/DIRECTOR.md), [TECHNIQUE.md](assets/lemo/TECHNIQUE.md) and [core commands](assets/lemo/core/README.md) for deeper production details.
7. Write the user's treatment before opening `assets/lemo/styles/<slug>/DEMO.md` or `demo/` code. Reuse a drawing technique, rig or shader after deciding an original story. Demo sources are bundled; original generated narration and some reference media are not. Bundled fonts and shared textures are validated separately from optional demo production media.

Keep current user requirements and the host's tool and permission rules authoritative. Apply this skill's operational defaults when upstream guides assume a different host, fixed home-directory paths, automatic updates or mandatory consultation. Preserve style constraints unless the user requests an adaptation. Never modify policy or permissions to make a workflow run.

## Keep production code focused

Separate the film's required story, timing, style, and delivery contract from the proposed engine or workflow. Apply YAGNI to infrastructure: reuse project and bundled runtime capabilities, then standard-library and native browser/media tools, then installed dependencies before adding a renderer, orchestration layer, or package. Use a short representative render to resolve uncertain behavior before building a larger mechanism. Install only the dependency tiers needed for the film; do not prepare every optional pipeline by default.

After the sample works, remove unused scene machinery, duplicated timing logic, and speculative controls while preserving the chosen art direction, determinism, audio synchronization, and output contract. Fix root causes and retest affected frames and delivery properties. Simplifying code is not permission to replace a requested visual technique with an easier style or weaken verification.

Before adding complexity for a speculative or vanishingly unlikely race or security edge case, explain the concrete failure mode, evidence for its likelihood (or uncertainty), implementation and maintenance cost, and simpler alternative. Get user buy-in for that scope expansion unless existing approval already covers the trade-off. Do not silently add theoretical robustness, weaken required controls, or delay an already-authorized fix for a demonstrated defect.

## Choose a style without blocking production

Use an explicitly requested style. If the brief is sufficient but no style is named, select a fit, state the choice briefly, and continue. Offer alternatives when their tradeoff matters; wait only when the user requests selection or a missing fact prevents useful work.

| Need                                                       | Starting point                                                |
| ---------------------------------------------------------- | ------------------------------------------------------------- |
| Teach a mechanism or causal chain                          | `lemo:whiteboard`                                             |
| Precise typography, rules, stages and comparisons          | `lemo:swiss-motion`                                           |
| Real measurements, charts or numerical comparisons         | `lemo:dataviz`                                                |
| Short, smooth component transformations                    | `twoclipping:ui-morph`                                        |
| Product launch with interface actions and optional imagery | `twoclipping:product-launch`                                  |
| Dark staged technology presentation                        | `lemo:dark-keynote`                                           |
| Faithful product walkthrough with the style's mascot       | `lemo:living-screencast`                                      |
| GIS, satellite, LiDAR, CAD, microscopy or archives         | Match the Evidence Films category to the actual material      |
| Illustration, print, cartoons, games or 3D                 | Use the full category index; do not substitute Swiss by habit |

Treat `twoclipping`, `zero`, `continuous-ui-morph`, and `UI morph` as aliases for the added family. Its two variants independently adapt public demonstrations. Lemo's nearest styles differ from its combination of light UI, persistent component identity and restrained springs; see [overlap](references/twoclipping-overlap.md).

The bundled prompt libraries are a second vocabulary, not a style set to deal: 703 attributed community briefs for code-rendered video and 15 motion-design style prompts built around a fixed 10-second spec. Use them to name the technique the user is describing, to see how a short brief is phrased, and to adapt signature features; keep this skill's workflow, the user's story and the user's output contract. See [style-prompt-library.md](references/style-prompt-library.md).

## Bundled assets outside the Lemo snapshot

These travel with the skill and are optional; each is pinned by hash in [vendored-assets.json](references/vendored-assets.json). Read the referenced document before using one, and never edit the copies in place — copy what you need into the writable project.

| Path | What it is, and when to open it | Licence |
| --- | --- | --- |
| `assets/prompt-library/` | 703 community briefs and 15 MG style prompts, read with `scripts/prompt_library.py`. Use to name a technique or adapt a signature feature. | MIT, per-collection notices in the directory |
| `assets/mg-styles15/stills/` | One still from each of the fifteen MG films. Look before choosing one of those styles. | MIT |
| `assets/mg-styles15/rubric.md`, `template.md` | The independent review prompt and the style-prompt authoring skeleton. Use for a review round or a new style. | MIT |
| `assets/mg-styles15/textures/paper/`, `hdri/` | A 4K paper texture and a 2K studio HDRI for print, engraving and staged-product looks. | CC0, see [asset notices](references/mg-styles15-asset-notices.md) |
| `assets/hand-painted-cartoon/` | Clawd starter kit: brush-based character rig, 31 acted emotions, five drawn views, model sheets, headless renderer and its `ANIMATION_GUIDE.md`. Use for an acted 2D cartoon. | MIT, `John Heibel` |
| `assets/lyric-alignment/` | Alignment and analysis pipeline for music-led films: lyric timing, stems, beat grid. Use when the film must sync to supplied audio. | MIT, code only |
| `assets/lemo/` | The pinned Lemo style snapshot and shared tools, including 105 bundled fonts and shared Poly Haven textures. | MIT with CC BY media notices; see [SOURCES.md](SOURCES.md) |

## Defaults

- Infer language from the request. Use supplied brand requirements, narration, fonts, imagery and data. Ask only for missing facts or assets that materially prevent completion; do not ask again for choices already made.
- Default to 30–60 seconds and 1920×1080 for an ordinary explainer. Use the selected style's frame rate; 24 fps is the general Lemo fallback, not a universal constraint. Use 60 fps for twoclipping final output and its variant's aspect ratio. Respect vertical, square, silent and shorter requests.
- Default to no additional paid image, video, voice, stock or rendering service. Use local rendering, procedural visuals/audio, user assets and appropriate free assets. Keep model-access costs separate from production-service costs. Never promise $0 model use.
- When external imagery or sound would help, use optional [Openverse acquisition](references/sources-and-licenses.md#optional-openverse-assets) during asset planning. Download and credit selected media before rendering; preserve the supplied/procedural route when offline.
- Use supplied speech or available offline TTS for narration. Keep render-time assets local. Do not introduce online TTS when local-only work is requested. Install dependencies in the runtime or project, not global Python or Node environments.
- If offline speech for the requested language is unavailable, use supplied recordings or report the missing capability. Do not substitute a paid voice or image API to complete a render. Dependency/model downloads need network access during setup; offline production starts only after required assets are present.
- Use the available model/agent. Mention Lemo's original Opus 5.5 tuning only when relevant; do not require switching models or promise identical results across models.
- Make style frames and review them internally. Stop for storyboard approval only if the user requested that checkpoint. Continue through rendering when work is already authorized.

## Produce the film

1. **Brief and evidence.** Fix the audience, objective, facts, length, aspect ratio and sound needs. Verify factual explainer claims. For Evidence Films, use sourced measurements/data and record transformations. Label hypothetical or synthetic material accurately.
2. **Treatment.** Write TREATMENT.md with an original opening, progression, turn and ending. Consider a few structures privately, select one, then specify shots, time ranges, text, narration, motion and audio cues. Give complex ideas time to be understood. For a music-led film use the treatment sections in [music-video-and-lyrics.md](references/music-video-and-lyrics.md); when the film is an acted cartoon, add the storyboard and reads that [hand-painted-cartoon.md](references/hand-painted-cartoon.md) requires.
3. **Runtime.** Use scripts/prepare_project.py with the selected style to preserve its resource tree in a new project. Read the project path rules in references/runtime.md, especially document-relative fetch URLs. Run prepare_runtime.py with a writable destination outside the skill. Install only necessary local tiers. Read renderer `--help`; honor host network and install approvals. Keep the pinned revision.
4. **Style frame.** Use actual drawing code, fonts and dimensions. For characters, establish consistent poses and expressions. Inspect the difficult shot before implementing the whole timeline.
5. **Audio.** Generate or import narration, measure it, align captions, then fit visuals to speech. Make the score and interaction sounds from the same cue map. Honor silence requests.
6. **Random-access frames.** Expose `window.DUR`, `window.READY`, and `window.render(t)` or `window.seek(t)`. Compute complete state from time, content and fixed seeds. Await media seeks and decoding. Avoid live timers, unseeded randomness, incremental physics and carried state during capture.
7. **Preview.** Run scripts/audit_assets.py against the composition and resolve missing dependencies. Use deterministic checks and selected stills, then a short sample of the hardest transition. Fix clipping, glyph failures, masks, stale media, illegible type, poor pacing and wrong facts before final export.
8. **Render and mix.** Capture at the selected size/rate and encode MP4. Use temporal supersampling only when useful and supported. Mix sound separately and mux the final film. A silent capture is not a completed narrated deliverable.
9. **Deliver.** Inspect representative frames and final duration, dimensions, frame count and audio. Review playback and sound when available; state material review limits. Deliver MP4, poster, applicable captions, editable source, TREATMENT.md, CREDITS, asset manifest and a reproducible build command. Use the host's persistent-file workflow.

## Drawing and time are independent choices

Use Canvas for procedural drawing and stroke engines; DOM/CSS/SVG for browser-like UI and type; Three.js/WebGL for spatial or shader work. Keep the deterministic time contract in every case. Combine technologies when useful.

Do not call every style CSS-only. The inspected Whiteboard and Swiss engines draw in Canvas. Twoclipping compositions calculate HTML/CSS/SVG properties from JavaScript time. If the user requests CSS keyframes, author them deliberately, pause and seek through the Web Animations API, and test out-of-order frame equality. Do not infer a timing mechanism from a social caption.

Use the [browser starter](assets/browser-starter/index.html) as a minimal deterministic scaffold. It is an engineering starter, not a polished style implementation or substitute for the user's storyboard. Read [browser-renderer.md](references/browser-renderer.md) for the strict exporter, asynchronous frame functions and grouped temporal samples.

## Preserve style and source integrity

- Read the selected style fully. Retain palette logic, motion, materials and camera rules; do not add springs to Swiss Motion by accident.
- Follow Evidence Film measurement/source requirements. Never invent a scan, treat imagery as measured data, or relabel random geometry as a real reconstruction.
- Check fonts for the actual language. Do not render missing Chinese glyphs or imply a Latin single-stroke font supplies CJK handwriting. Use suitable licensed font/path data or a compatible treatment.
- Read CREDITS before reusing demo assets. Preserve the MIT source notice and separate asset attribution. Do not carry LemoLab or Opus promotional end cards into an original film unless requested.
- Do not promise every upstream demo renders from a clean clone. Generated voices, fonts and other media can be absent. Reconstruct only assets needed for the new film.
- Keep personal variants in the project or designated persistent styles location, preserving the base. Document changed invariants and render a short sample if useful. Do not impose an unrequested approval gate.

## Reference map

| Resource | Read when |
| --- | --- |
| [Main style index](references/style-index.md) | Selecting/listing all 51 Lemo styles and two twoclipping variants |
| [OPUSCAR 98 index](references/opuscar98-index.md) | Selecting a film-era or named cinematic reference |
| [Machine catalogue](references/catalogue.json) | Searching exact slugs, bilingual names, categories and source paths |
| [Direction and quality](references/workflow.md) | Producing/revising a film |
| [Runtime and audio](references/runtime.md) | Preparing, rendering, muxing or packaging |
| [Browser renderer](references/browser-renderer.md) | Async DOM/Canvas capture and motion blur |
| [Twoclipping family](references/twoclipping.md) | UI morph and light product-launch direction |
| [Twoclipping overlap](references/twoclipping-overlap.md) | Explaining the additional family |
| [Sources and retrieval dates](SOURCES.md) | Original source URLs, fetched dates, pinned revision and attribution |
| [Sources and licenses](references/sources-and-licenses.md) | Attribution, reuse, cost and completeness |
| [Additional production modes](references/production-modes.md) | Kinetic type, music visualizers, loops, footage captions, and authorized personal stories |
| [Upstream manifest](references/upstream-manifest.json) | Verifying a pinned snapshot or deliberate update |

Run `python3 "$SKILL_DIR/scripts/verify_bundle.py"` after an intentional update. Do not download newer upstream main automatically during production.
