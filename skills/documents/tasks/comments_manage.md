# Task: comments — extract, remove, or keep for review

## Pick the mode before touching the file

| Mode   | Deliverable                                                    | Tools                                             |
| ------ | -------------------------------------------------------------- | ------------------------------------------------- |
| Review | a commented `.docx` with reviewer notes intact                 | `comments_add.py`, `comments_apply_patch.py`      |
| Final  | a clean `.docx` with comments gone, revisions usually accepted | `accept_tracked_changes.py` + `comments_strip.py` |
| Triage | a machine-readable list of comments to summarise               | `comments_extract.py`                             |

Word's "resolved" flag does not survive a `python-docx` round trip reliably, so these scripts stick to operations that do.

## Inserting new comments

For a single comment, or one anchored at a specific place, follow `ooxml/comments.md` and use `scripts/docx_ooxml_patch.py --add-comment`.

For many comments at once, `comments_add.py` anchors each one by searching for a substring:

```bash
python scripts/comments_add.py contract.docx --out reviewed.docx \
  --author "Reviewer" \
  --add "Payment Terms=Please confirm Net 45 is acceptable." \
  --add "Governing Law=Prefer Delaware; any constraints?" \
  --ignore_case
```

- Each `--add` is `contains=text`, and the flag repeats.
- Matching scans ordinary text _and_ deleted text (`w:delText`), so anchors are still found in documents carrying tracked changes.
- A pattern with no match produces a warning; pass `--require_all` to make it a hard failure instead.

## Updating or resolving comments that already exist

Extract first to learn the ids, then apply a patch file:

```bash
python scripts/comments_extract.py reviewed.docx --out comments.json
python scripts/comments_apply_patch.py reviewed.docx patch.json --out reviewed_v2.docx
```

The patch is JSON with an `ops` list; each op names a comment `id` and one action:

```json
{
  "ops": [
    { "id": 0, "append": "Follow-up note" },
    { "id": 0, "replace": "Full replacement text" },
    { "id": 0, "resolved": true }
  ]
}
```

`"resolved": false` clears the flag again.

## Extracting for triage

```bash
python scripts/comments_extract.py contract.docx --out comments.json
```

Each entry carries the comment text, author, date when the package records one, and the snippet it is anchored to.

## Removing every comment

```bash
python scripts/comments_strip.py contract.docx --out no_comments.docx
```

That deletes comment ranges and references from all story parts — main document plus headers and footers — and drops `word/comments.xml` together with its relationships and content-type override.

## Producing a clean final document

```bash
python scripts/accept_tracked_changes.py contract.docx --mode accept --out accepted.docx
python scripts/comments_strip.py accepted.docx --out final_clean.docx
python render_docx.py final_clean.docx --output_dir out_final_clean
```

## Pitfalls

- Comments anchored in a header or footer are easy to miss. Stripping has to cover every story part, which is why `comments_strip.py` does.
- Newer Word writes `commentsExtended.xml`; the stripper removes it when it is there.
- After stripping, render and read the pages around the old anchors to confirm no text went with them.
