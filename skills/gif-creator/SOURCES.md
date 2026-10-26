# Sources and notices

This package reimplements the entry-point workflow from the user-supplied repository snapshots `gif-creator`. Supporting tools and selected references were retained where useful; their provenance is the supplied snapshot, not a new upstream retrieval. The installed package is self-contained and does not read the original snapshots.

Preserved notices: [LICENSE.txt](LICENSE.txt). Adapted third-party material retains those terms; new repository contributions follow the repository MIT license.

## deepseek: adaptation retrieved 2026-10-26

Source: [https://github.com/deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness/tree/22ddee3792402c3e70ec5f86a63c3e3e895a2f60), revision `22ddee3792402c3e70ec5f86a63c3e3e895a2f60`. License: MIT; retained in [LICENSE-deepseek.txt](LICENSE-deepseek.txt).

Adapted record-browser-gif workflow and encode_gif.py for existing gif-creator. Supports ordered screenshots and video trims, speed, final holds, palette and byte budgets. Local change stages encoding and validation before replacing the requested destination, preserving prior output on failure. No browser recording or upload happens implicitly.
