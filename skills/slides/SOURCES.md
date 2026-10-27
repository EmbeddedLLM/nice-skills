# Sources and notices

Browse the [material catalogue](references/material-catalogue.json) for local paths, uses, source links, revisions, and recorded licenses. Unresolved provenance fields are written as `"Unknown"`; the catalogue does not replace the notices and scope below.

## Replacement work for issue 6

The supporting files listed below replace the internal-export carry-over identified in [issue 6](https://github.com/jiahuei/agentic-skills/issues/6). Helpers were reimplemented from their public interfaces, artifact contracts, and regression requirements; matching an interface does not require retaining its old implementation. The prose now uses the supplied **Design Office Artifacts** permissive-source revision as its main reference, adapted to this package's local tools and preservation requirements.

The [source manifest](references/source-manifest.json) records the exact reference inputs, their hashes, the selected upstream revisions, and the retained license/notice files. The supplied package's recorded license review is the basis for this selection; it is not a new ownership-chain audit. Its original MIT text is retained in [LICENSE.design-office-artifacts.txt](LICENSE.design-office-artifacts.txt), with [NOTICE.design-office-artifacts.txt](NOTICE.design-office-artifacts.txt) and the applicable upstream texts under `licenses/`. Preserve those notices with redistribution. Adaptations to Apache-derived guidance are identified in the changed guides and the manifest.

Original replacement implementations and examples use [the repository MIT license](LICENSE.repository.txt). No reference-package runtime, external engine, font, palette, or sample artifact was imported for this replacement. The skill remains usable independently; local `__ref__/` directories are authoring inputs, not runtime dependencies.

### Replaced files

- `pptxgenjs_helpers/code.js`
- `pptxgenjs_helpers/index.js`
- `pptxgenjs_helpers/latex.js`
- `pptxgenjs_helpers/layout.js`
- `pptxgenjs_helpers/svg.js`
- `pptxgenjs_helpers/text.js`
- `pptxgenjs_helpers/util.js`
- `references/template_following.md`

## Scope limits and other materials

The earlier package was assembled from user-supplied snapshots. This remediation covers the enumerated files, not a blanket relicense of every retained file. Similarity scores are review signals, not proof of rights or independent authorship. Existing separately attributed schemas, dependencies, and assets retain their terms; future retrieved third-party content needs its own permission.

Bundled Office schema provenance is recorded in [PROVENANCE.md](scripts/office/schemas/PROVENANCE.md).

The replacement template pack comes from the supplied `__ref__/ppt-templates` snapshot. Preserve [template reuse permission](slide_templates/Template_Reuse_Permission.txt) and the separate [DejaVu font notice](slide_templates/Fonts/LICENSE_DEJAVU.txt).

## deer-flow: adaptation retrieved 2026-10-26

Source: [https://github.com/bytedance/deer-flow](https://github.com/bytedance/deer-flow/tree/f7d02a75151e2cdb8222805124d430b815e53e35), revision `f7d02a75151e2cdb8222805124d430b815e53e35`. License: MIT; retained in [LICENSE-deer-flow.txt](LICENSE-deer-flow.txt).

Adapted image-plan composition as an explicit raster-deck mode using local images, aspect-ratio-preserving placement, and notes. Added strict count/ratio validation and centered contain placement. Editable decks remain the default; paid image generation and DeerFlow-specific paths are not required.
