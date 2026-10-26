# Interactive PDF form integrity

A page widget can paint a plausible value while the canonical AcroForm tree is missing or stale. Verify both representations.

1. Enumerate `PdfReader.get_fields()` and page `/Annots` of subtype `/Widget`, following `/Parent` and `/Kids`. Record fully qualified names, field types, current values, allowed options, and button export states.
2. Distinguish true orphan widgets from duplicate-name objects. If a widget and a canonical field share a name but are distinct and unlinked, do not blindly call `reattach_fields()`: it can create a second top-level field. Resolve the ambiguity before filling. Offer a static result only when that meets the user's intent.
3. Clone the original into a writer, repair only understood orphan links, reject unknown fields, and validate values against types/options. Fill all relevant pages with appearance regeneration controlled deliberately. Preserve interactivity by default.
4. Reopen the written file. Every expected field must have the expected `/V`; each widget's own or inherited value must agree. Check nonempty normal appearance streams for changed widgets and render the result for stale/clipped appearances. `/NeedAppearances` is not proof of correctness.
5. Flatten only when requested. Paint current and updated field values before removing widgets and the AcroForm tree. Reopen and verify there are no remaining widgets or form fields, then inspect rendered pages.

Editing a signed PDF can invalidate its signature. Preserve the original and clarify the intended signed-document workflow if the requested edit depends on signature validity. Do not assert signature preservation from a clean render.

Use [form mapping](../tasks/form_field_mapping.md) for field discovery and strict input validation, and [debugging](../tasks/forms_debugging.md) for problematic widget structures. For visual overlays on a nonfillable PDF, report the result as stamped text, not interactive fields.
