# Sources and provenance

Browse the [material catalogue](references/material-catalogue.json) for local paths, uses, source links, revisions, and recorded licenses. Unresolved provenance fields are written as `"Unknown"`; the catalogue does not replace the notices and scope below.

Reference colours and displayed like counts were observed on **20 October 2026** during the guide refresh. This skill was packaged on **21 October 2026 (Asia/Kuala_Lumpur)** from that guide; packaging did not re-fetch popularity data.

- Color Hunt Vintage: https://colorhunt.co/palettes/vintage
- Color Hunt Popular, with All time selected: https://colorhunt.co/palettes/popular
- Coolors Trending: https://coolors.co/palettes/trending

The live rendered pages supplied colours and counts after text-only retrieval did not expose the dynamic palette data. Color Hunt records retain their exact palette URLs. Coolors records cite the observed trending collection and retain exact reference swatches, allowing the combination to be identified even when ordering changes. Some report names are editorial. Counts are displayed rounded values where the site used K notation.

The guide contains curated selections from the observed pages, including recent vintage examples and all-time favourites. It is **not** a global top-50 ranking, nor a ranking of all vintage palettes. Editorial ordering balances mood and usability. The exact reference swatches are stored separately from derived UI roles; generated dark/light support shades do not claim source popularity independently.

Lavender comes from the user's supplied nine colours and roles, preserved in the guide's `lavender-ledger-data` block. It is separate from the Coolors reference called Soft Lavender.

## Reuse scope

This package includes selected colour values, source metadata, original role mappings, utility code and the user's guide. It does not bundle source-site artwork, screenshots, logos, fonts or code. No open-source licence is asserted for the third-party community references. Do not reuse the MIT/Apache claims from the previous software-theme collection. Source-site terms are linked in each record; a reference URL does not itself establish permission to redistribute the site's assets.

## Technical references carried by the guide

- Text contrast: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- Non-text contrast: https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html
- Non-colour cues: https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html
- Office colour scheme structure: https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.colorscheme

These links explain the implementation concepts. The current packaging task did not re-fetch them. Numerical checks use the standard sRGB relative-luminance formula and final opaque HEX values; XML is validated structurally, not in native PowerPoint.

## hallmark: adaptation retrieved 2026-10-26

Source: [https://github.com/Nutlope/hallmark](https://github.com/Nutlope/hallmark/tree/7ec868225c6caa040558c321ee0fefa0e73f83a8), revision `7ec868225c6caa040558c321ee0fefa0e73f83a8`. License: MIT; retained in [LICENSE-hallmark.txt](LICENSE-hallmark.txt).

Adapted 48 theme recipes as optional material references, with a local list/show/CSS exporter. Excluded preview photographs, screenshots, photo catalogs, paid generation, installers, hooks, and automatic project mutation. These are web material recipes, separate from the existing 51 cross-format palettes. Font names are suggestions, not bundled font files; use installed fallbacks or acquire fonts with their own notices.
