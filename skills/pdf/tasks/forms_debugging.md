# Diagnose a rejected or invisible form value

Keep the failing PDF and intended value mapping together. Reproduce one field first, then inspect its actual type and widgets:

```sh
python scripts/pdf_extract.py forms source.pdf --include_widgets --out review/fields.json
```

A field name may be hierarchical or shared by widgets on multiple pages. Match its page and rectangle to the label before changing the mapping. Choice fields need an exact option from `options`; a visible label may differ from the stored export value. XFA is not ordinary AcroForm and needs a compatible route rather than forced overlays.

The Node fill helper accepts strings for text, booleans for checkboxes, and one listed string for choice/radio fields. Inspecting `appearance_states` helps explain backend state names, but do not replace a Node checkbox boolean with a PDF name such as `/Yes`. Invalid keys, types or choices reject the entire mapping before output is saved. Correct the reported field rather than ignoring it.

When the stored value exists but is invisible, compare appearance streams and renderers. `--need_appearances` in the Python fill command is a viewer hint, not a portable appearance guarantee. Run [renderer parity](parity.md) and inspect the actual target viewer when available. Flatten only when the user's required editing behavior permits losing interactive fields. Preserve an editable copy if both a filled form and a fixed reading copy are needed.

If a value clips, inspect its rectangle, font and maximum length. Do not truncate user input to make it fit. Ask about an abbreviation or alternate field when the meaning would change. Record unsupported fonts or forms as limitations.
