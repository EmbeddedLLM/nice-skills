# Task: accessibility audit and mechanical fixes

## Goal

Produce an accessibility report for a `.docx` and, where it is safe to do so mechanically, fix the findings that have the highest payoff.

This is not a WCAG conformance engine. It covers the checks that can be made dependably from OOXML:

- heading hierarchy with no skipped levels;
- images whose `descr` (alt text) is empty;
- tables with no header-row flag;
- link text that says nothing, such as "click here" or a bare URL.

## Running the audit

```bash
python scripts/a11y_audit.py brochure.docx
```

The report goes to stdout and the exit status is non-zero when any high-severity finding exists. To keep stdout short and write the full report to disk:

```bash
python scripts/a11y_audit.py brochure.docx --out_json a11y_report.json
```

## Optional fixes

**Fill empty alt text from the image filename** — a baseline that beats nothing, not a substitute for a real description:

```bash
python scripts/a11y_audit.py brochure.docx --fix_image_alt from_filename --out a11y_fixed.docx
```

**Flag the first row of each table as a header** — only when the first row really is one:

```bash
python scripts/a11y_audit.py brochure.docx --fix_table_headers first_row --out a11y_fixed.docx
```

Both fixes can be passed in a single run, with `--out` written once.

## Verification loop

1. Apply the fixes.
2. Render and read the pages to be sure nothing moved:

```bash
python render_docx.py a11y_fixed.docx --output_dir out_a11y
```

3. Re-run the audit against the fixed file and confirm the counts dropped.

## Pitfalls

- Heading problems are reported, never rewritten. Repairing a hierarchy is an editorial decision, not a mechanical one.
- Marking a header row changes how that row repeats across page breaks. Always re-render and look.
- Filename-derived alt text is a placeholder. Replace it with descriptions of what the image conveys before delivery.
