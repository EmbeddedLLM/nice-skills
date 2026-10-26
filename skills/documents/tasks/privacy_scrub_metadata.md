# Task: privacy scrub (strip personal metadata)

## Goal

Make a `.docx` safe to send outside the organisation by removing the metadata that identifies people and machines:

- core properties — creator, lastModifiedBy;
- custom properties — `docProps/custom.xml`, when the package has one;
- Word's revision session ids, the `rsid*` attributes scattered through story parts.

What it does **not** do: touch the document's meaning. Text and images are left alone, and personal data _inside_ the content is not redacted. For that, use `redact_docx.py`.

## Running it

```bash
python scripts/privacy_scrub.py report.docx --out scrubbed.docx
```

## Verifying

```bash
python render_docx.py scrubbed.docx --output_dir out_scrubbed
```

The pages should be indistinguishable from the input — a scrub that changes the layout has done something it should not.

## Pitfalls

- Some viewers keep author information cached outside the file. When the stakes are high, open the resulting `docProps/core.xml` and read it.
- Templates and other documents that rely on custom properties lose them here. Do not scrub those.
