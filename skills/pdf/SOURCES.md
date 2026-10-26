# Sources and notices

## Replacement work for issue 6

The supporting files listed below replace the internal-export carry-over identified in [issue 6](https://github.com/jiahuei/agentic-skills/issues/6). Helpers were reimplemented from their public interfaces, artifact contracts, and regression requirements; matching an interface does not require retaining its old implementation. The prose now uses the supplied **Design Office Artifacts** permissive-source revision as its main reference, adapted to this package's local tools and preservation requirements.

The [source manifest](references/source-manifest.json) records the exact reference inputs, their hashes, the selected upstream revisions, and the retained license/notice files. The supplied package's recorded license review is the basis for this selection; it is not a new ownership-chain audit. Its original MIT text is retained in [LICENSE.design-office-artifacts.txt](LICENSE.design-office-artifacts.txt), with [NOTICE.design-office-artifacts.txt](NOTICE.design-office-artifacts.txt) and the applicable upstream texts under `licenses/`. Preserve those notices with redistribution. Adaptations to Apache-derived guidance are identified in the changed guides and the manifest.

Original replacement implementations and examples use [the repository MIT license](LICENSE.repository.txt). No reference-package runtime, external engine, font, palette, or sample artifact was imported for this replacement. The skill remains usable independently; local `__ref__/` directories are authoring inputs, not runtime dependencies.

### Replaced files

- `examples/smoke_test.md`
- `js/extract_text_pdfjs.mjs`
- `js/fill_form.mjs`
- `scripts/compare_renders.py`
- `scripts/create_montage.py`
- `scripts/edit_smoketest.py`
- `scripts/forms_smoketest.py`
- `scripts/pdf_edit.py`
- `scripts/place_text_by_boxes.py`
- `scripts/renderer_parity.py`
- `tasks/batch.md`
- `tasks/compare.md`
- `tasks/convert.md`
- `tasks/coords.md`
- `tasks/create.md`
- `tasks/edit.md`
- `tasks/extract.md`
- `tasks/forms_annotations.md`
- `tasks/forms_debugging.md`
- `tasks/forms_nonfillable.md`
- `tasks/js_tools.md`
- `tasks/preflight.md`
- `tasks/read_review.md`
- `tasks/redact.md`
- `troubleshooting/common.md`

## Scope limits and other materials

The earlier package was assembled from user-supplied snapshots. This remediation covers the enumerated files, not a blanket relicense of every retained file. Similarity scores are review signals, not proof of rights or independent authorship. Existing separately attributed schemas, dependencies, and assets retain their terms; future retrieved third-party content needs its own permission.

Optional PyMuPDF redaction has AGPL/commercial licensing; local free use is available under its open-source terms. It is not required for ordinary extraction or forms. Check redistribution/application obligations for the chosen dependency route; this package does not grant a commercial license.
