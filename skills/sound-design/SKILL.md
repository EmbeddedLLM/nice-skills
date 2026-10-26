---
name: sound-design
description: Create local procedural sound effects and align them to video or interface cues, or plan and verify a soundtrack mix. Use for UI clicks, hits, swells, plucks, transitions, and cue sheets; not for speech generation or claiming an automated score proves audio quality.
license: MIT; see LICENSE-earshot.txt and SOURCES.md
---

# Local sound design

The bundled Earshot synthesis tier renders 237 presets without recordings, model weights, credentials, or network access. Install the exact NumPy/SciPy/Numba versions in [requirements.txt](requirements.txt) into the project's environment. Resolve scripts from this directory; run outputs in the user's project. Initial package installation needs network access if packages are uncached.

## Choose and render

Identify the audible event, material, action, and intended envelope: for example, "a short soft UI pop on a completed selection." Choose effects around important events; continuous ornament obscures speech and weakens emphasis.

```sh
python scripts/sfx.py list --query ui_pop
python scripts/sfx.py render ui_pop/soft pop.wav
```

Use an ID returned by `list` (the example ID must be checked against the catalog). The default seed reproduces the stored preset; `--seed 7` produces a variation. Output is stereo 48 kHz PCM16 WAV and a JSON report. Existing outputs are refused unless `--force` is supplied. No implicit playback, upload, or account access occurs.

## Place cues

A cue sheet declares the total duration and effect anchors in seconds. `align: peak` aligns the actual rendered waveform's largest sample peak; `start` aligns its first sample. This is a precise signal anchor, not a claim about perceived onset.

```json
{ "duration": 4, "cues": [{ "id": "cut_hit/sub", "at": 1, "align": "peak", "gain_db": -6 }] }
```

```sh
python scripts/sfx.py mix cues.json effects.wav
```

The mixer preserves tails, rejects cues outside the timeline and clipping, and leaves existing output untouched on failure. Add pre-roll/tail room or lower cue gain instead of silently truncating or normalizing the mix. Reports keep the chosen seeds and actual anchor times. The helper accepts local JSON and writes only the requested WAV; invalid input returns a nonzero exit code.

Read [mixing and verification](references/mixing.md) for music, speech, external recordings, and final delivery. Deliver WAVs, the cue sheet, source notices, and measured limits. Listen or request human playback review before claiming subjective quality. Automated measurements establish technical properties, not taste, realism, provenance, or intelligibility.
