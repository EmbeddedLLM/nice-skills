# Task: fields and update behaviour (TOC, page numbers, cross-references)

## Goal

Tell the difference between a document that is wrong and a document whose Word fields are merely stale. Most "the render looks broken" reports are the second one.

The fields that cause this:

| Field            | Shows                                |
| ---------------- | ------------------------------------ |
| `PAGE`           | current page number                  |
| `NUMPAGES`       | total page count                     |
| `TOC`            | table of contents                    |
| `REF`, `PAGEREF` | cross-references, e.g. "see page 12" |

## When to suspect staleness

- the render shows placeholders: an empty TOC, every page numbered 1, a reference pointing at the wrong page;
- the file was edited programmatically (python-docx or an OOXML patch) and exported without a field refresh;
- LibreOffice and Word disagree about what the page says.

## Procedure

**1. Inventory the fields**

```bash
python scripts/fields_report.py work/report.docx
```

`--max_examples` controls how many samples per field type are printed. If the inventory mentions `TOC`, `REF`, `PAGEREF`, `NUMPAGES`, or `PAGE`, a refresh step belongs in the plan.

**2. Render and read**

```bash
python render_docx.py work/report.docx --output_dir work/out
```

Go through every `page-*.png` at 100% zoom.

**3. If something is stale, refresh in a GUI editor**

In Microsoft Word: open the file, `Ctrl+A`, `F9` (Update Fields), save, then render again. LibreOffice's GUI can also update fields, but Word is the reference implementation and the safer choice for a deliverable.

## When you cannot refresh: materialize instead

For stable PNG regression runs — where determinism matters more than Word semantics — bake cached field results into literal text so a headless render cannot drop them:

```bash
python scripts/flatten_ref_fields.py report.docx --out ref_flattened.docx
python scripts/fields_materialize.py ref_flattened.docx --out fields_materialized.docx
```

The first replaces `REF`/`PAGEREF` blocks with the visible text they currently cache; the second materializes `SEQ`/`REF` results such as caption numbers. Neither refreshes `TOC`, `PAGE`, or `NUMPAGES` — those still need a GUI editor. Render and inspect after materializing, as always.

## Field review checklist for the rendered pages

- page numbers increment through headers/footers;
- `NUMPAGES` equals the number of pages actually rendered;
- TOC entries exist, are indented by level, and their page numbers match where the headings really are;
- cross-references resolve — no "Error! Reference source not found.";
- no leftover authoring text such as "(TOC will populate…)".
