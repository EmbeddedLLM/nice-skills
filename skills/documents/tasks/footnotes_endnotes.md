# Task: real footnotes and endnotes

## Goal

Add or audit genuine footnotes/endnotes in a `.docx` — separate parts with numbered references — and confirm they render.

## How they are represented

Footnotes and endnotes are not text sitting in the footer. They live in their own parts:

- `word/footnotes.xml`
- `word/endnotes.xml`

and the body points at them with `w:footnoteReference w:id="N"` or `w:endnoteReference w:id="N"`. Both note parts must also carry the separator entries at `w:id="-1"` and `w:id="0"`; strict consumers reject files without them.

## Auditing what a document already has

```bash
python scripts/footnotes_report.py report.docx
```

## Inserting a note

`scripts/insert_note.py` patches the OOXML for you. Put a marker where the reference should land — `[[FN]]` for a footnote, `[[EN]]` for an endnote — then run:

```bash
python scripts/insert_note.py report.docx --kind footnote --marker "[[FN]]" --text "Source: internal ledger, March." --out with_fn.docx
python scripts/insert_note.py report.docx --kind endnote  --marker "[[EN]]" --text "Methodology note."              --out with_en.docx
```

The default marker is `[[NOTE]]`; `--kind`, `--text`, and `--out` are all required.

Then render and review:

```bash
python render_docx.py with_fn.docx --output_dir out_fn
```

## What the pages should show

- the marker appears in the body exactly where you put it;
- footnote text at the foot of that page, endnote text in the notes section;
- numbering starting at 1 with no duplicates and no gaps;
- long notes wrapping cleanly, with nothing overlapping or clipped.

## Pitfalls

- Missing separator entries in `footnotes.xml` / `endnotes.xml` break strict readers even though LibreOffice is forgiving.
- Marker visible but no note text? Run `footnotes_report.py` and check that the reference id in `document.xml` has a matching note id in the note part.
- For anything high-stakes, open the result in Microsoft Word as well as rendering it. The two disagree often enough to matter.
