# Optional end-to-end smoke test

Five short checks that the runtime and the helper scripts are wired up. Run them against a throwaway file, not a deliverable — steps 2 to 4 overwrite their input unless you pass `--out`.

## 1. Rendering works

```bash
python render_docx.py work/sample.docx --output_dir work/pages
```

Expect a `Pages rendered to …` line and one PNG per page. Add `--verbose` if nothing appears.

## 2. Header line, footer page field, and a link

```bash
python scripts/docx_ooxml_patch.py work/sample.docx \
  --header-date "Issued 2026-02-11" \
  --add-page-numbers \
  --hyperlink-first "https://example.org/spec"
```

## 3. A comment, verified structurally

```bash
python scripts/docx_ooxml_patch.py work/sample.docx \
  --add-comment --comment-text "Check this figure"
```

Pass `--contains "…"` to anchor the comment to a chosen paragraph. Confirm it with the checklist in `ooxml/comments.md` — do not trust a render.

## 4. A tracked replacement

Given an existing `<w:ins w:id="77">` in the document:

```bash
python scripts/docx_ooxml_patch.py work/sample.docx \
  --enable-track --tracked-replace-ins-id 77 --new-text " revised"
```

The tool retires that insertion as a deletion and adds a new insertion beside it, picking unused `w:id` values unless you override them.

## 5. Look at the result

Follow `tasks/verify_render.md` to turn the DOCX into PNGs and read them.
