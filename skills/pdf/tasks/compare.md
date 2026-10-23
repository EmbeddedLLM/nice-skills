# Assess changes with rendered evidence

Use the same engine and resolution for before/after comparison:

```sh
python scripts/compare_renders.py original.pdf revised.pdf --out_dir review/diff --dpi 150 --save_renders
```

The helper invokes `render_pdf.py` with the current Python interpreter. Install Pillow and the selected renderer (`--engine pdftoppm` or `pdfium`). It saves `summary.json` with page counts and `per_page` records. A missing page is marked `missing`; compared pages include `changed`, `bbox`, `pct_changed` and `max_channel`. Changed pages also have a diff PNG path. Page files are paired by numeric page order. A rerun clears obsolete generated diff images.

Differences use exact RGB-channel values. `pct_changed` is the fraction of pixels with any changed channel, and `max_channel` is the largest channel difference. Images of different sizes are padded with white rather than stretched; white margins alone may therefore produce no pixel change. Check dimensions separately. The command exits successfully when comparison completes even if pages differ.

`--save_renders` retains `render_a/` and `render_b/`. Without it, generated page renders are removed after the report is written. With retained renders, a contact sheet can help review long documents:

```sh
python scripts/create_montage.py review/diff/render_b --out review/revised-sheet.png --cols 3
```

Relate each difference to the requested edit. Metadata-only work should leave appearance unchanged; an inserted page shifts later pairings and needs manual page mapping. Pixel agreement does not prove that links, fields, attachments or accessibility survived. Verify those structures independently. For different viewer engines, use [renderer parity](parity.md) and expect rasterization noise.
