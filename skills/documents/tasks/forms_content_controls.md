# Populate a Word form

Determine whether the deliverable must remain fillable, become a completed form, or retain edit restrictions. Obtain the actual template and field values; do not infer missing names, dates, or declarations. Inspect tags, bindings, locks, repeating sections, and control types before editing. Preserve the supplied form's structure and named styles, following the production guidance identified in [Sources and notices](../SOURCES.md).

## Plain-text helper

The local helper requires Python and `lxml`. It edits the main document and numbered header/footer parts by default. Add `--no_headers_footers` to any action to restrict the scope.

```sh
python scripts/content_controls.py intake.docx list --json
```

The JSON array records each control's part, tag, alias, and text. Match values to tags rather than labels that may repeat. Preserve unknown controls. Dropdown choices, checkboxes, date metadata, data bindings, repeating sections, and controls with nested tables need a route that understands their semantics; this text helper is insufficient.

For a new plain-text template, author distinctive tokens such as `{{PROJECT}}` in single text nodes. Convert them before filling:

```sh
python scripts/content_controls.py blank.docx wrap_placeholders --output tagged.docx
python scripts/content_controls.py tagged.docx fill --set 'PROJECT=Example project' --set 'REFERENCE=R-104' --output complete.docx
```

Wrapping retains surrounding text, run formatting, and nontext run children. It leaves existing controls alone. Tokens divided across runs or interrupted by nontext elements are not recognized; normalize the token deliberately in the authoring application and verify it again. Filling replaces the selected control content while retaining the first run's formatting and the first paragraph's properties for block controls. Nested controls/tables are refused to prevent silent structural loss. An invalid assignment fails before publishing output.

## Review

List the saved controls again and compare tags and values with the input record. Check leading/trailing spaces, repeated tags, long values, untouched fields, and header/footer scope. Render the completed file to catch overflow and unexpected pagination. For a form intended for further editing, open it in a compatible editor and exercise navigation and typing when available. Record if this interaction was not tested; an XML listing cannot establish form usability.
