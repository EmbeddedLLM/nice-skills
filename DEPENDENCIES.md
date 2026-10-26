# Software and dependencies

This page lists the local software and packages needed to run each published skill, and the optional extras that unlock additional routes. Install only what the selected skill needs; every skill is independently usable.

No skill requires a paid model-provider API, hosted artifact platform, or paid image-generation service. Two video skills can optionally call a paid speech or presenter service; those routes are explicit opt-ins with complete local alternatives.

The pins inside each skill directory (`requirements*.txt`, `package-lock.json`) are authoritative. The versions quoted here describe the tested environment, not an additional constraint.

## Interpreters and hosts

| Component | Minimum | Tested | Notes |
| --- | --- | --- | --- |
| Python | 3.10 | 3.12 in CI | Most helpers need only the standard library. `vector-art` needs Python 3.12+; presenter generation planning needs 3.12; the motion voice tier supports 3.11–3.13 |
| Node.js | 18 | 24 in CI | `pdf` JS helpers and the `security-audit` validators need 18+, the motion runtime declares Node 20+, and `design-taste` needs 22+. Every package directory installs from its own lockfile with `npm ci` |
| npm | bundled with Node.js | — | Needed for the slide, PDF, equation, cartoon-kit, and motion Node packages |
| Browser | current Chrome, Chromium, or Edge | Playwright 1.58.0 Chromium | Used directly for previews, the `design-taste` inspector, and the motion cartoon kit, and by Playwright for automation, rendering, and conversion |

Python packages belong in a project-local virtual environment, and Node packages in a writable copy of the owning directory (`npm ci` writes `node_modules`). Installed skill directories are treated as read-only.

## Command-line tools

| Tool | Minimum | Tested | Used by | Purpose |
| --- | --- | --- | --- | --- |
| Poppler (`pdftoppm`, `pdfinfo`, `pdftotext`, `pdffonts`) | distribution package | Ubuntu 24.04 | documents, pdf, slides | Rendered page review, thumbnails, text extraction |
| LibreOffice (`soffice`) | distribution package | Ubuntu 24.04 | documents, pdf, slides, spreadsheets | Writer rendering and revision acceptance, Impress thumbnails, Calc recalculation, Office-to-PDF conversion |
| FFmpeg / ffprobe | 6.1 | 7.0.2 verified | create-motion-videos, explainer-video, presenter-video, gif-creator (optional) | Encoding, muxing, loudness checks, contact sheets. Needs `libx264`, AAC, `loudnorm`, and image/tile filters; the motion strict exporter needs `-fps_mode` |
| jq | 1.7 | Ubuntu 24.04 | explainer-video, presenter-video | Delivery finalization reports |
| Bash and POSIX utilities | — | — | explainer-video, presenter-video | Delivery finalizers; the presenter provider ledger also needs POSIX file locks |
| Git | current release | — | review-agent | Reading the requested commit, branch, or diff |
| Tesseract with language data | distribution package | — | pdf OCR tier | Local OCR through `ocrmypdf` |
| Pandoc | current release | — | pdf Markdown conversion tier | Markdown-to-PDF input |
| TeX (`latexmk` and packages) | current release | — | pdf TeX tier | TeX-to-PDF input |
| Fonts | DejaVu Sans/Serif available | — | canvas-design, documents, slides, vector-art | Text measurement and rendering. `slides` bundles DejaVu fonts; other skills use an installed licensed font |
| `fc-list`/fontconfig (optional) | distribution package | — | canvas-design, vector-art | Discover installed fonts before measuring text |

System package names differ by distribution. The skills invoke the executable names above and require them on `PATH`; substitute an alternative binary path through the documented environment variable where a skill provides one (for example `FFMPEG`).

## Skills

| Skill | Required | Optional |
| --- | --- | --- |
| [algorithmic-art](skills/algorithmic-art/SKILL.md) | Browser for Canvas/SVG output | p5.js (pinned or bundled locally); Openverse asset search |
| [canvas-design](skills/canvas-design/SKILL.md) | One local drawing route: Pillow, SVG/CairoSVG, or ReportLab; fonts | Poppler to rasterize a PDF for review; Openverse asset search |
| [create-motion-videos](skills/create-motion-videos/SKILL.md) | Node 20+, FFmpeg, Python 3.10+ (standard library), Chromium installed into a prepared runtime | Core audio/image tier, offline TTS/ASR voice tier, music tier, instrument samples, `hand-painted-cartoon` kit packages, lyric-alignment pipeline, Openverse asset search |
| [deep-research](skills/deep-research/SKILL.md) | Source material and the host's search tooling | A browser for dynamic pages and discussion threads; network access for live research |
| [design-taste](skills/design-taste/SKILL.md) | Node 22+ and an installed Chrome, Edge, or Chromium for the inspector; the scripts install nothing | Network access for the anonymous asset search; `lint.mjs` alone runs on Node 18+ |
| [doc-coauthoring](skills/doc-coauthoring/SKILL.md) | Text editing in the destination format | An independent reader, if authorized |
| [documents](skills/documents/SKILL.md) | Python 3.10+ and `requirements.txt`; LibreOffice Writer and Poppler for rendered review | `scripts/requirements-office.txt` for OOXML checks; `equation-runtime` Node packages for rendered equations |
| [explainer-video](skills/explainer-video/SKILL.md) | Python 3.10+ (standard library), FFmpeg/ffprobe, Bash, jq | MiniMax TTS (paid, explicitly selected) or another local speech tool |
| [frontend-design](skills/frontend-design/SKILL.md) | Source editing and a browser; the project's own stack for existing code | Python 3 standard-library helpers for standalone export; Openverse asset search |
| [gif-creator](skills/gif-creator/SKILL.md) | Pillow from `requirements.txt` | FFmpeg for conversion; Openverse asset search |
| [mcp-builder](skills/mcp-builder/SKILL.md) | The project's Python or TypeScript MCP SDK and a local test client | MCP Inspector; online specification and SDK documentation |
| [pdf](skills/pdf/SKILL.md) | Python 3.10+ and `requirements.txt`; Poppler | Redaction, browser-conversion, OCR, and form tiers; LibreOffice, Pandoc, or TeX for conversion; Node 18+ with `js/` packages |
| [presenter-video](skills/presenter-video/SKILL.md) | Python 3, Bash, FFmpeg/ffprobe, jq, POSIX tools | Python 3.12 for generation planning; an authorized presenter-generation backend and its credentials |
| [resolve-recipients](skills/resolve-recipients/SKILL.md) | A supplied roster/history or authorized directory tools | — |
| [review-agent](skills/review-agent/SKILL.md) | Git and read access to the change | The project's own test and lint commands |
| [security-audit](skills/security-audit/SKILL.md) | Source access, and Node.js 18+ to run the two report validators | A local sandbox for executing a target |
| [skill-creator](skills/skill-creator/SKILL.md) | Python 3; PyYAML from `requirements.txt` for the validator | — |
| [slides](skills/slides/SKILL.md) | Python 3.10+ and `requirements.txt`; LibreOffice Impress and Poppler | PptxGenJS route with `pptxgenjs_helpers`; bundled DejaVu fonts |
| [spreadsheets](skills/spreadsheets/SKILL.md) | openpyxl from `requirements.txt` | LibreOffice Calc for recalculation checks |
| [theme-factory](skills/theme-factory/SKILL.md) | Python 3 standard library | A browser to preview the bundled HTML guide |
| [vector-art](skills/vector-art/SKILL.md) | Python 3.12+, `requirements.txt`, Playwright Chromium | `fontTools` text outlining with an installed licensed font |
| [webapp-testing](skills/webapp-testing/SKILL.md) | The project's browser tests, or Python Playwright and Chromium | A local dev server managed by `scripts/with_server.py` |

## Python packages

Install with `python -m pip install -r <manifest>` inside a project-local virtual environment. `uv pip install -r <manifest>` installs the same pins; the sample container uses uv.

| Manifest | Packages | Skill |
| --- | --- | --- |
| `skills/documents/requirements.txt` | python-docx 1.2.0, pdf2image 1.17.0, openpyxl 3.1.5, Pillow 11.3.0, lxml 6.0.2, defusedxml 0.7.1 | documents |
| `skills/documents/scripts/requirements-office.txt` | defusedxml 0.7.1, lxml 6.0.2 | documents (OOXML checks only) |
| `skills/pdf/requirements.txt` | pypdf 6.1.3, pdfplumber 0.11.7, pypdfium2 4.30.0, reportlab 4.4.4, Pillow 11.3.0, openpyxl 3.1.5 | pdf |
| `skills/pdf/requirements-redaction.txt` | PyMuPDF 1.26.5 | pdf (redaction) |
| `skills/pdf/requirements-browser.txt` | playwright 1.58.0 | pdf (HTML-to-PDF) |
| `skills/pdf/requirements-ocr.txt` | ocrmypdf 16.11.1 | pdf (OCR) |
| `skills/pdf/scripts/requirements-forms.txt` | pypdf 6.1.3, pdfplumber 0.11.7, Pillow 11.3.0 | pdf (form field mapping) |
| `skills/slides/requirements.txt` | python-pptx 1.0.2, Pillow 11.3.0, lxml 6.0.2, defusedxml 0.7.1 | slides |
| `skills/slides/scripts/requirements-office.txt` | defusedxml 0.7.1, lxml 6.0.2, Pillow 11.3.0 | slides (package tools) |
| `skills/spreadsheets/requirements.txt` | openpyxl 3.1.5 | spreadsheets |
| `skills/gif-creator/requirements.txt` | Pillow 11.3.0 | gif-creator |
| `skills/vector-art/requirements.txt` | Pillow 11.3.0, lxml 6.0.2, playwright 1.58.0, fonttools 4.60.1 | vector-art |
| `skills/webapp-testing/requirements.txt` | playwright 1.58.0 | webapp-testing |
| `skills/skill-creator/requirements.txt` | PyYAML 6.0.3 | skill-creator |
| `skills/create-motion-videos/requirements/core.txt` | numpy 2.2.6, scipy 1.15.3, soundfile 0.13.1, soxr 0.5.0.post1, Pillow 11.3.0 | create-motion-videos (local audio and images) |
| `skills/create-motion-videos/requirements/voice.txt` | kokoro-onnx 0.4.9, faster-whisper 1.2.0, requests 2.34.2 | create-motion-videos (offline speech and speech checks) |
| `skills/create-motion-videos/requirements/music.txt` | numba 0.61.2 | create-motion-videos (optional physical-model music) |

Playwright does not download a browser with `pip`. After installing a Playwright-facing manifest, run `python -m playwright install chromium` if no compatible browser is present. `vector-art`, `webapp-testing`, and the PDF browser tier each pin Playwright 1.58.0.

The motion tiers are installed into a writable runtime rather than into the skill directory:

```sh
python3 skills/create-motion-videos/scripts/prepare_runtime.py "$WORK_DIR/motion-runtime" --install render
python3 skills/create-motion-videos/scripts/prepare_runtime.py "$WORK_DIR/motion-runtime" --reuse --install core
```

The bundled lyric-alignment asset is a separate optional pipeline with its own `pyproject.toml` and `uv.lock` (Demucs, Whisper, torch, and librosa). Its dependencies are intentionally per-project and are not part of the motion runtime; install them with `uv sync` only when a film needs real lyric alignment.

`--install render` adds the Node packages and Playwright Chromium; `core`, `voice`, and `music` add the matching Python tier. The voice tier also downloads the Kokoro and Whisper models on first use.

## Node packages

Install each directory with `npm ci` from a writable copy, or with `npm ci --prefix <dir>` from the repository root.

| Manifest | Packages | Skill |
| --- | --- | --- |
| `skills/pdf/js/package.json` | pdfjs-dist 4.10.38, pdf-lib 1.17.1 | pdf (extraction and form helpers) |
| `skills/slides/pptxgenjs_helpers/package.json` | pptxgenjs 4.0.1, skia-canvas 3.0.8, mathjax-full 3.2.2, prismjs 1.30.0, linebreak 1.1.0 | slides (PptxGenJS route) |
| `skills/documents/equation-runtime/package.json` | mathjax-full 3.2.2, sharp 0.34.3 | documents (rendered equations) |
| `skills/create-motion-videos/assets/lemo/package.json` | playwright-core ^1.63.0, three ^0.170.0 | create-motion-videos (installed by `prepare_runtime.py`) |
| `skills/create-motion-videos/assets/hand-painted-cartoon/package.json` | p5 ^2.3.3, p5.brush ^2.2.3, puppeteer-core ^25.11.0 | create-motion-videos (optional cartoon kit, installed with `npm ci`) |

## Network access and optional paid services

Network access is needed for initial package, browser, and model downloads, and for the optional routes below. Every skill has a local route that needs neither an account nor a paid API.

| Route | Skill | Requirement |
| --- | --- | --- |
| MiniMax text-to-speech | explainer-video | `--tts-provider minimax` plus existing authorization for text transfer, voice choice, and bounded cost |
| Generated presenter | presenter-video | An explicitly selected backend or adapter with its own credentials, transfer authorization, and cost limit. Generated planning tools never call a provider |
| Openverse asset search | create-motion-videos, slides, canvas-design, frontend-design, gif-creator | Anonymous network access; no account. Verified local assets and credits must be kept |
| Asset search | design-taste | Anonymous network access for `assets.mjs`; no API key |
| MCP specification and SDK documentation | mcp-builder | Online access when available; otherwise versioned local documentation |
| Live web research | deep-research | Search and browser access authorized in the host environment |

## Platform notes

- The workflows are exercised on Linux. LibreOffice, Poppler, and FFmpeg builds differ slightly between platforms, so verify rendered or encoded output locally instead of assuming identical results.
- `explainer-video` and `presenter-video` finalizers are Bash scripts. On Windows, run them under WSL or another POSIX shell.
- The presenter provider ledger uses POSIX file locks, and `webapp-testing`'s `with_server.py` manages POSIX process groups. On Windows, use the project's own runner instead.

## Container image

[Dockerfile](Dockerfile) builds a sample Ubuntu 24.04 environment containing every required and optional dependency above. It is a convenience for evaluating skills or reproducing the documented toolchain, not a way to distribute the repository.

```sh
docker build -t nice-skills:local .
docker run --rm -it -v "$PWD:/work" -w /work nice-skills:local
```

- The image uses a multi-stage build. Builder stages install the Python manifests with pinned uv 0.12.7 into `/opt/venv` and the Node lockfiles with `npm ci`; the runtime stage adds the command-line tools, Playwright 1.58.0 Chromium, and the skill Node packages.
- `uv` and `uvx` remain on `PATH` in the runtime stage with `/opt/venv` as the active Python environment, so project environments and the pinned manifests install the same way the image was built.
- The runtime stage exposes the pinned Chromium as `CHROME_PATH=/usr/local/bin/chromium`, a wrapper that adds `--no-sandbox` because containers block the browser sandbox; the `design-taste` inspector and the motion cartoon kit use it. The optional `hand-painted-cartoon` kit ships with its Node packages installed.
- The image has no GPU, so the cartoon renderer needs its documented `--soft-gl` SwiftShader flag. The `design-taste` inspector already renders in software.
- The repository is copied to `/opt/nice-skills` with Python 3.12 and Node.js 24 on `PATH`. A writable motion runtime with the render, core, music, and voice tiers, including the Kokoro model, is prepared at `/opt/motion-runtime`; pass `--reuse` to `prepare_runtime.py` to use it.
- `/work` is the working directory. Copy the selected skill directory there, or read it from `/opt/nice-skills/skills/` and write outputs to `/work`. The image runs as root and trusts bind-mounted checkouts; add `--user "$(id -u):$(id -g)"` if you prefer your host identity.
- Not included: provider credentials or adapters, Whisper model downloads, instrument samples (about 1.4 GB), HDRIs, the lyric-alignment Python stack, additional fonts, and Playwright browsers other than Chromium. Fetch or install those per project as the owning skill documents.
- The image is roughly 5.4 GB, mostly LibreOffice, TeX, Chromium, and the motion runtime. Remove `lmodern`, `latexmk`, and the `texlive-*` packages from the runtime stage if the PDF TeX route is not needed.

## Repository verification tooling

Running the repository's checks needs the versions in this table plus the pinned Python and Node test dependencies. See [tests/README.md](tests/README.md) for the commands, coverage, and optional skips; CI uses Python 3.12 and Node.js 24. The sample container can run the same suites against a bind-mounted checkout; suites that inspect Git metadata need that checkout rather than the baked copy.

## Source-adapted workflow additions (2026-10-26)

| Skill or helper | Required | Optional and limits |
| --- | --- | --- |
| software-workflow | Source access and the destination project's own tools | No new runtime or hooks |
| procedural-3d | The user's existing Blender or Three.js environment | Version follows the destination project; no model weights, MCP server, generator, or third-party assets bundled |
| game-development | Destination engine/SDK; Python 3.10+ for the nine helpers | Raster tools use Pillow 11.3.0. Engine execution is separate from static checks. The Ebitengine generator defaults to Ebitengine 2.10.5 and Go 1.25.0; generated dependencies need the destination project's lock/build verification. Other engine versions follow the selected guide and existing project. No engines, signing identities, or publishing accounts are installed |
| design-research | Python 3.10+ standard library | Offline catalog retrieval; external asset acquisition and version checks need separately authorized network access |
| sound-design | NumPy 2.2.6, SciPy 1.15.3, Numba 0.61.2 from `skills/sound-design/requirements.txt` | Numba resolves llvmlite 0.44.0 in the test lock. No models or recorded samples. FFmpeg/ffprobe 6.1+ for optional final media mixing/inspection |
| theme-factory Hallmark exporter | Python standard library | Fonts are fallback names, not bundled binaries; browser review checks actual contrast and font availability |
| slides image composer | Existing Pillow 11.3.0 and python-pptx 1.0.2 | Existing LibreOffice/Poppler tier for visual review; content within images is not editable |
| gif-creator browser encoder | Python 3.10+, FFmpeg/ffprobe 6.1+ | Existing browser tooling only when capture is requested; no capture or upload inside the encoder |

Install the sound tier with `python -m pip install -r skills/sound-design/requirements.txt`; the repository test lock includes the same pins. Install game raster helpers with `python -m pip install -r skills/game-development/library/disciplines/create-game-assets/scripts/requirements.txt`. These are local dependencies; initial downloads need network access. The existing container's test lock installs the sound and raster dependencies, but it does not bundle game engines or Blender. Its broad dependency description covers the packaged Python/Node tools, not destination-project engines/SDKs.
