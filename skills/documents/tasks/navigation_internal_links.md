# Navigation for long documents

Choose navigation according to the recipient's task. A short memo may need only semantic headings; a long reference document may benefit from a contents page and return links. Preserve the template's outline hierarchy and avoid adding repetitive navigation that interrupts reading.

For a contents page with updating page numbers, follow [the TOC workflow](toc_workflow.md). A Word field must be refreshed in a compatible editor before its page references can be checked. If field evaluation is unavailable, offer a static chapter list with internal links and label that limitation clearly. This follows the native-structure and verification guidance recorded in [Sources and notices](../SOURCES.md).

## Static navigation helper

`scripts/internal_nav.py` uses Python, `python-docx`, and `lxml`. It recognizes heading styles and outline levels, adds heading bookmarks, and creates a static contents block. Its defaults also include return links, Top/Bottom bookmarks, and a quick-links row. Review `--help` and inspect existing bookmark names before running it on a document that already contains navigation.

```sh
python scripts/internal_nav.py handbook.docx --out navigable.docx --toc_title 'Chapter guide' --levels 1 2
```

Use `--no_quicklinks` or `--no_top_bottom` when those additions are unnecessary. Figure/table shortcuts depend on existing `figN`/`tblN` bookmarks; [caption tools](captions_crossrefs.md) can establish those before navigation is generated. Avoid repeating the generation step without inspecting its previous additions.

## Check behavior, not just appearance

Confirm each bookmark has paired boundaries and a unique ID/name appropriate to its use. Internal links use `w:anchor` to name a bookmark; they do not need an external URL relationship. Renaming a bookmark requires updating its incoming anchors.

Open representative forward and return links in a compatible editor. Test the first and last chapter, any duplicate heading text, and caption shortcuts. Render the final DOCX to inspect line wrapping and contents layout, but do not count a PNG review as a successful hyperlink test. A PDF companion may have different link behavior and needs its own checks.

Keep the navigation labels synchronized after chapter edits. Static entries do not update automatically, and never imply page accuracy by inserting guessed numbers.
