# Inspecting and changing document stamps

Start by identifying the user's intended change: remove a draft label, replace a classification label, or introduce a new stamp. Confirm which pages and section variants should change. A picture behind text may be branding rather than a watermark; a text match alone cannot establish intent.

The [document production principles](../SOURCES.md) apply: preserve unrelated package parts, choose a writer that supports the actual objects, and inspect the saved output. Use a working copy and inventory first/default/even headers, footer artwork, and body backgrounds before selecting a removal method.

## Supported local operations

The bundled tools require Python and `lxml`; run these commands from the skill directory or resolve the script paths there.

```sh
python scripts/watermark_audit_remove.py review.docx --mode report
python scripts/watermark_audit_remove.py review.docx --mode remove --contains 'DRAFT COPY' --out released.docx
```

The report searches the body and numbered header/footer parts. It lists VML text paths and attribute values containing “watermark,” including false positives. Review the relevant XML and page image together. Removal deletes the complete `w:pict` containing a case-insensitive matching VML text path. A nonempty filter and output path are required; unmatched pictures and unrelated ZIP members survive. It does not remove arbitrary DrawingML or page-background artwork.

For a synthetic draft stamp:

```sh
python scripts/watermark_add.py review.docx --text 'DRAFT COPY' --out stamped.docx
```

This helper targets the lowest-numbered header, creating a default header on the first section if none exists. It does not promise coverage of every section or odd/even/first-page header. Inspect those variants before presenting it as a whole-document stamp.

## Verification and delivery

Compare original and revised pages with `scripts/render_and_diff.py`, following [render verification](verify_render.md). Check the stamp's visibility, logos, running text, page count, and unexpected layout movement. A renderer that never displayed the original stamp cannot prove its visual removal. If the target editor is unavailable, report the XML changes separately from that unverified appearance.

Deliver the requested DOCX and any requested PDF companion. Do not describe a classification stamp as access control or as a substitute for document protection.
