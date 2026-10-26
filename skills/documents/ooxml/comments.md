# OOXML notes: real Word comments

## Start from the package, not the render

A comment that is wired incorrectly still shows up as ordinary text in some viewers, and a comment that is wired _correctly_ frequently shows up as nothing at all in headless LibreOffice. Rendered pages therefore prove very little here. Treat the ZIP as the source of truth and verify structurally.

## The three cooperating parts

A comment only exists once all three of these agree on the same `w:id`.

**1. Body text — `word/comments.xml`**

Holds the comment content, one `<w:comment w:id="…">` per comment, each with at least one paragraph inside it.

**2. Anchors — `word/document.xml`**

Marks where the comment attaches:

- `<w:commentRangeStart w:id="…"/>` immediately before the first covered run
- `<w:commentRangeEnd w:id="…"/>` immediately after the last covered run
- a run _after_ the range end holding `<w:commentReference w:id="…"/>`

**3. Registration — relationships plus content types**

In `word/_rels/document.xml.rels`, one relationship whose `Type` is `http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments` and whose `Target` is `comments.xml`.

In `[Content_Types].xml`, one override:

```xml
<Override PartName="/word/comments.xml"
  ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
```

## Order of operations

1. Locate the runs in `document.xml` that the comment should cover.
2. Drop `commentRangeStart` in front of them and `commentRangeEnd` behind them.
3. Append the reference run after the range end.
4. Add the matching `<w:comment>` body to `comments.xml`, creating that part only if the package has no comments yet.
5. Register the part (relationship, then override) unless both are already there.

## Prefer the patcher over hand-editing

`scripts/docx_ooxml_patch.py --add-comment` handles the boring parts and is safe to run against a document that already carries comments:

- it scans the package and allocates an unused comment id,
- it _appends_ to an existing `word/comments.xml` rather than rebuilding it,
- it reuses a comments relationship that is already present instead of creating a second one.

Anchor it with `--contains` when the comment should attach somewhere other than the default location.

## Confirming the result

Work through this list against the unpacked package:

| Check                                                         | Where                          |
| ------------------------------------------------------------- | ------------------------------ |
| `word/comments.xml` is in the ZIP                             | package listing                |
| comments relationship present exactly once                    | `word/_rels/document.xml.rels` |
| override present                                              | `[Content_Types].xml`          |
| start, end, and reference anchors exist for every comment id  | `word/document.xml`            |
| each `w:id` appears in both `comments.xml` and `document.xml` | both parts                     |
