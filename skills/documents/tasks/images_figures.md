# Task: image and figure placement

## Goal

Images and their captions stay where you put them across Word, LibreOffice, and PDF export.

## Why this is the hard part

Image placement is the single most common LibreOffice-versus-Word divergence. A page that is correct in one is wrong in the other often enough that every image-bearing document needs a render check.

## Inline versus floating

| Kind | Markup | Behaviour |
| --- | --- | --- |
| Inline | `wp:inline` | acts like a very large character in the text flow; the most predictable option for automation |
| Floating / anchored | `wp:anchor` | supports wrap-around, absolute positioning, keep-with-paragraph — and is the kind that renders differently between applications |

## Guidance

1. Use inline images unless the design genuinely requires text to wrap around them.
2. Start from high-resolution sources and let the document scale down. Scaling a low-DPI image up produces visible softness that no amount of layout work fixes.
3. Put the caption in its own paragraph directly after the image so the two travel together.

## Audit

```bash
python scripts/images_audit.py work/report.docx
```

`--max_rows` caps the listing (default 50). Any row reported as `anchor` is high risk: read the renders of those pages closely.

## Image review checklist for the rendered pages

- each image is on the page it belongs to;
- nothing overlaps text, tables, or margins;
- captions are still adjacent to their figures;
- images are not soft or pixelated — zoom to 200% to be sure;
- no unexpected cropping or stretching.

## Pitfalls

- A floating image migrating to another page after an unrelated text edit.
- Wrap modes that LibreOffice resolves into an overlap.
- Pasted screenshots carrying enormous DPI metadata, which makes them render far larger than they appear on screen.
