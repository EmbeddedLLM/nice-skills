# Music videos, lyric sync and beat-driven type

Use this when the film is cut to supplied music: a title sequence, a word-synced lyric video, a launch film scored to a track, or a music video whose type is part of the image. It is an adapted summary of the _I'm Upping My P(doom)_ treatment and engine guides by the pdoom-video authors (MIT; see [SOURCES.md](../SOURCES.md)), reduced to the parts that transfer to another project.

The song is supplied material. Do not redistribute it, do not claim it, and do not analyse a track you have no right to use.

## 1. Treatment first: the style bible

A music video is decided by a written treatment, not by the first scene that renders. Write these sections before any scene code, and keep the file in the project:

- **The idea in one paragraph.** The organising conceit (a treatise, a broadcast, a ledger, a strip of film) and how the recurring motif moves through it.
- **Tone.** Three or four adjectives, plus an explicit list of what the film is not. "Not slop" belongs here: no neon cyberpunk, no glowing brains, no code rain, no lens-flare soup, no generic particle nebulae, no imitation of a real product's interface.
- **Palette.** Named roles with hex values: one ink/background, one paper/surface, one signal colour that owns every highlight, at most one rare accent used by exactly one moment. Record which values are allowed to bloom.
- **Typography.** Each family and its job (lyric voice, machine voice, sacred or quoted register, hand-lettered voice). Layout discipline: grid, asymmetry, negative space, rules, where small labels sit next to big display type.
- **Motifs.** Numbered and each described as a design, not as a mood: the spark and its line, the mask, the counter, the field. Note where each first appears and where it pays off.
- **Plates.** One row per scene: id, time window, lyric line or instrumental, owner, one-line description. Times come from the aligned lyrics, never from guesswork.

**Lyric integration rule.** Every line must be readable and synced per word. Each plate integrates its line _graphically and differently_ — written by the pen, riding a curve, typed as tokens, stamped on a form, woven, masked — so the words are part of the image rather than subtitles on top. Default emphasis: the sung portion in the signal or bone colour, the unsung portion at 30–40% or as an outline. Keep text inside the title-safe area and clear of any HUD corners.

**Palette discipline carries the rhythm.** Let some plates invert to paper with ink lines so the edit alternates light and dark; keep the signal colour identical in both.

## 2. Alignment and analysis data

Do not hand-time a karaoke video. Produce three data sets once, then read them:

1. **Line-level lyrics** as the source of truth for wording (typographic quotes and apostrophes included).
2. **Word-level timings** from forced alignment of the vocal, cross-checked against a second recogniser; then spot-check the lines a listener would notice. Keep syllable timing only where it drives an effect.
3. **Musical structure**: tempo, beats, downbeats, sections, drum and vocal onsets, and loudness envelopes for the full mix and for stems.

The pipeline that produced these three sets is bundled at [`assets/lyric-alignment/`](../assets/lyric-alignment/): `align.py` (Demucs stems, CTC forced alignment, Whisper cross-check, word and syllable timings), `analyze.py` (tempo, beats, downbeats, sections, onsets, loudness envelopes) and the shared helpers around them. It pins its stack in `pyproject.toml` and `uv.lock` and needs a GPU-class environment for Demucs and Whisper, so treat it as an optional tier: read it for the method, and run it only when the user wants real alignment data and can install the dependencies. `pron.py` shows the display-token-to-pronunciation map that keeps acronyms and invented words alignable.

Then honour two rules in scene code:

- **Look lines up by content, never by hard-coded times.** `lyrics.get('sudden drop')` returning `words[3].start` survives a re-render, a re-master or a tempo correction; `t = 12.4` does not.
- **Snap the edit to the grid.** Cut on downbeats, land hits on kicks and snares, ease camera moves into downbeats. Windows that touch cut hard; overlaps crossfade only when the brief wants a dissolve. No floaty, generic screensaver motion: strong eases, holds, then snaps.

Carry a per-frame context into every scene rather than recomputing: time, local time, local progress, beat index, bar, beat phase, and the smoothed envelopes (rms, low, mid, high, vocal, drums, bass, other) plus decaying hit pulses.

## 3. The scene contract

Every scene is a module that returns a complete frame for any time `t`:

- **Deterministic.** Output is a pure function of `t`, the content and fixed seeds. No `Math.random()`, no `Date.now()`, no `performance.now()` for visuals. Seeded PRNGs and hashes only.
- **Full overwrite.** Each scene writes the whole frame; there is no accumulating canvas state between frames.
- **Stateful scenes are declared.** If a scene truly needs feedback (particles with trails, iterative buffers), mark it stateful, reset it on every seek, integrate with the frame delta, and let the engine fast-forward after a seek. Such a scene can only be exported with a fixed sampling count, so prefer stateless.
- **Bounded cost.** Budget a frame time in the low tens of milliseconds; precompute text outlines, glyph layouts and geometry in `init()`, not per frame. Limit how many 2D layers you upload per scene (two or three).
- **Shared typography helpers.** Layout text glyph by glyph with the font's own kerning. Never measure a slice of a string to place a word drawn in pieces: that drops the kern between the pieces. Adjacent runs in different faces or sizes have no kerning between them, so set those gaps by eye.

## 4. Sampling and motion blur

The exporter averages several sub-frames per output frame, in arbitrary order, to make motion blur:

- Sub-frames may be rendered out of order, so any scene state must be reproducible from `t` alone.
- Exposure must be a function of the sub-frame offset, not of wall-clock time.
- Encoder and browser failures must leave the previous output file untouched; write to a temporary path and publish atomically.

## 5. Output scale

If you offer a 2× (or 4K) export, keep all layout in logical pixels and scale only the render targets:

- Convert physical fragment coordinates to logical ones before using them with logical sizes.
- Make hairline and derivative-based effects use physical pixels deliberately, so a 1-pixel line stays 1 logical pixel and gets sharper rather than thinner at 2×.
- Check the same frame at both scales: downscaled, the 4K frame must look like the 1× frame, only sharper.

## 6. Verification before delivery

- **Stills at chosen times** are the main way to check work: render a handful of key times, then open the images and look at them.
- **Contact sheets** over a time range show whether the whole plate holds up; **frame strips** around the fastest moves show whether the motion is real.
- **Compare both scales** when a 2× export is offered.
- **Check the loop.** If the brief asks for one, render the first and last frame and compare them, and make the closing plate return to the opening composition.
- Confirm that every lyric line is fully readable in at least one frame, that no word highlights before its sung time, and that no text sits under the HUD safe areas.

## 7. Boundaries

- Use supplied or licensed audio. Keep the track, the vocal stems and any analysis artefacts local to the project; do not commit them to a shared skill.
- Do not imitate a real product's interface, a person's likeness, or an existing artwork as a scene's design. Describe what the scene is doing in your report instead.
- Report the alignment method and any lines you could not verify.
