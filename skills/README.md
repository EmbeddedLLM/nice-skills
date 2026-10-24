# Skill catalog

Each directory is independently installable, including its bundled resources. No skill requires a paid model-provider API, hosted artifact platform, or paid image-generation service. Install only the local dependencies for the selected task; offline production can still require initial package/browser/model downloads. The [dependency reference](../DEPENDENCIES.md) lists every required and optional tool, the tested versions, and install commands.

Research guidance draws on the permitted Adaptive Deep Research reference; the office workflows use Design Office Artifacts. `security-audit` is a vendored MIT skill from Cloudflare, and `design-taste` is a vendored MIT skill from taste-skill. Each affected skill carries its own source record, pinned revision, and retained licence notice in a `SOURCES.md`. The source records describe the scope of each adaptation; they do not certify every retained asset's provenance.

| Skill | Purpose and boundary | Local requirements |
| --- | --- | --- |
| [deep-research](deep-research/SKILL.md) | Iterative needs clarification, evidence synthesis, product comparisons, and cited reports | Supplied sources; search and browser access for live research and forum inspection |
| [doc-coauthoring](doc-coauthoring/SKILL.md) | Drafting and reader-focused revision, including internal communications | Source material and text editing |
| [documents](documents/SKILL.md) | Word creation, edits, comments, revisions, and page review | Python; LibreOffice Writer and Poppler for rendering |
| [pdf](pdf/SKILL.md) | PDF extraction, authoring, edits, forms, OCR, redaction, and validation | Python; optional Poppler, OCR, conversion, or Node tools |
| [slides](slides/SKILL.md) | Presentation story, editable decks, and six bundled template families | Python or PptxGenJS; LibreOffice Impress and Poppler for rendering |
| [spreadsheets](spreadsheets/SKILL.md) | Local workbook/CSV analysis, edits, formulas, and cache checks | openpyxl; LibreOffice for recalculation |
| [frontend-design](frontend-design/SKILL.md) | Websites, application UI, and portable interactive HTML | Existing project stack or plain HTML; browser |
| [design-taste](design-taste/SKILL.md) | Art direction, no-slop house rules, and a measured look-and-fix gate for landing pages and app screens, with four credited example screenshots | Node 22+ and an installed Chrome, Edge, or Chromium for the inspector; network only for asset search |
| [webapp-testing](webapp-testing/SKILL.md) | Browser interaction, failure-state, and visual verification | Existing browser tests or Python Playwright/Chromium |
| [canvas-design](canvas-design/SKILL.md) | Static posters/covers and composed PNG/PDF artwork | Local drawing tool and fonts |
| [algorithmic-art](algorithmic-art/SKILL.md) | Seeded procedural art and interactive exploration | Browser Canvas/SVG; dependency-free starter included |
| [vector-art](vector-art/SKILL.md) | Editable SVG creation/conversion and 44 style recipes | Python; Playwright/Chromium for previews |
| [gif-creator](gif-creator/SKILL.md) | Compact GIF loops, palettes, timing, and size checks | Pillow; optional FFmpeg |
| [create-motion-videos](create-motion-videos/SKILL.md) | Code-rendered films, explainers, launches, and loops | Node, FFmpeg, Chromium; optional local audio/TTS |
| [explainer-video](explainer-video/SKILL.md) | Narration-led explanations from supplied audio and authored scenes; optional paid TTS | Python, FFmpeg/ffprobe; Bash and jq for final delivery |
| [presenter-video](presenter-video/SKILL.md) | Presenter-led edits from supplied footage; optional authorized presenter generation | Python, FFmpeg/ffprobe, Bash, jq |
| [theme-factory](theme-factory/SKILL.md) | Theme selection/application, contrast checks, and offline exports | Python standard library; browser for previews |
| [mcp-builder](mcp-builder/SKILL.md) | MCP server design, contracts, implementation, and protocol checks | Project's Python/TypeScript SDK and local test client |
| [resolve-recipients](resolve-recipients/SKILL.md) | Identity disambiguation and bounded audiences without sending | Supplied roster/history or authorized integrations |
| [review-agent](review-agent/SKILL.md) | Read-only code-change review of outcomes, contracts, defects, and concrete simplifications; optional authorized subagents | Git, source access, applicable local tests |
| [security-audit](security-audit/SKILL.md) | Source-first vulnerability audit in six phases, including guidance-only answers to narrower security questions | Node.js 18+ for the two validators; source access and a local sandbox for any target execution |
| [skill-creator](skill-creator/SKILL.md) | Portable skill authoring and validation | Python; PyYAML for structural checks |

Choose by deliverable: use canvas-design for a composed static graphic, vector-art for editable SVG, algorithmic-art for procedural exploration, gif-creator for GIF, and create-motion-videos for code-rendered motion. Explainer-video follows locked narration and an explanatory storyboard; presenter-video edits a visible speaker's footage. These packages are independently usable. Theme-factory supplies reusable colors and typography roles; the artifact's own workflow handles its content and layout. Frontend-design includes standalone HTML export; webapp-testing owns verification of existing interfaces. Design-taste supplies the art direction, house rules, browser measurements, and critique loop when a page must look designed rather than merely work; it is usable without frontend-design and replaces none of its implementation guidance. Review-agent reads a change; security-audit audits a codebase's trust boundaries and writes validated findings.

Motion, slides, canvas-design, frontend-design, and gif-creator include optional Openverse asset acquisition guidance. Each keeps its own instructions, uses verified local assets and accompanying credits, and retains a supplied/procedural fallback. Network access is needed only when acquiring external media; no Openverse account or paid provider is required for the documented anonymous searches.

The motion package contains 51 Lemo style packages, 98 cinematic references, two twoclipping variants, and two attributed prompt libraries (703 community briefs and 15 motion-design style prompts) that name techniques without replacing the package's own workflow. It also bundles a hand-painted cartoon starter kit, one still per MG style with a 4K paper texture and a 2K studio HDRI (CC0), and a lyric-alignment pipeline; each bundle is hash-pinned in its `references/vendored-assets.json` or `examples/vendored-assets.json` and named from `SKILL.md`. Some upstream demos reference absent optional production media; the bundle is not a promise that every demo renders without preparation. The theme package supplies 51 themes across ten moods including Lavender. Original asset and source notices remain inside each package.

Software and code-based creative workflows apply YAGNI, reuse existing capabilities before adding infrastructure, validate uncertain approaches, and simplify after verification. Extra complexity for speculative race or security edge cases requires an explained trade-off and user buy-in. These instructions are bundled within each relevant skill so a standalone copy does not depend on this repository's agent instructions.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the format, authoring conventions, and verification steps.

Executable helper contracts and the coverage inventory are documented in [tests/README.md](../tests/README.md). CI runs these alongside formatting and skill-local regressions; agent behavior and visual quality still require separate verification.
