---
name: gif-creator
description: Create and optimize compact animated GIF loops from local drawings or supplied assets, checking timing, palette, disposal, and file size. Use when the deliverable is a GIF rather than a full video.
license: Apache-2.0; see LICENSE.txt and SOURCES.md
---

# GIF creation

Use local Pillow drawing/encoding and optional FFmpeg conversion. No media API, chat account, or upload integration is required. The bundled helpers need [requirements.txt](requirements.txt); install into a project-local environment if needed.

## Design and encode

1. Establish dimensions, duration, loop behavior, transparency/background, and byte budget. Start with one readable motion and keep important text legible at final size.
2. Compute frames from explicit time. For a seamless periodic loop, omit the duplicated terminal frame and review the transition from the last frame to the first.
3. Draw equal-size frames with local primitives or supplied assets. Measure actual fonts rather than relying on emoji rendering.
4. Prefer a shared palette to avoid color flicker. GIF supports palette transparency, not full alpha; inspect disposal and the intended background. Timing is stored in centiseconds, so preserve cumulative duration when rounding or merging identical frames.

From the skill directory, import `GIFBuilder` from `core.gif_builder`, with optional drawing helpers in `core.frame_composer` and timing helpers in `core.easing`. Add equal-sized Pillow frames and call `builder.save("new.gif")`. The builder composites onto its explicit background, white by default; use a separate palette-transparency workflow for transparent output.

For a supplied browser video or ordered screenshots, use [browser recordings](references/browser-recordings.md) and `scripts/encode_gif.py` for trim, speed, final hold, and checked byte budgets.

## Optional Openverse image assets

Use the free anonymous [Openverse image API](https://api.openverse.org/v1/) for stills to animate when network access and an HTTP tool are available. Example:

```text
GET https://api.openverse.org/v1/images/?q=clouds&license=cc0,pdm,by&page_size=5&mature=false
```

Use public subject terms, inspect warnings, and verify each image's license, creator, and notices on its original source page; [Openverse metadata needs verification](https://docs.openverse.org/api/reference/made_with_ov.html). Keep the default license selection unless another license's adaptation and distribution conditions fit the animation.

Download selected originals before frame generation, inspect dimensions and crop, and animate local copies. GIF has no soundtrack, so audio search does not apply. Deliver required credits alongside the GIF, including title, creator, source URL, license/version/link, retained notices, and transformations. Do not depend on GIF comments surviving sharing or optimization.

Respect source-host terms, response limits, and retry guidance on 429; do not scrape the catalog. If access fails or rights cannot be verified, use appropriate supplied imagery or local drawing and disclose any missing requirement. The encoder needs no account, paid service, or runtime network access.

## Verify

```sh
python core/validators.py new.gif --max-bytes 500000
```

The validator inspects decoded dimensions, frame count, duration, looping, and the specified size budget. Reopen and play the GIF as well: a contact sheet cannot prove motion quality. If oversized, reduce the least important of dimensions, palette size, frame rate, or duration and verify again. Report an unmet budget rather than claiming compliance or uploading without instruction.

Example: “Make a looping 256-pixel progress pulse under 500 KB.” Deliver the GIF with a continuous loop and checked byte size; keep the generator available for revisions.
