# Link targets, field results, and running text

These features combine visible content with package state. Editing only the displayed label may leave a stale field result or a broken relationship. Preserve existing formatting and target semantics, and validate the saved artifact in the intended reader where possible. See [Sources and notices](../SOURCES.md) for the native-document guidance used here.

## Hyperlink ownership

An external link's `r:id` is resolved by the relationships part belonging to its containing story. A header link therefore uses that header's relationships, not `document.xml.rels`. The relationship identifies the destination and has external target mode. The `w:hyperlink` contains the visible runs, which may have multiple formatting spans.

For an internal destination, use a `w:anchor` matching an existing bookmark name. Confirm bookmark IDs pair correctly and names are unique enough for unambiguous navigation. Neither a plausible label nor a well-formed hyperlink element proves that the target exists.

Prefer an available native hyperlink API that preserves the source paragraph. If working with `python-docx` internals, create the relationship through the paragraph's own part and build the associated OOXML deliberately. Retain whitespace and run properties; apply the template's Hyperlink character style where appropriate instead of hardcoding brand colors.

The bundled `scripts/docx_ooxml_patch.py --hyperlink-first URL` is intended for simple boilerplate: it collapses the first paragraph's runs into a single link and loses their individual formatting. Do not use it on a complex paragraph that contains fields, mixed styles, or other anchored content.

## Fields have instructions and cached output

A complex field consists of a begin marker, an instruction, a separator, a cached result, and an end marker. The parts can span several runs. Simple fields use a different element form. Preserve the whole field when editing; replacing a cached page number with text does not change its instruction.

`PAGE` depends on pagination; TOC, REF, and sequence fields depend on document structure. Requesting an update on open does not perform the update. Use a compatible editor to refresh fields, save, and check the resulting references. Never present an unevaluated placeholder or repeated cached “1” as verified page numbering.

Useful local entry points are `scripts/fields_report.py` for inventory, `scripts/insert_toc.py` for a placeholder-based TOC, and `scripts/docx_ooxml_patch.py --add-page-numbers` for a first-section footer field. Consult their help and [field-update guidance](../tasks/fields_update.md) for their scope and dependencies.

## Headers and footers

Inspect section linkage before changing running text. Editing a shared header can affect several sections; first/even/default variants are separate. Named styles, paragraph tab stops, and explicitly sized tables can provide stable alignment. Avoid positioning with runs of spaces.

After edits, verify relationship targets and field structure, then test link activation separately from rendering. Review page numbers, section transitions, title-page variants, and the PDF companion if one is delivered. Describe any checks that require an unavailable target application as unverified.
