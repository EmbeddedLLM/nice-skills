# Task: redaction and anonymization (layout-preserving)

## When this applies

Sensitive material has to go, but the document must stay usable and visually stable: removing emails, names, and identifiers; anonymizing customer or company names; producing a version of a report that can be shared.

`scripts/redact_docx.py` works on OOXML text nodes and defaults to length-preserving masking — each match is replaced by the mask character repeated to the same length — so line breaks and pagination barely move.

## The path to follow

1. Copy the input. Never redact the only copy of a file.
2. Run the tool with patterns scoped as tightly as you can.
3. Render to PNG and read the redacted areas.
4. Confirm nothing sensitive survives: spot-check visually and search the extracted text.

## Running it

Both paths are positional — input first, output second.

Built-in rules for the common cases:

```bash
python scripts/redact_docx.py work/input.docx work/redacted.docx \
  --emails --phones
```

Custom regexes, repeatable:

```bash
python scripts/redact_docx.py work/input.docx work/redacted.docx \
  --pattern "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" \
  --pattern "\b\d{3}[-. ]\d{3}[-. ]\d{4}\b"
```

A visible label instead of a mask, still length-preserving (the label is repeated or truncated to fit each match):

```bash
python scripts/redact_docx.py work/input.docx work/redacted.docx \
  --pattern "Acme Corp" --replacement "[REDACTED]"
```

Also sweep `word/comments.xml`:

```bash
python scripts/redact_docx.py work/input.docx work/redacted.docx \
  --pattern "confidential" --include_comments
```

Other switches: `--mask_char` changes the mask glyph (default `█`), and `--no_preserve_length` turns length preservation off — expect layout drift if you use it. At least one rule is required or the tool exits.

## Pitfalls

- **An over-broad regex eats prose.** Prefer specific patterns and read the diff of what was replaced.
- **Matches cannot span paragraphs.** Redaction happens inside a single `w:p`, so keep patterns local.
- **Text that is not a text node stays put.** Images of text, embedded objects, charts, and the deleted side of tracked changes can all carry sensitive data that masking text will not remove.

## QA checklist

- Render and inspect every page containing a redaction.
- Search the document text to confirm the strings are gone.
- Check headers, footers, footnotes, and endnotes — the script patches those by default, but verify rather than assume.

## Deliverables

Only the final DOCX the user asked for. PNGs and optional PDFs are internal QA unless requested.
