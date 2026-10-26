# Production interchange contract (version 1)

Keep this record in the editable project, not in the installed skill. It describes useful interchange fields without requiring another skill, a common schema implementation, or a particular editor. Engines retain their own native project formats; convert explicitly at their boundary.

- `brief`: requested deliverable, audience, dimensions in pixels, fps, duration in seconds, master clock (`music`, `narration`, or `timeline`), and loop intent.
- `assets`: job-relative path, SHA-256, origin URL or supplied-file identity, license/permission evidence, author/credit, and permitted external transfers. Keep private records local unless transfer is authorized; never record secrets or signed URLs.
- `script` and `storyboard`: claims with source references; scenes with start/end seconds, purpose, visual/camera action, text, transition, and audio cue. Preserve accepted sections during revisions.
- `timing`: units explicitly `seconds`; audio path and hash; alignment method and provenance (`provider`, `forced-alignment`, `manual`, `estimated`, or `draft`). Word/phrase cues have text, start, end; beats have index, time, and measured/derived provenance; note events have pitch, start, duration, velocity, and source. BPM alone is not a measured beat map: record the track offset and any tempo changes.
- `render`: backend and exact dependency versions, seed, dimensions/fps, shutter/subframes, audio mapping/offset, output paths, and elapsed render time.
- `qa`: measured duration, stream layout, full decode outcome, loudness/peaks, timing/bounds findings, final-encode contact sheet, reviewed frames/time ranges, and unresolved issues. Record machine results separately from visual/audio review. Only loops include a wraparound continuity result.

Estimated timings cannot be relabeled as measured or aligned. Supplied-audio assembly can normalize/resample: retain source and rendered-audio hashes separately. A visual restyle reuses the accepted narration; a narrative rewrite creates a new audio revision. When preserving original presenter speech, keep video and audio source offsets aligned.

At delivery, include editable source and required local assets, caption files, timing data, provenance, and the actual QA evidence. No cross-skill runtime import or symlink is part of this contract.
