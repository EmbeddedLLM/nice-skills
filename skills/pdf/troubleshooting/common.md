# Investigate the first observable failure

Keep the input and tool diagnostics. Reduce the failing operation to one page or field when possible, without replacing the original. A fallback is useful only if it still meets the requested output and preservation requirements.

| Observation                       | Next evidence to inspect                                                           |
| --------------------------------- | ---------------------------------------------------------------------------------- |
| Empty extraction                  | Render the page; determine whether it is scanned, encrypted or lacks text mappings |
| New line breaks or clipped labels | Font availability/embedding, page dimensions and export settings                   |
| Overlay displaced                 | Rotation, CropBox offset, origin and units in the mapping                          |
| Value saved but invisible         | Field/widget value and appearance streams; compare renderer engines                |
| Scrambled table cells             | Original rendered table, word coordinates, merged cells and reading order          |
| Conversion failed                 | Executable availability, source-relative assets and converter stderr               |

For a second rendering route, specify a destination explicitly:

```sh
python scripts/render_pdf.py source.pdf --engine pdfium --out_dir review/pdfium
```

Renderer warnings can coexist with a plausible image. Preserve and investigate warnings relevant to the requested task; visual appearance alone cannot establish that all content survived. Compare engines for disputed pages and report remaining uncertainty.

Missing glyphs require a font covering the actual characters, with embedding permitted by its license. Do not silently replace the user's punctuation or non-Latin text to hide a font problem. Regenerate from the source when possible.

For OCR issues, check source resolution, orientation and language data before trying destructive rasterization. `ocr_pdf.py --force` can replace existing text with OCR output; use it only when that tradeoff is appropriate and compare the result. Better OCR is not guaranteed by enlarging a low-resolution image.

A CropBox changes what is shown and leaves hidden content intact. Use the [redaction workflow](../tasks/redact.md) for removal. For encrypted documents, work only with authorized access and do not assume owner permissions are a request to remove restrictions. Keep unresolved credentials or unsupported features explicit in the result.
