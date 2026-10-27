# Sources and notices

Browse the [material catalogue](references/material-catalogue.json) for local paths, uses, source links, revisions, and recorded licenses. Unresolved provenance fields are written as `"Unknown"`; the catalogue does not replace the notices and scope below.

## Replacement work for issue 6

The supporting files listed below replace the internal-export carry-over identified in [issue 6](https://github.com/jiahuei/agentic-skills/issues/6). Helpers were reimplemented from their public interfaces, artifact contracts, and regression requirements; matching an interface does not require retaining its old implementation. The prose now uses the supplied **Design Office Artifacts** permissive-source revision as its main reference, adapted to this package's local tools and preservation requirements.

The [source manifest](references/source-manifest.json) records the exact reference inputs, their hashes, the selected upstream revisions, and the retained license/notice files. The supplied package's recorded license review is the basis for this selection; it is not a new ownership-chain audit. Its original MIT text is retained in [LICENSE.design-office-artifacts.txt](LICENSE.design-office-artifacts.txt), with [NOTICE.design-office-artifacts.txt](NOTICE.design-office-artifacts.txt) and the applicable upstream texts under `licenses/`. Preserve those notices with redistribution. Adaptations to Apache-derived guidance are identified in the changed guides and the manifest.

Original replacement implementations and examples use [the repository MIT license](LICENSE.repository.txt). No reference-package runtime, external engine, font, palette, or sample artifact was imported for this replacement. The skill remains usable independently; local `__ref__/` directories are authoring inputs, not runtime dependencies.

### Replaced files

- `ooxml/hyperlinks_and_fields.md`
- `scripts/a11y_audit.py`
- `scripts/apply_template_styles.py`
- `scripts/comments_apply_patch.py`
- `scripts/comments_extract.py`
- `scripts/content_controls.py`
- `scripts/google_docs_title_sanitize.py`
- `scripts/insert_note.py`
- `scripts/insert_toc.py`
- `scripts/merge_docx_append.py`
- `scripts/render_and_diff.py`
- `scripts/table_geometry.py`
- `scripts/watermark_add.py`
- `scripts/watermark_audit_remove.py`
- `tasks/clean_tracked_changes.md`
- `tasks/equations.md`
- `tasks/forms_content_controls.md`
- `tasks/multi_doc_merge.md`
- `tasks/navigation_internal_links.md`
- `tasks/sections_layout.md`
- `tasks/watermarks_background.md`

## Scope limits and other materials

The earlier package was assembled from user-supplied snapshots. This remediation covers the enumerated files, not a blanket relicense of every retained file. Similarity scores are review signals, not proof of rights or independent authorship. Existing separately attributed schemas, dependencies, and assets retain their terms; future retrieved third-party content needs its own permission.

Bundled Office schema provenance is recorded in [PROVENANCE.md](scripts/office/schemas/PROVENANCE.md).
