# Explicit raster-deck mode

Use this mode only when the user wants supplied slide images, a visual storyboard, or an image-based deck and accepts that text/charts inside each picture are not editable. For normal presentations, use native text, shapes, tables, and charts. Adapted from DeerFlow; [SOURCES.md](../SOURCES.md) and [LICENSE-deer-flow.txt](../LICENSE-deer-flow.txt) retain the source and notice.

Establish slide order, aspect ratio, content, and a visual system before producing images. If generation is explicitly requested and available, keep references consistent across slides; generation is optional, and no paid provider is required. Review text accuracy in the images before composing the deck. Prefer native overlays when important text or data must remain editable.

Create a local plan with exactly one entry per supplied image:

```json
{
  "aspect_ratio": "16:9",
  "slides": [
    { "title": "Observation", "key_points": ["Synthetic example"], "notes": "Source and context", "credits": "Creator, source, license, changes" }
  ]
}
```

```sh
python scripts/images_to_pptx.py --plan-file plan.json --slide-images slide-01.png --output-file storyboard.pptx
```

The helper uses the existing pinned Pillow/python-pptx dependencies, applies EXIF orientation, preserves transparency, contains each image without distortion, centers letterboxing, and transfers text/credits to notes. Only 16:9 and 4:3 are supported. Missing/corrupt images, mismatched counts, invalid plans, or existing output without `--force` fail nonzero. Validation/encoding failure preserves prior output even with `--force`.

Render and inspect every slide using the normal slide workflow. Confirm count/order, fit, image readability, and notes; add visible credits if the license requires them or exports would omit notes. Deliver editable source images/plan when appropriate and disclose the raster editability limit. Do not call this a fully editable deck.
