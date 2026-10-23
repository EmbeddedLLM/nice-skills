# Direction and production workflow

## Contents

1. Brief and treatment
2. Match style to explanation
3. Time, narration and captions
4. Assets and factual material
5. Preview and inspect
6. Deliver and revise

## 1. Brief and treatment

Resolve routine choices from the goal and existing conversation. A film request authorizes normal reversible production, not only a plan. Ask only when a necessary fact, asset or choice cannot be reasonably inferred. Stop at storyboard review only when requested.

Write a treatment before opening the selected demo or scene code. Include viewer, takeaway, logline, chosen structure, shot/cue table and ending. Use one central idea for a short film. Introduce a useful question or change immediately; earn a logo/end card through the story.

For education, let each scene answer a question left by the previous one. Captions should clarify instead of repeating dense paragraphs. Do not invent capabilities, measurements or customer statistics for a launch.

For a UI loop, reduce the treatment to states, causal transitions, cursor behavior, beat map and seam condition. A 12-second loop does not need the same number of scenes, silences or camera moves as a 90-second lesson. Treat upstream numeric directing heuristics as style-dependent guidance.

## 2. Match style to explanation

Use STYLE.md for visual invariants. Painting should exhibit paint behavior; whiteboard should draw in coherent space; Swiss should keep grid logic; product morphs should preserve understandable identity.

After the treatment exists, inspect the relevant engine and documentation. Copy the minimum reusable source or import shared runtime utilities. Build a new story and timeline. Do not deliver a demo with changed nouns as an original film.

Treat OPUSCAR entries as reference prompts with renderer hints. Their original shot lists, timecodes and titles describe the compilation. `styles.py show opuscar:<n>` loads the reusable prompt/description without the original shot plan. Do not imply every entry has a separate ready-made engine.

## 3. Time, narration and captions

Choose speech when useful; respect silence/music-only requests. Use a supplied recording or available offline voice. Create speech first, measure durations, verify names/numbers, and align picture to it. Voice choice is not a reason to introduce a paid service automatically.

Kokoro needs model downloads; offline describes subsequent synthesis. EdgeTTS is online and is not the default for local-only work. Read exact installation and language/voice instructions before use.

Use one declarative timeline for visuals, captions, cues and metadata. Leave a useful reading interval after a label settles. Reduce words or extend dense scenes. The beat grid must not force readers to chase text.

Use local fonts with required glyphs. CJK subtitles need proper coverage; a small display subset is insufficient. Handwriting needs stroke/path information or an honestly described reveal. Inspect punctuation, symbols and numbers in rendered frames.

Compose local music or use supplied/licensed audio. Align audible onsets, keep speech intelligible, and balance effects. Around −14 LUFS can suit web delivery; inspect true peaks and listen when playback is available. A loudness number alone does not establish quality.

## 4. Assets and factual material

Keep a manifest with local filename, role, origin URL or user-supplied status, license/attribution, and transformations. Software, fonts, recordings, imagery and datasets have distinct terms. Preserve relevant source notices.

Use user material first. For Evidence Films, record source acquisition date, units, coordinate system, processing and uncertainty when relevant. Use real scans/data for real-world claims. Label illustrative, simulated or hypothetical data.

Reference images omitted from the bundle are listed in upstream-manifest.json. Other production media are absent upstream too. Read CREDITS and reconstruct only necessary assets. Do not claim reproducibility until dependencies are present and rendering succeeds.

## 5. Preview and inspect

Inspect real style frames, including the signature shot, busiest text and hardest transition. Render a short sample for timing. Use representative checks; do not render an expensive full film merely to validate a small correction.

Check concrete risks:

- Missing media, glyphs, wrong fonts or decode failures.
- Text clipped by masks/camera, subtitles covering action, tiny type or low contrast.
- Frame differences after repeated timestamps or out-of-order seeks.
- Incremental physics, live CSS clocks, unseeded randomness or animation continuing after a seek.
- Boundary jumps, stale footage and duplicated loop endpoints.
- Invalid geometry, unintended transparency, unexplained blank frames and NaN-driven disappearance.
- Wrong numbers, invented diagrams presented as measured, or mismatched units.
- Mispronunciations, absent requested audio, clipping, late cues and unreadable captions.

Use strict-renderer checks for temporal consistency. They do not prove visual quality or factual accuracy. Inspect frames and, if available, complete final playback with sound. State if only frames and metadata could be reviewed.

## 6. Deliver and revise

Deliver MP4 with requested sound, poster, applicable captions, and editable source with needed assets. Include TREATMENT.md, CREDITS, asset manifest and a one-command build script. Exclude credentials, secrets, node_modules and temporary capture caches.

Use portable paths. Resolve the runtime through project config or a documented variable instead of a private absolute path. Record exact settings and upstream commit.

For revisions, preserve the source and intentionally change content, timing or style. Preview the relevant section, then render final output. Report actual changes/checks. Use the host's persistent deliverable workflow.
