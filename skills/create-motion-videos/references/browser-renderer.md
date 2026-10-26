# Deterministic local browser export

`scripts/render.mjs` exports a local HTML scene to a **silent MP4**. It uses Playwright Chromium and FFmpeg already present in a runtime; it never installs dependencies or calls a model. Add narration/music later with the local audio workflow. A browser preview with sound is not an audio export.

## Prepare a film and runtime

Copy `assets/browser-starter/index.html` to a new project folder and edit that copy. The starter is a six-second DOM/CSS scene with a JavaScript clock, no external assets, and a closed-form spring. Its preview controls are automatically hidden during capture. It is an original starter, not a copy of a creator's published film.

Use the skill's `scripts/prepare_runtime.py` for a writable copy of the pinned Lemo tools. `--install render` installs project dependencies and the Playwright browser when that installation is authorized. Node 20+ and FFmpeg must already exist; the renderer does not install system tools. `--runtime` can also name an existing dependency directory or its `node_modules`. `PLAYWRIGHT_CHROME` can point to an existing compatible Chromium executable.

```sh
node scripts/render.mjs /absolute/path/to/film \
  --runtime /absolute/path/to/runtime \
  --check-only --times 0,1.2,3.7,5.8 \
  --stills /absolute/path/to/film/review

node scripts/render.mjs /absolute/path/to/film \
  --runtime /absolute/path/to/runtime \
  --fps 30 --size 1920x1080 \
  --out /absolute/path/to/film/picture.mp4
```

Run commands with the skill directory as the working directory, or use the absolute path to `scripts/render.mjs`. Quote paths containing spaces. The source/runtime folders are not modified by rendering. Output files are not overwritten unless `--overwrite` is explicit.

If the runtime contains `core/render/serve.mjs`, it also supplies the `/core/` library. Otherwise the bundled `assets/lemo` library is used. `--library` overrides that choice. Lemo's local server mounts an outside project at `/@film/`; project-relative assets work there, and `/core/...` remains available. `/node_modules/...` resolves against the selected existing dependency directory.

## Scene contract

```js
window.DUR = 12; // total scene length in seconds
window.READY = false; // optional, but recommended during initialization

window.seek = async (t) => {
  // Set the complete DOM/SVG scene state from t, independently of previous calls.
  // Await media seeking or any other asynchronous work needed to finish this frame.
};
// Alternatively: window.render = async t => { /* draw the complete Canvas frame */ };

await document.fonts.ready;
// Load/decode all other assets here.
window.READY = true;
```

If both functions exist, `seek(t)` takes precedence. Returned promises are awaited. A `READY` flag that exists must become `true`; a missing flag is allowed once the drawing function exists. The renderer waits for fonts and HTML image decoding as well. Canvas textures, video seeks and asynchronous custom loaders remain the scene's responsibility: include them in readiness or the drawing promise.

Do not use accumulated physics state, uncontrolled CSS animations, unseeded random values or wall-clock time inside the scene. A closed-form spring or seeded noise is suitable. CSS keyframes can be used if their animations are explicitly paused and their `currentTime` is set from `t`. The renderer does not automatically fast-forward or disable CSS animations, because that would change the intended frame.

Disable preview timers and playback when `window.__MOTION_CAPTURE__ === true` or the `capture` query parameter exists. The renderer supplies both before capture. Preview controls should not appear in the exported frame.

## Determinism and review

`--check-only` captures exact PNGs at selected absolute timestamps, seeks through those timestamps in reverse, then repeats the reverse sequence in a fresh browser context. All three passes must produce identical SHA-256 hashes at each time. `--stills DIR` saves the baseline PNGs and a `check.json` report. It is a sampled repeatability check, not proof about every frame, factual accuracy or visual quality.

Review the stills for clipped text, missing elements, layout and incorrect content. After export, also review the actual video and audio mix: sampled stills cannot reveal every timing or narration issue.

`--from` and `--duration` select a clip. Check timestamps are absolute scene times within that clip, excluding its endpoint. Video uses only complete frames: `floor(duration × fps)`. Thus a duration that is not aligned to a frame boundary is shortened by less than one frame. The command prints requested and encoded duration and the exact frame count.

## Optional temporal supersampling

```sh
node scripts/render.mjs /absolute/path/to/film \
  --runtime /absolute/path/to/runtime \
  --fps 30 --samples 4 --shutter 0.5 \
  --out /absolute/path/to/film/picture-blur.mp4
```

With one sample, output frame `f` is captured at `start + f/fps`. With `S > 1` samples and shutter fraction `q`, sample `s` is captured at:

`start + (f + q × (s + 0.5) / S) / fps`, for `s = 0…S−1`.

This uses equal midpoint samples within a forward exposure interval starting at the frame timestamp. Four samples with `q=0.5` cover half a frame interval. It does not center the exposure around the nominal timestamp.

FFmpeg receives `S × fps` input samples. The filter averages the most recent `S` RGB frames with equal weights, **selects only input indices `S−1, 2S−1, 3S−1, …`**, and resets output timestamps to `N/fps`. Therefore each output frame averages exactly its own sample group; adjacent output frames are not mixed together. Merely applying a moving `tmix` and changing output FPS would not establish that grouping. Averaging is in encoded RGB channel space, not a physical linear-light shutter simulation. More samples increase capture work proportionally.

## Failure behavior and practical limits

- HTTP errors, failed requests, page errors, console errors and missing dependency files stop the run. Browser favicon requests receive an empty response because they do not contribute to the film.
- Page requests outside the local serving origin are blocked by default. WebSockets are blocked in that mode, and service workers are disabled. `--allow-network` explicitly relaxes the page-request rule. This is a capture policy, not an operating-system security sandbox for arbitrary code.
- Download fonts, images, models and sample packs before capture. Avoid using external services merely because an asset is missing.
- FFmpeg writes into a fresh temporary directory beside the destination. The named MP4 is created only after successful encoding and final error checks. Failures/signals clean up this process's browser, server, encoder and temporary output. Requested diagnostic stills remain available.
- A missing Playwright browser is a setup failure, not evidence that the scene is broken. Use an existing browser path or complete the approved runtime setup; do not silently substitute an online renderer.
- MP4 encoding here requires FFmpeg with `libx264`, `tmix`, `select` and the other referenced filters. Actual speed and browser/GPU compatibility depend on the environment. This wrapper does not promise a rendering benchmark or universal platform support.

Use `node scripts/render.mjs --help` for all flags. For a small validation clip, use `--duration 2 --size 320x180` before a full-resolution export.

Capture flushes DOM layout/compositor frames and disables partial raster caching. Avoid scale transforms on live text in the minimal starter: browser raster caching can make exact pixels depend on seek order. A failed check saves a mismatch PNG alongside baseline stills when --stills is supplied. Do not weaken hash equality to hide scene-state errors.
