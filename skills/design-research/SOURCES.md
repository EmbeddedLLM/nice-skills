# Sources and notices

Adapted from [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/28b3b8dee8c976df4fa3e94aed4e092ad43fcb03), revision `28b3b8dee8c976df4fa3e94aed4e092ad43fcb03`, retrieved 2026-10-26. MIT, copyright 2024 Next Level Builder; full notice in [LICENSE.txt](LICENSE.txt).

Bundled the source `data/` and five Python scripts for offline BM25 retrieval, stack guidance, provenance validation, and design-system suggestions. The entry point is rewritten for portable, optional research that preserves an existing design system. Installer, plugin metadata, screenshots, generated projects, and duplicated CLI assets are excluded.

The catalogs contain metadata and links, not font binaries or icon artwork. Keep [data/data-provenance.json](data/data-provenance.json) and font-license records with the package. A suggestion is not a license grant or a verified claim about the current version of a framework. Verify source records and the installed version before applying guidance or fetching assets. Scoring is retrieval relevance, not a quality or accessibility certification.

Search and generation use Python's standard library. `--persist` writes project files only when explicitly requested; use a new output directory and review before replacing existing design documents. No accounts, paid services, or network calls are needed for the documented local commands.

Local formatting follows repository conventions except the font-license and icon JSON snapshots, whose upstream byte hashes are preserved and verified by the data validator. Six upstream semantic test modules are adapted in the repository test suite, outside the installable skill.
