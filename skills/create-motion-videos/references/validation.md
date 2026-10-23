# Validation — 2026-10-21 (Asia/Kuala_Lumpur)

- Bundle: 1,882 files; 51 Lemo styles, 98 cinematic references and two twoclipping variants. All manifests and font/model dependency checks pass.
- Font resources: 105 original binaries across 77 OFL families; all parse with fontTools and load successfully in Chromium 153. All 251 static font-face target URLs resolve.
- Restored textures: all nine shared Poly Haven JPGs decoded in-browser; repeat captures matched.
- Starter, Whiteboard engine/stroke data, and Swiss Motion typography: exact PNG hashes match forward, reverse and fresh-context seeks. An independent original Whiteboard composition passed at 1920×1080.
- Export: a 0.5-second sample with four temporal samples per frame produced six frames at 12 fps, 640×360; FFprobe confirmed those values.
- Setup: project preparation preserves an existing TREATMENT.md, excludes repository-bound build tools, and preserves style engines/resources. Runtime preparation and reuse pass; a changed bundle fingerprint rejects an old runtime.
- Negative check: missing font URL is detected by asset preflight.

## Scope limits

This does not certify every original demonstration film. The full source-tree literal scan still finds 274 noncritical references (259 HTML references and 15 fetch/loader references), including omitted gallery images, archived source pages, generated demo outputs, optional HDR packs and production data absent upstream. These are not silently treated as present. The actual film must pass `audit_assets.py --strict` and strict browser capture after preparing its own narration and media. Dynamic paths and glyph coverage require browser/content checks. See runtime.md and font-replacements.md.
