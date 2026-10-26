---
name: presenter-video
description: Edit and deliver presenter-led videos from supplied footage, or plan optional authorized presenter generation. Use for talking-presenter productions with narration, captions, supporting visuals, and delivery checks; new synthetic presenters require a separately selected generation backend.
license: MIT
compatibility: Local delivery requires Python 3, Bash, FFmpeg with libx264 and loudnorm, ffprobe, jq, and standard POSIX tools. Optional generation planning uses Python 3.12; the provider ledger requires POSIX file locks.
---

# Presenter video

Deliver a presenter-led video with intelligible speech, readable supporting visuals, and checked exports. **Supplied presenter footage is the default route**: it needs no API key, account, hosted model, or external transfer. Keep its original voice unless the user requests a replacement. This package does not include a model or adapter that generates a new speaking likeness.

## Choose inputs and route

Read the request and available media. Establish the audience, intended edits, delivery aspect/duration, and whether the user wants to use existing footage or generate new presenter material. Ask only about gaps that affect the work. Reuse known permissions and preferences.

- **Existing footage:** follow [local production](references/local-production.md). Use a supplied recording and its transcript or locally checked transcription. If footage is missing, request it or help prepare a recording brief; do not silently switch to paid generation.
- **New generated presenter:** read [generation](references/generation.md) and [provider lifecycle](references/provider-lifecycle.md) only when that route is requested. An installed local backend may be used if suitable; a remote or paid provider needs its own selected adapter, credentials, transfer authorization, and bounded cost/attempt plan. The bundled image-job tools are for this optional route and are not prerequisites for editing supplied footage.

## Edit and verify

1. Preserve original files and record sources, usable ranges, and the requested changes. For narration, use actual speech timing; label manual or estimated captions accordingly. Do not infer a voice or speech performance from a photograph.
2. Make an edit plan with separate source offsets and timeline starts. Keep accepted speech and presenter motion when revising supporting graphics. Read [editing](references/editing.md) for captions, screen demonstrations, cuts, and source-audio handling. No sibling skill or particular compositor is required.
3. Preview the edit and inspect captions, face/UI obstruction, cuts, speech sync, and the final spoken tail. Keep machine checks separate from visual and listening judgments. Revisit the user when new evidence exposes a consequential choice, such as unusable audio or an incompatible crop.
4. Finalize a rendered video using the bundled `scripts/finalize_delivery.sh`. It requires video and audible audio, checks complete decoding and delivered loudness, and writes master/share MP4s, a contact sheet, and a technical JSON report to new paths. [Local production](references/local-production.md) documents commands and failure behavior.
5. Review the encoded output using [QA and recovery](references/qa-recovery.md), including full playback/listening where available. A successful technical report does not establish factual accuracy, likeness quality, lip-sync, or human review. Deliver the editable project, used assets, captions, source records, and actual check results with any limitations. Publishing is a separate action.

Example: “Trim this recorded introduction, add chapter captions, and export a landscape version.” Inspect the recording and transcript, choose cuts at speech pauses, preserve its original audio, compose within the requested crop, then produce and review local delivery files. No provider selection or image-generation job is needed.

The optional provider tests use mocks; they do not establish a live provider's quality or billing behavior. [Sources and modifications](SOURCES.md) record the archive adaptation and retained notices.
