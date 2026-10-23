# Task: captions and cross-references (SEQ and REF)

## When this applies

The user wants "Figure 1" / "Table 2" style captions, prose that says "see Figure 3", and numbering that survives a headless render.

Word does captions and cross-references with fields: `SEQ` produces the number (`SEQ Table`, `SEQ Figure`) and `REF` points at a bookmark. `python-docx` offers no API for either, so the work happens at OOXML level through three helpers:

| Script                              | Job                                                                        |
| ----------------------------------- | -------------------------------------------------------------------------- |
| `scripts/captions_and_crossrefs.py` | insert caption paragraphs, optionally bookmarking the caption number       |
| `scripts/insert_ref_fields.py`      | turn `[[REF:bookmark]]` markers into real `REF` fields                     |
| `scripts/fields_materialize.py`     | freeze `SEQ`/`REF` display text so headless renders show the right numbers |

## The gotcha that drives the design

Fields do not update reliably without a GUI editor. Insert field codes only and the rendered number may be blank or stale. So for deterministic automation:

1. insert the field codes, then
2. materialize their display text.

A person can still open the file later and update fields; automation gets stable visuals either way.

## Workflow

### 1. Add captions, and bookmarks if you will cross-reference

Captions are added to tables and/or figures that do not already have a `Caption` paragraph immediately after them:

```bash
python scripts/captions_and_crossrefs.py \
  work/in.docx \
  work/with_captions.docx \
  --tables --figures \
  --caption_text "Caption" \
  --bookmarks
```

Each caption is a `Caption`-styled paragraph numbered by a `SEQ Table` or `SEQ Figure` field. With `--bookmarks`, the number itself is wrapped in a bookmark: `tbl1`, `tbl2`, … for tables and `fig1`, `fig2`, … for figures. At least one of `--tables` / `--figures` is required. Pass `--materialize` to fold in step 3 at the same time.

### 2. Insert the cross-references

Write markers into the prose where references belong:

```
See [[REF:tbl1]] for the breakdown.
As shown in [[REF:fig2]] …
```

then convert them:

```bash
python scripts/insert_ref_fields.py \
  work/with_captions.docx \
  work/with_refs.docx
```

Markers are replaced in `document.xml` and in headers and footers, and several may sit inside one run. `--pattern` overrides the marker regex (it must define a group named `bookmark`) and `--prefix` inserts text just before the field.

**Limitation:** a marker has to be wholly inside one `<w:t>`. If Word split it across runs, retype it as a single contiguous token.

### 3. Materialize for deterministic renders

```bash
python scripts/fields_materialize.py \
  work/with_refs.docx \
  --out work/with_refs_materialized.docx
```

`SEQ` values are materialized before `REF` values so cross-references pick up the new caption numbers. To freeze only one kind, pass `--only REF` (or `--only SEQ`).

### 4. Render and QA

```bash
python render_docx.py work/with_refs_materialized.docx --output_dir work/out_caps
```

## Pitfalls

- **No `Caption` style in the document** means captions come out looking like body text. Apply a template or style pack first if the user cares.
- **Figure detection** is structural: a paragraph counts as a figure paragraph when it contains a `<w:drawing>` or `<w:pict>`.
- **Editing after materializing** invalidates the frozen numbers. Re-run `fields_materialize.py` whenever figures or tables are added or removed.

## Deliverables

Only the final DOCX the user asked for. PNGs and optional PDFs are internal QA unless requested.
