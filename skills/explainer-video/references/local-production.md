# Local production

Use Python 3.10 or later and FFmpeg/ffprobe with the `libx264` encoder and AAC support. Finalization also needs Bash, jq, and ordinary Unix utilities. No Python packages, Node runtime, paid account, or network calls are needed. Install system tools through the host's approved mechanism; versions of FFmpeg shipped by different systems may encode slightly different bytes. Tests assert decoded behavior rather than byte identity.

Create a separate project, with a `story/` directory containing `script.md` and a supplied recording. The script format is intentionally small, not arbitrary YAML: metadata is `key: value`, chapters begin with `## key | Display title`, and each following text line represents one spoken line. Use the actual transcript, including names and numbers. Example:

```markdown
---
title: A queue absorbs a burst
subtitle: A simplified example
---

## burst | Requests arrive together

Three requests arrive while one worker is busy.

## waiting | The queue preserves order

The remaining requests wait until the worker is ready.
```

Check the script without producing audio, then import the recording:

```sh
python3 "$SKILL_DIR/scripts/story.py" "$PROJECT/story" --check
python3 "$SKILL_DIR/scripts/story.py" "$PROJECT/story" --audio "$PROJECT/recording.wav"
python3 "$SKILL_DIR/scripts/srt.py" "$PROJECT/story/story.json" "$PROJECT/captions.srt"
```

`story.py` writes resampled mono `story/audio/narration.wav` and `story/story.json` containing the measured duration, chapter boundaries, lines, and estimated word times. It can replace these derived files: keep an accepted revision before regenerating them. Pointing `--audio` at the existing derived recording reuses its bytes without conversion. Keep an original recording outside the generated audio directory so later revisions cannot replace your only copy. A failed local import preserves the accepted derived recording and metadata. It accepts FFmpeg-decodable audio/video files; only the audio is used. Too few pauses trigger a warning and proportional line timing. Review and correct the JSON/captions against the recording; short caption intervals are retained rather than extended into neighboring speech, and non-positive intervals fail for correction; timing is never a claim of forced alignment. The timing estimator is oriented toward English and CJK text; other languages need particular care.

`--dry` makes explicitly silent drafts with estimated durations. The local delivery renderer rejects stories marked `draft`. Running without an audio mode fails even if a provider API key is present. `--audio`, `--dry`, and `--tts-provider` are mutually exclusive.

Create actual scene images, then write `scenes.json` in the project. Image paths are relative to that JSON file. For an example story whose measured duration is exactly six seconds:

```json
{
  "width": 1280,
  "height": 720,
  "fps": 30,
  "scenes": [
    { "image": "scenes/arrival.png", "duration": 2.5 },
    { "image": "scenes/waiting.png", "duration": 3.5 }
  ]
}
```

Set durations from the accepted story and actual recording, not these example values. Durations must be positive and finite; the total must match `story.duration` within one frame and cover all narration. Dimensions must be positive even integers; FPS is a positive integer. Scene boundaries round up to output frames; each scene must occupy at least one frame, and the final video can extend by less than one frame. PNG, JPEG, WebP, and PPM images are supported. Images are fitted inside the frame with black padding when their aspect differs. Use matching aspect ratios when padding is undesirable. An optional recap may extend beyond narration; the renderer pads the audio with silence during that ending.

```sh
python3 "$SKILL_DIR/scripts/render_story.py" \
  "$PROJECT/story/story.json" "$PROJECT/scenes.json" "$PROJECT/render.mp4"
bash "$SKILL_DIR/scripts/finalize_delivery.sh" \
  "$PROJECT/render.mp4" "$PROJECT/delivery" explainer
```

The renderer writes an H.264/AAC MP4, checks that both streams fully decode, and publishes it only after success. It refuses existing output paths; use a new revision name for rerenders. Invalid images, missing narration, inconsistent timing, silent draft state, missing tools, or encoding failures return nonzero and leave no new output. It does not validate whether speech matches the transcript or whether the audio is silent; the finalizer rejects silent/unmeasurable narration.

The finalizer uses Python 3 for exclusive publication, refuses existing deliverables (including dangling symbolic links), and writes `explainer-master.mp4`, `explainer-share.mp4`, `explainer-contact-sheet.png`, and `explainer-delivery-report.json`. It measures final loudness, checks complete decoding, and records black/frozen-frame events. Still scenes intentionally produce freeze events; review them in context. It defaults to −16 LUFS and can use `PROGRAM_LUFS` between −40 and −5. It checks the encodes before publishing files, with the report last as a completion marker. If another process creates a deliverable during encoding, publication fails without replacing that file; earlier files from this attempt can remain, so inspect them and choose a new output stem before retrying. Its report's `verified` status describes technical checks only. Review visuals, listen to the sound, and record those human/agent checks separately. Very short clips may not provide reliable loudness measurements; do not weaken checks merely to label a draft complete.

For animated explainers, a separately installed renderer/editor can consume the same locked audio, scene durations, and source records. Its prerequisites and licenses are separate. No particular backend, sibling skill, cloud account, or paid generation service is required by this package.
