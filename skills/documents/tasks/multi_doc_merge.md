# Combining Word documents without losing dependencies

Establish the chapter order and which source governs styles, page setup, numbering, headers, and review history. Inspect both packages before choosing a merge route. Native paragraphs may refer to styles, list definitions, comments, bookmarks, notes, media, and relationship IDs elsewhere in the archive; copying those paragraphs does not copy their dependencies.

Follow the preservation approach recorded in [Sources and notices](../SOURCES.md). Use an editor's document-insertion facilities or an available dependency-aware merger when cross-document IDs must be reconciled. Verify that route on a representative copy rather than assuming it preserves every Word feature.

## Limited body append

`scripts/merge_docx_append.py` is appropriate when the caller has established compatible styles, numbering, relationships, and identifiers. It requires Python and `lxml`.

```sh
python scripts/merge_docx_append.py volume.docx appendix.docx --out combined.docx
```

The base archive remains the package source. Appendix body elements are inserted before the base's final section properties; the appendix's final section properties are omitted. Embedded section properties inside appended paragraphs still exist and require review. No appendix style, list, note, comment, media, or relationship part is imported. A coincidentally matching ID can point to the wrong base object, not merely an absent one.

Drawings and VML pictures cause a failure before output is published. `--allow_drawings` suppresses that refusal; it does not import images or resolve their relationships. Use the option only after separately establishing that all referenced parts are compatible. Existing output is replaced atomically after a successful splice.

## Verification

Check chapter order, transition spacing, list restarts, table widths, notes and references against the inputs. Inspect relationship targets and identifiers in the appended content. Review [section layout](sections_layout.md), [comments](comments_manage.md), and [revision handling](clean_tracked_changes.md) when those features exist. Preserve review decisions rather than accepting changes merely to make a merge easier.

Render the saved result with `render_docx.py`; inspect section boundaries and all pages containing complex objects. If dependencies cannot be reconciled with available tools, identify that limitation and preserve the separate source documents. Do not deliver a body-only splice as a fully faithful merger.
