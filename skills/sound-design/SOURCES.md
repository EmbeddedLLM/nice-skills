# Sources and notices

Browse the [material catalogue](references/material-catalogue.json) for local paths, uses, source links, revisions, and recorded licenses. Unresolved provenance fields are written as `"Unknown"`; the catalogue does not replace the notices and scope below.

## earshot: adaptation retrieved 2026-10-26

Source: [https://github.com/Leonxlnx/earshot](https://github.com/Leonxlnx/earshot/tree/591fa3e028032e6dce56620a20e932e35667e8d8), revision `591fa3e028032e6dce56620a20e932e35667e8d8`. License: MIT; retained in [LICENSE-earshot.txt](LICENSE-earshot.txt).

Adapted the model-free procedural synthesis tier: 237 presets (including all 51 new v0.4 sounds), recipe modules, DSP/effects, and tone math. The portable sfx.py CLI renders these presets with their stored parameters and seeds. No recordings, model weights, model scores, API clients, MCP registration, reference fitting, or search optimizer are included. The 15 recording-fitted presets are excluded; this bundle makes no realism-classifier or listening claims. Upstream recipe authoring/benchmark routines are retained as reference code but are not exposed by this CLI. Local modifications: lightweight package initializer; JIT acceleration is a pinned dependency after the Python fallback proved too slow; on-disk JIT caching is disabled to keep installed skills read-only.
