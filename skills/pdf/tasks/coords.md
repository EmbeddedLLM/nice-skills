# Match coordinates to the selected operation

Record units, origin, page rotation and the box represented by an image before using coordinates. PDF points are 1/72 inch; raster pixels depend on render DPI. The same four numbers can refer to different regions in different tools.

| Consumer or producer                                      | Coordinate convention                         |
| --------------------------------------------------------- | --------------------------------------------- |
| `place_text_by_boxes.py`, ReportLab canvas, picker export | Bottom-left PDF points                        |
| `pdf_redact.py` boxes, PyMuPDF positions                  | Top-left PDF points                           |
| `fill_pdf_form_with_annotations.py` field specification   | Top-left coordinates with explicit page units |
| Rendered PNG                                              | Top-left pixels                               |

For an unrotated page rendered at `d` DPI with no crop offset, a pixel rectangle `[left, top, right, bottom]` becomes bottom-left points as follows:

```text
scale = 72 / d
[left * scale, (image_height - bottom) * scale,
 right * scale, (image_height - top) * scale]
```

For top-left points under those same assumptions, scale all four coordinates without flipping the vertical axis. Converting a bottom-left rectangle to top-left points requires `[left, page_height-top, right, page_height-bottom]`.

These formulas are insufficient when rotation, a nonzero MediaBox origin, or a trimmed CropBox changes the rendered viewport. Inspect the actual page boxes and renderer behavior. Normalize a separate copy only when the preservation contract allows it, or apply the page's transformation explicitly. The picker does not prove that unusual geometry is supported. The annotation helper rejects rotated pages instead of guessing their placement.

Validate with a labeled guide overlay and re-render the page. Confirm two widely separated reference points, page edges and the intended entry area. Keep source coordinates and their convention in the mapping file so later edits do not accidentally reuse them in the wrong tool. Cropping hides content; it is not redaction.
