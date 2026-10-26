# Renderer parity

A PDF that looks right in one viewer but broken in another is a renderer-sensitivity problem. The golden path renders the same input twice — poppler (pdftoppm) and pdfium — and pixel-diffs the PNGs:

```bash
python scripts/renderer_parity.py input.pdf --out_dir _parity --dpi 200
```

Then open, in order:

- `_parity/render_pdftoppm/page-*.png` — poppler's rendering
- `_parity/render_pdfium/page-*.png` — pdfium's rendering
- `_parity/diff/page-*.png` — written only where the two disagree

Randomized rendering inside the PDF (rare) can make parity diffs noisy; when a diff is tiny, spot-check it visually instead of chasing it.
