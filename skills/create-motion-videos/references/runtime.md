# Runtime, rendering and audio

## Contents

1. Prepare a writable runtime
2. Project contract
3. Choose the exporter
4. Voice, music, captions and muxing
5. Reuse and portability

## 1. Prepare a writable runtime

Set `SKILL_DIR` to the folder containing SKILL.md. Use task-specific variables; never overwrite HOME or CODEX_HOME. Keep installed skill files read-only.

```sh
python3 "$SKILL_DIR/scripts/prepare_runtime.py" "$WORK_DIR/motion-runtime"
```

This verifies bundled hashes and copies the pinned library. It installs nothing. Nonempty unrelated destinations are rejected; use `--reuse` for a matching runtime.

With Node 20+, FFmpeg and appropriate Python already available, install only necessary local tiers. The strict exporter needs FFmpeg's `-fps_mode` option: FFmpeg 7.0.2 was verified during this migration, while system FFmpeg 4.4 could not encode. Select a compatible local binary through `FFMPEG` when necessary; do not mistake a successful browser capture for a successful video export.

```sh
# npm dependencies and headless Chromium only.
python3 "$SKILL_DIR/scripts/prepare_runtime.py" "$WORK_DIR/motion-runtime" --reuse --install render
# Add Python audio/image processing.
python3 "$SKILL_DIR/scripts/prepare_runtime.py" "$WORK_DIR/motion-runtime" --reuse --install core
# Add offline TTS, speech checks and downloaded Kokoro model.
python3 "$SKILL_DIR/scripts/prepare_runtime.py" "$WORK_DIR/motion-runtime" --reuse --install voice
# Add optional physical-model music dependencies.
python3 "$SKILL_DIR/scripts/prepare_runtime.py" "$WORK_DIR/motion-runtime" --reuse --install music
```

The voice tier needs Python 3.11–3.13; select an interpreter with `--python /path/to/python3.12`. The helper does not install system tools, reset git, or update upstream. Follow host network/install permissions. Report a missing system tool specifically; do not substitute a paid service without authorization.

For existing supported Chromium, use `--skip-browser-download` and set `PLAYWRIGHT_CHROME` when rendering. The strict renderer can also use runtime-owned Playwright; read its reference/help. Record departures from pinned dependency versions. Do not rewrite the lockfile to conceal an installation failure.

The portable wrapper installs Python tiers from this package's pinned `requirements/core.txt`, `requirements/voice.txt`, and `requirements/music.txt`, not the upstream unpinned manifests. The upstream files remain unchanged for hash verification. The voice tier supplies offline Kokoro/Whisper after model downloads and does not install the optional online EdgeTTS provider. These are direct dependency pins; platform-specific transitive dependencies and model downloads are not a fully locked offline runtime. Record the resolved environment when reproducing a film.

Instrument samples and other large assets are optional. Inspect `core/audio/INSTRUMENTS.md`, the chosen CREDITS, and `tools/assets.json` before running `sh tools/fetch.sh instruments <library>` in the writable runtime. Prefer synthesis when it suits the film and avoids needless downloads.

## 2. Project contract

Create an original-film starter with selected style resources:

```sh
python3 "$SKILL_DIR/scripts/prepare_project.py" "$FILM_DIR" --style whiteboard
```

The helper copies the selected demo browser resource tree into `style/` (excluding repository-bound `tools/` and `build.sh`) and creates a separate starter `index.html`. It accepts an empty destination or one containing only `TREATMENT.md`, preserving the treatment. It never merges different styles' engine or font directories. Use the demo only as a technical reference after writing the original treatment. Import modules via `./style/engine/...`; relative ES module imports and CSS URLs then retain their original locations. **Plain `fetch('fonts/...')`, image src assignments and loader strings are relative to the page, not the JS module.** Rebase those to `./style/fonts/...`, or use `new URL('./fonts/...', import.meta.url)` from the correct module. Do not assume copying a module alone makes its assets available.

Serve through the Lemo server with `--library` pointing to the prepared runtime. Root-relative `/core/`, `/styles/`, and `/node_modules/` continue to resolve there. Read `font-replacements.md` for bundled font sources and supported scripts. Font notices stay with copied source. Runtime copies made before this patch must be recreated: runtime reuse checks the bundle manifest as well as the upstream commit.

Run static preflight on the actual composition before browser checks:

```sh
python3 "$SKILL_DIR/scripts/audit_assets.py" "$FILM_DIR" \
  --library "$WORK_DIR/motion-runtime" --report "$FILM_DIR/assets-check.json" --strict
```

This inspects literal URLs, module imports and glTF resources. It reports dynamic paths separately; it cannot establish their validity. Unused reference demos in `style/` may still reference original narration/media not tracked upstream. Remove unused reference files from the deliverable, or audit the composition's own source folder separately; never suppress missing assets that the composition actually loads. The strict browser renderer remains the final check for requested assets.

Keep a separate film folder with index.html, content/timeline data and local assets. Use `/core/...` or `/node_modules/...` for shared library modules. The Lemo server mounts external film folders under `/@film/`; use project-relative URLs for their own assets.

```js
window.DUR = durationInSeconds;
window.render = async (t) => {
  // Set/draw complete state for t; await necessary media decoding.
};
window.READY = true; // Only after required fonts and assets load.
```

For DOM UI, implement `window.seek(t)` and expose `window.render = t => window.seek(t)` for upstream tools. Return the Promise. Optional EV cues, SUBS and TEXTS(t) support upstream audio/text checks.

The starter provides a small pure-time loop with no remote media. Replace its content, visual composition and timeline with the user's film. It is not a finished product-film template.

## 3. Choose the exporter

### Strict renderer

Use scripts/render.mjs for Canvas/DOM, asynchronous seeking, local-only rendering and optional temporal sampling. Read [browser-renderer.md](browser-renderer.md) for exact flags.

```sh
node "$SKILL_DIR/scripts/render.mjs" "$FILM_DIR" \
  --runtime "$WORK_DIR/motion-runtime" --library "$WORK_DIR/motion-runtime" \
  --check-only --times 0,1,2 --stills "$FILM_DIR/review"

node "$SKILL_DIR/scripts/render.mjs" "$FILM_DIR" \
  --runtime "$WORK_DIR/motion-runtime" --library "$WORK_DIR/motion-runtime" \
  --size 1440x1440 --fps 60 --samples 4 --shutter 0.5 \
  --out "$FILM_DIR/out/picture.mp4"
```

Select real scene times for checks. The output is picture only; mix/mux sound separately. Localize a blocked external asset instead of disabling the restriction to hide a local-only project's missing dependency.

### Original Lemo renderer

Use the upstream tools when a selected engine/build fits them. From the writable runtime, with an absolute film path:

```sh
node core/render/still.mjs "$FILM_DIR" 1.5 8 15 --out "$FILM_DIR/review"
node core/render/video.mjs "$FILM_DIR" --fps 24 --workers 3 \
  --size 1920x1080 --out "$FILM_DIR/out/picture.mp4"
```

It awaits asynchronous render(t) but captures one sample per output frame. Higher fps alone adds no temporal blur. It does not enforce a network allowlist and may only warn about missing optional media. The strict renderer addresses those cases; do not imply every upstream engine already passes its checks.

Use each style's frame rate: some styles specify 30 or 60 fps. Distinguish stepped character motion from a smooth camera. Software-rendered 3D/shaders can be slow.

## 4. Voice, music, captions and muxing

From the writable runtime, after installing the needed tier:

```sh
.venv/bin/python core/tts/tts.py "$FILM_DIR/lines.json" "$FILM_DIR/voices"
.venv/bin/python core/tts/asr_check.py "$FILM_DIR/lines.json" "$FILM_DIR/voices"
node core/render/events.mjs "$FILM_DIR" --out "$FILM_DIR/events.json"
node core/render/readcheck.mjs "$FILM_DIR"
```

Read core/README.md for schemas. Use the actual language/voice pairing. Kokoro runs offline after downloads; EdgeTTS is online. Supplied recordings can be aligned. Do not claim a speech check for an unsupported ASR language.

Write the project's score/foley/mix script from its cue map. core/audio supplies primitives, not an automatically composed score. Align all layers to the picture timeline.

```sh
sh core/render/mux.sh "$FILM_DIR/out/picture.mp4" "$FILM_DIR/out/mix.wav" \
  "$FILM_DIR/final.mp4" 60 0
```

Use the actual fps and appropriate grain; Swiss/clean UI normally use none. The mux processes loudness. Check output with ffprobe and playback when available. Requested narration/music must exist in the final file.

## 5. Reuse and portability

Exclude installed dependencies from the deliverable source archive. Record the upstream commit and a documented MOTION_RUNTIME path in build scripts. Package source, required assets and licenses rather than a private skill-installation path.

Do not update the collection mid-film. For an intentional skill update, compare snapshots, rebuild catalogue/hashes, preserve twoclipping additions, run verify_bundle.py and render representative samples. Save through the host's approved persistence mechanism.
