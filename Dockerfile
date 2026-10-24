# Sample environment for the published skills. See DEPENDENCIES.md.
# Build: docker build -t nice-skills:local .
# Run:   docker run --rm -it -v "$PWD:/work" -w /work nice-skills:local
#
# The image contains the repository at /opt/nice-skills with every required and
# optional dependency installed, plus a prepared motion runtime at /opt/motion-runtime
# that includes the Kokoro voice model. Skills stay read-only; copy a skill and write
# its outputs in /work. Instrument samples, HDRIs, the Whisper models, and any
# paid-provider credentials are not baked in; fetch or supply them per project.

ARG UBUNTU_VERSION=24.04
ARG NODE_IMAGE=node:24-bookworm-slim
ARG UV_VERSION=0.12.7

# Pinned uv binary; it installs the pinned Python manifests and stays available in
# the runtime stage for project environments.
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# Python packages from every skill manifest, kept out of the runtime stage so the
# compiler toolchain and package cache do not ship. uv resolves and installs the
# pinned manifests into a virtual environment on the distribution Python.
FROM ubuntu:${UBUNTU_VERSION} AS python-deps

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential ca-certificates python3 python3-dev python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /usr/local/bin/uv

RUN uv venv --python /usr/bin/python3 --seed /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY skills/documents/requirements.txt /tmp/req/documents.txt
COPY skills/documents/scripts/requirements-office.txt /tmp/req/documents-office.txt
COPY skills/pdf/requirements.txt /tmp/req/pdf.txt
COPY skills/pdf/requirements-redaction.txt /tmp/req/pdf-redaction.txt
COPY skills/pdf/requirements-browser.txt /tmp/req/pdf-browser.txt
COPY skills/pdf/requirements-ocr.txt /tmp/req/pdf-ocr.txt
COPY skills/pdf/scripts/requirements-forms.txt /tmp/req/pdf-forms.txt
COPY skills/slides/requirements.txt /tmp/req/slides.txt
COPY skills/slides/scripts/requirements-office.txt /tmp/req/slides-office.txt
COPY skills/spreadsheets/requirements.txt /tmp/req/spreadsheets.txt
COPY skills/gif-creator/requirements.txt /tmp/req/gif-creator.txt
COPY skills/vector-art/requirements.txt /tmp/req/vector-art.txt
COPY skills/webapp-testing/requirements.txt /tmp/req/webapp-testing.txt
COPY skills/skill-creator/requirements.txt /tmp/req/skill-creator.txt
COPY tests/requirements.txt /tmp/req/tests.txt

RUN uv pip install --no-cache --python /opt/venv/bin/python \
        -r /tmp/req/documents.txt \
        -r /tmp/req/documents-office.txt \
        -r /tmp/req/pdf.txt \
        -r /tmp/req/pdf-redaction.txt \
        -r /tmp/req/pdf-browser.txt \
        -r /tmp/req/pdf-ocr.txt \
        -r /tmp/req/pdf-forms.txt \
        -r /tmp/req/slides.txt \
        -r /tmp/req/slides-office.txt \
        -r /tmp/req/spreadsheets.txt \
        -r /tmp/req/gif-creator.txt \
        -r /tmp/req/vector-art.txt \
        -r /tmp/req/webapp-testing.txt \
        -r /tmp/req/skill-creator.txt \
        -r /tmp/req/tests.txt \
    && rm -rf /tmp/req

# Node packages from the skill lockfiles. Playwright browsers are installed in the
# runtime stage, where the system libraries they need also live.
FROM node:24-bookworm-slim AS node-deps

WORKDIR /deps

COPY skills/pdf/js/package.json skills/pdf/js/package-lock.json pdf-js/
RUN cd pdf-js && npm ci --no-audit --no-fund

COPY skills/slides/pptxgenjs_helpers/package.json skills/slides/pptxgenjs_helpers/package-lock.json pptxgenjs-helpers/
RUN cd pptxgenjs-helpers && npm ci --no-audit --no-fund

COPY skills/documents/equation-runtime/package.json skills/documents/equation-runtime/package-lock.json equation-runtime/
RUN cd equation-runtime && npm ci --no-audit --no-fund

COPY skills/create-motion-videos/assets/hand-painted-cartoon/package.json skills/create-motion-videos/assets/hand-painted-cartoon/package-lock.json hand-painted-cartoon/
RUN cd hand-painted-cartoon && npm ci --no-audit --no-fund

FROM ubuntu:${UBUNTU_VERSION} AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PATH=/opt/venv/bin:$PATH \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONUNBUFFERED=1

# Required and optional command-line tools: document rendering, PDF processing,
# media encoding and delivery, OCR, conversion, fonts, and Git.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        ffmpeg \
        fontconfig \
        fonts-dejavu-core \
        fonts-liberation \
        ghostscript \
        git \
        jq \
        latexmk \
        libreoffice-calc \
        libreoffice-impress \
        libreoffice-writer \
        lmodern \
        pandoc \
        poppler-utils \
        python3 \
        python3-venv \
        tesseract-ocr \
        tesseract-ocr-eng \
        texlive-fonts-recommended \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-xetex \
    && rm -rf /var/lib/apt/lists/*

# Treat bind-mounted checkouts as trusted so the repository's Git-based audit suites
# run against /work when the container runs as root.
RUN git config --system --add safe.directory '*'

# Node.js 24 for npm-driven helpers and the motion runtime (Node 20+ required).
COPY --from=node-deps /usr/local/bin/ /usr/local/bin/
COPY --from=node-deps /usr/local/lib/node_modules/ /usr/local/lib/node_modules/

COPY --from=python-deps /opt/venv /opt/venv

# uv manages Python environments for both the skills and the repository checks.
COPY --from=uv /uv /usr/local/bin/uv
RUN ln -s /usr/local/bin/uv /usr/local/bin/uvx

# Playwright 1.58.0 Chromium for vector-art previews, webapp-testing, and the PDF
# browser tier, with the distribution libraries it needs.
RUN apt-get update \
    && python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

# The vendored design-taste inspector and the motion cartoon kit launch a browser
# without --no-sandbox, which container sandboxes block. Expose the pinned Chromium
# through a wrapper and point the skills at it.
RUN chrome="$(python -c 'from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print(p.chromium.executable_path); p.stop()')" \
    && printf '#!/bin/sh\nexec "%s" --no-sandbox "$@"\n' "$chrome" > /usr/local/bin/chromium \
    && chmod +x /usr/local/bin/chromium
ENV CHROME_PATH=/usr/local/bin/chromium

# Node helpers stay next to their manifests so npm and each skill's documented
# commands resolve them from the skill directory.
COPY --from=node-deps /deps/pdf-js/node_modules /opt/nice-skills/skills/pdf/js/node_modules
COPY --from=node-deps /deps/pptxgenjs-helpers/node_modules /opt/nice-skills/skills/slides/pptxgenjs_helpers/node_modules
COPY --from=node-deps /deps/equation-runtime/node_modules /opt/nice-skills/skills/documents/equation-runtime/node_modules
COPY --from=node-deps /deps/hand-painted-cartoon/node_modules /opt/nice-skills/skills/create-motion-videos/assets/hand-painted-cartoon/node_modules

COPY . /opt/nice-skills

# Writable motion runtime with Node packages, Playwright Chromium, and the core,
# music, and voice Python tiers. The voice tier also fetches the Kokoro model.
# Whisper models and the large instrument/HDRi packs stay per-project downloads.
# Verify voice imports because upstream package metadata can omit runtime dependencies.
RUN python3 /opt/nice-skills/skills/create-motion-videos/scripts/prepare_runtime.py /opt/motion-runtime --install render \
    && python3 /opt/nice-skills/skills/create-motion-videos/scripts/prepare_runtime.py /opt/motion-runtime --reuse --install music \
    && python3 /opt/nice-skills/skills/create-motion-videos/scripts/prepare_runtime.py /opt/motion-runtime --reuse --install voice \
    && /opt/motion-runtime/.venv/bin/python -c "import kokoro_onnx, faster_whisper"

WORKDIR /work

CMD ["bash"]
