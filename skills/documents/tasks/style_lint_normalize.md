# Task: style lint and normalization

## When this comes up

The user says something like: "make the formatting consistent", "apply our style guide", "get rid of the random bold and spacing", or "why do the headings look different from each other?"

Two tools cover it:

- `scripts/style_lint.py` — reports the inconsistencies;
- `scripts/style_normalize.py` — conservative cleanup, optional.

## The workflow that avoids damage

1. Render to PNG first and look at the areas the user complained about. That is your baseline.
2. Lint, and read what is actually causing the drift.
3. Normalize only where the result matches the user's intent.
4. Re-render and read **every** page.

## Linting

```bash
python scripts/style_lint.py report.docx --json work/style_report.json
```

Signals worth attention:

- a high `run_direct_formatting` count — the usual answer to "why is this one different";
- more than one font or size in body text that should all be `Normal`;
- paragraphs that look like headings but carry no Heading style.

## Normalizing

`style_normalize.py` always removes **run-level** overrides — bold, italic, underline, font, size, colour — so that styles drive appearance.

**Default (start here):**

```bash
python scripts/style_normalize.py report.docx out_normalized.docx
```

The output path also accepts `--out`:

```bash
python scripts/style_normalize.py report.docx --out out_normalized.docx
```

**Also clear paragraph-level overrides** — more invasive, can move layout; use only when the user wants spacing and indents to come from styles:

```bash
python scripts/style_normalize.py report.docx out_normalized.docx --clear_paragraph_format
```

**Enforce one heading spacing rule** (space after = 6pt), for documents where headings drift apart:

```bash
python scripts/style_normalize.py report.docx out_normalized.docx --enforce_heading_spacing
```

## Visual QA gate

```bash
python render_docx.py out_normalized.docx --output_dir work/out_norm
```

Pass means: nothing clipped or overlapping, headings and body text consistent, tables still aligned.

## Pitfalls

- Clearing run overrides also clears **deliberate** emphasis. If the document uses bold or italic for meaning, do not normalize globally — restrict it to the styles or sections that need it.
- Some documents mix fonts on purpose, code samples being the obvious case. Whitelist those styles rather than clearing everything.

## Deliverables

Ship only the final DOCX the user asked for. PNGs and any optional PDF are internal QA material unless requested.
