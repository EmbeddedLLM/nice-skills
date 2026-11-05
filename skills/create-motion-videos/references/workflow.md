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

When a transition is meant to grow from an existing object, name that subject and track its starting anchor, silhouette, scale and color into the next state. Derive the deformation, reveal mask or particle origin from that visible object. Animate camera or composition changes separately: scaling the whole group or introducing an unrelated replacement shape does not establish the subject's continuity. This applies to object-driven transitions; deliberate cuts, wipes and new compositions remain valid choices.

After the treatment exists, inspect the relevant engine and documentation. Copy the minimum reusable source or import shared runtime utilities. Build a new story and timeline. Do not deliver a demo with changed nouns as an original film.

Treat OPUSCAR entries as reference prompts with renderer hints. Their original shot lists, timecodes and titles describe the compilation. `styles.py show opuscar:<n>` loads the reusable prompt/description without the original shot plan. Do not imply every entry has a separate ready-made engine.

## 3. Time, narration and captions

Choose speech when useful; respect silence/music-only requests. Use a supplied recording or available offline voice. Create speech first, measure durations, verify names/numbers, and align picture to it. Voice choice is not a reason to introduce a paid service automatically.

Kokoro needs model downloads; offline describes subsequent synthesis. EdgeTTS is online and is not the default for local-only work. Read exact installation and language/voice instructions before use.

Use one declarative timeline for visuals, captions, cues and metadata. Leave a useful reading interval after a label settles. Reduce words or extend dense scenes. The beat grid must not force readers to chase text.

For a narrated sequence of features or actions, record each phrase's measured start/end, corresponding visual state, entrance interval and readable hold in spoken order. Derive any active headline, icon, detail content and camera target from the same cue. Have the relevant state readable by its phrase onset and keep it identifiable through the phrase. Put introductions and transitions in the available lead-in or gaps; if time is tight, shorten the entrance or use a persistent layout. Equal visual intervals or template order can disagree with unequal spoken phrases. ASR/alignment timestamps are estimates to check against the actual audio.

Plan vocal emphasis and pauses as part of the narration direction. When a product name and tagline need separate beats, give the name its own delivery and leave an intentional pause before the tagline. Punctuation alone does not guarantee a TTS pause. If necessary, record or generate separate phrases with the same voice, preserve natural word tails, and schedule the gap using measured clip lengths as described in [runtime.md](runtime.md#4-voice-music-captions-and-muxing). Choose the pause and delivery for this line; there is no universal duration or speed. Align the visual reveal and captions to the chosen delivery, and retain an end-card reading hold.

Use local fonts with required glyphs. CJK subtitles need proper coverage; a small display subset is insufficient. Handwriting needs stroke/path information or an honestly described reveal. Inspect punctuation, symbols and numbers in rendered frames.

Compose local music or use supplied/licensed audio. Align audible onsets, keep speech intelligible, and balance effects. Around −14 LUFS can suit web delivery; inspect true peaks and listen when playback is available. A loudness number alone does not establish quality.

## 4. Assets and factual material

Keep a manifest with local filename, role, origin URL or user-supplied status, license/attribution, and transformations. Software, fonts, recordings, imagery and datasets have distinct terms. Preserve relevant source notices.

Use user material first. For Evidence Films, record source acquisition date, units, coordinate system, processing and uncertainty when relevant. Use real scans/data for real-world claims. Label illustrative, simulated or hypothetical data.

Reference images omitted from the bundle are listed in upstream-manifest.json. Other production media are absent upstream too. Read CREDITS and reconstruct only necessary assets. Do not claim reproducibility until dependencies are present and rendering succeeds.

## 5. Preview and inspect

Inspect real style frames, including the signature shot, busiest text and hardest transition. Render a short sample for timing. Use representative checks; do not render an expensive full film merely to validate a small correction.

Review short encoded passages with their mixed audio, including enough lead-in and tail to judge the handoff:

- For an object-driven transition, trace the subject immediately before, during and after the move. Look for a substituted or duplicated object, unexplained jump, or unrelated group scaling.
- For a narrated sequence of features or actions, inspect frames around each measured phrase onset and through its interval. Confirm that any headline, emphasis, icon, details and camera refer to the spoken item. Count reading time after the entrance settles; scene midpoints alone can miss a late or out-of-order state.
- For a closing line with separate name/tagline beats, listen for the intended name emphasis, audible pause and tagline pace in the final mix. Check the associated visual/caption entrances and the final reading hold.

Check concrete risks:

- Missing media, glyphs, wrong fonts or decode failures.
- Text clipped by masks/camera, subtitles covering action, tiny type or low contrast.
- Frame differences after repeated timestamps or out-of-order seeks.
- Incremental physics, live CSS clocks, unseeded randomness or animation continuing after a seek.
- Boundary jumps, stale footage and duplicated loop endpoints.
- Invalid geometry, unintended transparency, unexplained blank frames and NaN-driven disappearance.
- Wrong numbers, invented diagrams presented as measured, or mismatched units.
- Mispronunciations, absent requested audio, clipping, late cues and unreadable captions.

Use strict-renderer checks for temporal consistency. Matching frame hashes, valid media metadata and an accurate ASR transcript do not prove semantic synchronization, natural speech cadence, visual quality or factual accuracy. Inspect frames and, if available, complete final playback with sound. State which playback/listening checks were unavailable; do not describe timing calculations or transcript checks as listening.

## 6. Deliver and revise

Deliver MP4 with requested sound, poster, applicable captions, and editable source with needed assets. Include TREATMENT.md, CREDITS, asset manifest and a one-command build script. Exclude credentials, secrets, node_modules and temporary capture caches.

Use portable paths. Resolve the runtime through project config or a documented variable instead of a private absolute path. Record exact settings and upstream commit.

For revisions, preserve the source and intentionally change content, timing or style. After changing narration, remeasure the final clips and update affected visual cues, captions and any delivered cutdowns from the same timing data. Preview the relevant section, then render final output. Report actual changes/checks. Use the host's persistent deliverable workflow.
