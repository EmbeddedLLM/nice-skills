# Bundled font resolution

Font audit and retrieval: **2026-10-21 (Asia/Kuala_Lumpur)**.

All production CSS font-face URLs now resolve to bundled, unmodified Google Fonts binaries in `assets/lemo/core/fonts/bundled/`. The 105 font files cover 77 families. Each family carries its SIL Open Font License. See [font-replacements.json](font-replacements.json) for exact source commit, URLs, SHA-256 hashes, file sizes and aliases.

Original font families were obtainable, so the repair preserves the styles’ typography instead of using unrelated system fonts. CSS aliases such as `AD`, `Archivo`, `Fraktur`, `SC`, `PM`, and `Shippori` remain compatible with the drawing code. Historical subset URLs are replaced with complete font binaries; repeated Unicode subset declarations and restrictions were removed. Full CJK fonts support new content beyond the original demos’ text. Validate the exact script and glyphs of each new film; no font promises every Unicode character.

- Whiteboard: Architects Daughter plus the unchanged EMS stroke JSON fonts.
- Swiss Motion: Archivo variable, UnifrakturMaguntia and DM Serif Display.
- CJK: Noto Sans SC, Noto Serif SC, Noto Sans JP and the applicable handwritten/display families.
- Spy Titles: its outline loader reads bundled League Gothic directly.

Serve the full runtime with `/core/` mounted. A selected style’s CSS can then be copied with its project without copying these binaries repeatedly. For portable delivery, include the referenced shared fonts and their OFL notices or rewrite URLs to included project-relative paths.

Eight demo build scripts no longer invoke font downloads. Remaining font-download utilities are explicitly marked optional legacy tools; do not run them in ordinary production, because they can replace corrected CSS with fresh remote subsets. Upstream style guides retain their historical font design terminology; their original per-demo binary filenames are superseded by the executable CSS and this mapping.

Validation: 251 font-face target URLs exist; all 105 added binaries parsed with fontTools. No missing literal font URL remains in the bundled HTML/CSS/JS scan (excluding optional download tools). The archived watercolor music-source webpage has its unrelated external Google Fonts link removed.
