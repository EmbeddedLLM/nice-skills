# OOXML notes: tracked changes (genuine redlines)

## Reach for this when the revision must be a revision

If the deliverable has to show up in Word's Reviewing pane as an insertion or deletion attributed to an author, no amount of `python-docx` styling will do it — the library has no tracked-change API. The change has to be expressed in `w:ins` / `w:del` markup.

## What has to be in place

- `word/settings.xml` — `<w:trackRevisions/>` turns recording on for anything edited afterwards.
- `word/document.xml` — inserted runs sit inside `<w:ins …>`, removed runs inside `<w:del …>`.

## Rules that keep the file loadable

| Rule                                                       | Why                                                                         |
| ---------------------------------------------------------- | --------------------------------------------------------------------------- |
| `w:id` is an integer string and unique across the document | Word keys revisions by id; a collision merges or drops them                 |
| set `w:author` and `w:date` on every revision element      | without them the change is attributed to nobody and some viewers hide it    |
| deleted text lives in `<w:delText>`, never `<w:t>`         | `<w:t>` inside `<w:del>` is invalid and Word repairs the file               |
| operate on runs, not on paragraph text                     | Word fragments a sentence across many runs; paragraph-level edits miss them |
| `xml:space="preserve"` where spaces matter                 | leading/trailing blanks are otherwise dropped on load                       |

## Shape of a tracked word swap

Delete the old run and insert the new one next to it:

```xml
<w:del w:id="41" w:author="Reviewer" w:date="2026-02-11T09:30:00Z">
  <w:r><w:delText xml:space="preserve"> quarterly </w:delText></w:r>
</w:del>
<w:ins w:id="42" w:author="Reviewer" w:date="2026-02-11T09:30:00Z">
  <w:r><w:t xml:space="preserve"> annual </w:t></w:r>
</w:ins>
```

## Let the patcher allocate ids

`scripts/docx_ooxml_patch.py` is the runnable version of the above. It can switch on `<w:trackRevisions/>`, turn an existing `<w:ins>` into a `<w:del>`, and add a fresh `<w:ins>` beside it.

Its defaults (`--del-id auto --ins-id auto`) are what you want almost always: the tool walks the document, collects the ids already in use, and picks unused ones. Pass explicit integers only when reproducing a known revision.

## Verifying

1. Structural pass first — ids unique, `delText` used for deletions, author and date present.
2. Then a layout pass: render to PDF/PNG per `tasks/verify_render.md` and confirm nothing reflowed unexpectedly.
3. Renders do display redlines, but a render that looks right can still hide malformed revision markup. Do not skip step 1.
