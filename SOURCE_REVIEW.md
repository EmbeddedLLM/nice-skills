# Licensed source adaptations

Reviewed 2026-10-26. This record covers all 17 requested links and the useful implementations they identify. Each adapted skill includes its own pinned `SOURCES.md` and complete applicable license/notice files so it remains independently distributable. Repository licenses cover the identified code or prose; they do not automatically cover linked footage, recordings, fonts, model weights, trademarks, or paid services.

The X pages returned access errors. Their public post text and outbound links were inspected through the FxTwitter public status endpoint; no post text, screenshots, or attached media are redistributed here. Repository source and license files, rather than social claims about licensing or quality, determine the adaptation scope. Links inferred from a product name are identified below. Snapshots are review evidence, not a promise that an upstream branch remains unchanged.

## Requested sources and outcomes

| Requested source | Useful result and disposition |
| --- | --- |
| [Lemo Opuscar](https://github.com/lemomo-ai/lemo-opuscar) | Added eight new documentary/editorial style guides and metadata to `create-motion-videos`, with their own revision and file hashes. The original 51 demo packages and patched runtime remain pinned. Added evidence-led and music-led edit guidance. |
| [Hallmark](https://github.com/Nutlope/hallmark) | Added all 48 material recipes to `theme-factory`, a searchable CSS-token export helper that carries the MIT notice, and material-first selection guidance in `frontend-design`. No screenshots or fonts copied. |
| [Lemomo post](https://x.com/lemomo_ai/status/2110983292027814316) | Confirmed the same eight new styles: Caption News, City Symphony, Countdown, Kino Montage, News Package, Newsreel, Telestrator, Visual Investigation. These are guidance additions, not eight runnable demo films. |
| [Zmdsb collection](https://x.com/zmdsb259414/status/2113140946699460933) | Adapted image reconstruction, Blender assembly, interactive diorama, and shot-planning logic into `procedural-3d` and motion references. Lemo and MG Styles 15 overlap existing bundles. Motion2MixamoRig has restricted upstream models; no pipeline/weights imported. Jianying repository was unavailable. |
| [Nutlope post](https://x.com/nutlope/status/2113316017510191578) | Hallmark v2 is covered by the 48-recipe import and export tests above. |
| [Okapi audio collection](https://x.com/okapi_fukugyo/status/2113390079368667563) | Added procedural Earshot synthesis, peak-aligned cues, mixing, and per-item licensing guidance in `sound-design`. Stock libraries have separate conditions; no stock audio or ElevenLabs client added. |
| [Lexnlin Earshot post](https://x.com/lexnlin/status/2113393065427620076) | Bundled the model-free synthesis tier: 237 presets including all 51 new v0.4 sounds, deterministic recipes, and a local WAV/mix CLI. Excluded 15 recording-fitted presets, recordings, learned models, and hosted services. |
| [Peko game skills](https://x.com/peko1487584/status/2113459788680221042) | Added `game-development`: all 76 specialized guides present in the inspected revision, supporting references, starter assets, nine helpers, and retained Apache notices. The post's earlier count was 74. Seven upstream regression suites exercise the helpers. |
| [Shadcnlabs video tools](https://x.com/shadcnlabs/status/2113615826326860013) | Adapted Snapcn's content/scene selection and duration budgeting into motion guidance. No Pro components or Remotion runtime bundled. Rive, Jitter, Shots, Screen Studio, Mobbin, and Fontshare are optional separate tools/resources, not a license to copy their libraries or output examples. |
| [Dave Kiss robustness advice](https://x.com/davekiss/status/2113363042247512161) | Existing project rules already require evidence and buy-in for speculative robustness. The new engineering workflow follows that rule; no duplicate process machinery or copied post text added. |
| [Amir design collection](https://x.com/AmirMushich/status/2113692928824484078) | Adapted Impeccable's task-specific design passes, UI UX Pro Max's offline research data/scripts, and semantic-diagram planning. Reused the Lemo, reconstruction, and shot-planning adaptations. Added HyperFrames' frame/cut/phone review logic to the existing renderer. Blender MCP and Penpot are whole applications/connectors; no additional runtime needed. Remotion has separate license limits. |
| [Aman animation resources](https://x.com/amananimates/status/2113599514103906657) | Existing GIF/motion easing covers the reusable technique. Easings.net is GPL-3.0 and was not copied into the permissive packages. ScrollShaders disallows reusable-library redistribution; Scrolltide was inaccessible. No proprietary shaders or Fontshare font binaries imported. |
| [Nixinhai Galaxy UI](https://x.com/nixinhai0/status/2114021822895387009) | Identified Uiverse Galaxy from the product name (the post did not supply a repository URL). Added selective snippet acquisition, provenance, accessibility, and integration review guidance; no bulk widget library copied. |
| [CY AI Design Skills](https://x.com/cy160909/status/2114213361621540994) | The post names `landing-page-design`; `elayadesign/ai-design-skills` is the matching repository found during research, not a verified outbound link from the post. Adapted its licensed page-story and design-to-motion guidance into `frontend-design`; no secondary credited libraries or visual assets copied. |
| [DeerFlow presentation skill](https://github.com/bytedance/deer-flow/tree/main/skills/public/ppt-generation) | Added an explicit raster-slide path to `slides`, with local image composition, centered aspect-preserving placement, notes/credits, and failure-safe output. Editable slides remain the default when editability is required. No model credentials or source brand assets needed. |
| [Addy Osmani agent skills](https://github.com/addyosmani/agent-skills) | Consolidated 25 topics into the task-routed `software-workflow` references instead of installing overlapping lifecycle triggers. Preserved evidence, contracts, testing, profiling, migration, and handoff logic; removed mandatory interviews, universal quotas, automatic publishing, and sibling-skill dependencies. |
| [DeepSeek harness skills](https://github.com/deepseek-ai/deepseek-harness/tree/master/.agents/skills) | Adapted engineering failure ownership, CI reliability, derived state, documentation, performance, and handoff logic; added the real browser-video-to-GIF encoder with tests and staged replacement. DSH APIs, archive locations, plugin art, localization infrastructure, grading policy, and automatic stacked-PR operations remain outside this portable collection. |

## Redistribution boundaries

- Every copied/adapted package above uses MIT, Apache-2.0, or BSD-3-Clause material with its notice retained. New code is described as an adaptation where applicable. Source pins and local changes live with each skill.
- [Motion2MixamoRig's notices](https://github.com/MaxLiu22/Motion2MixamoRig/blob/f05a718188026b06e7ee64b47bab077970444b19/NOTICE) distinguish its Apache code from GVHMR's research/noncommercial terms and SMPL-X's separately gated scientific-research terms. No such weights, body models, or automated installation pipeline is included.
- [ScrollShaders](https://scrollshaders.com/license) prohibits redistribution as a reusable library, including modified items. [Sound Effect Lab](https://soundeffect-lab.info/agreement/) restricts redistribution; [Pixabay](https://pixabay.com/service/license-summary/) restricts standalone distribution. [Freesound](https://freesound.org/help/faq/) uses individual sound licenses; [Mixkit](https://mixkit.co/license/) separates item types. No downloaded recordings are redistributed. A later project must check the exact item and use.
- [Remotion's license](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md) is not a general permissive grant for every organization. No Remotion source/runtime is copied. Snapcn's MIT workflow does not override its runtime's terms, and paid components are excluded.
- [Fontshare](https://www.fontshare.com/licenses), third-party icon catalogs, and linked brand imagery need asset-specific review. Diagram/design imports contain guidance and metadata, not those font/icon/logo binaries. Game starter assets retain their bundled third-party notices.
- [Jianying Headless](https://github.com/mcncarl/jianying-headless) returned repository-not-found during review; [Scrolltide](https://scrolltide.com/) could not be inspected. Neither contributes material. Penpot, Blender MCP, and proprietary editors were assessed as optional tools, not vendored dependencies.

## Adapted implementation pins

The following revisions are the reviewed snapshots. Full notices and narrower file scope are recorded in each destination's `SOURCES.md`.

| Source | Revision | License | Destination |
| --- | --- | --- | --- |
| [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar/tree/413a6bd6d78ebd3bdd5abaec9538a26867f890df) | `413a6bd6d78ebd3bdd5abaec9538a26867f890df` | MIT | create-motion-videos |
| [Nutlope/hallmark](https://github.com/Nutlope/hallmark/tree/7ec868225c6caa040558c321ee0fefa0e73f83a8) | `7ec868225c6caa040558c321ee0fefa0e73f83a8` | MIT | theme-factory, frontend-design |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills/tree/aeac41d4d005999432bb7312f7ff06383a91d59d) | `aeac41d4d005999432bb7312f7ff06383a91d59d` | MIT | software-workflow |
| [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness/tree/22ddee3792402c3e70ec5f86a63c3e3e895a2f60) | `22ddee3792402c3e70ec5f86a63c3e3e895a2f60` | MIT | software-workflow, gif-creator |
| [bytedance/deer-flow](https://github.com/bytedance/deer-flow/tree/f7d02a75151e2cdb8222805124d430b815e53e35) | `f7d02a75151e2cdb8222805124d430b815e53e35` | MIT | slides |
| [img2threejs/img2threejs](https://github.com/img2threejs/img2threejs/tree/954cd5845e90efd045694bab725d68a9863c20e0) | `954cd5845e90efd045694bab725d68a9863c20e0` | Apache-2.0 | procedural-3d |
| [sixtysevenlf/dsh-blender-plugin](https://github.com/sixtysevenlf/dsh-blender-plugin/tree/f9f115f86b3c40fbe8d3dba811283acf71df03f9) | `f9f115f86b3c40fbe8d3dba811283acf71df03f9` | BSD-3-Clause | procedural-3d |
| [blendi-remade/dioramas](https://github.com/blendi-remade/dioramas/tree/868539fb5b64a843071a2247d5d8bacb706a07b1) | `868539fb5b64a843071a2247d5d8bacb706a07b1` | MIT | procedural-3d |
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft/tree/43bd349a136651865ecfa6ea1cf012f6e957d304) | `43bd349a136651865ecfa6ea1cf012f6e957d304` | Apache-2.0 | create-motion-videos |
| [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot/tree/591fa3e028032e6dce56620a20e932e35667e8d8) | `591fa3e028032e6dce56620a20e932e35667e8d8` | MIT | sound-design |
| [gamedev-skills/awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/tree/184b72be02884f782a0058f2eeae2ce4277453e4) | `184b72be02884f782a0058f2eeae2ce4277453e4` | Apache-2.0 | game-development |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable/tree/bce6e0fbfa836a13902a9632d6e1f042747e0bf7) | `bce6e0fbfa836a13902a9632d6e1f042747e0bf7` | Apache-2.0 | frontend-design |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/28b3b8dee8c976df4fa3e94aed4e092ad43fcb03) | `28b3b8dee8c976df4fa3e94aed4e092ad43fcb03` | MIT | design-research |
| [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design/tree/b8f36171da6e1bce05c3eb984969e5d4e7cb3a20) | `b8f36171da6e1bce05c3eb984969e5d4e7cb3a20` | MIT | vector-art |
| [elayadesign/ai-design-skills](https://github.com/elayadesign/ai-design-skills/tree/a2735a3eaf092eaaffb6dc17df25de33ef3bd048) | `a2735a3eaf092eaaffb6dc17df25de33ef3bd048` | MIT | frontend-design |
| [shadcn-labs/snapcn](https://github.com/shadcn-labs/snapcn/tree/d83a98ed00c520fd672535a4bb1d5e81580d4694) | `d83a98ed00c520fd672535a4bb1d5e81580d4694` | MIT | create-motion-videos |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes/tree/c9e86a3b01199e78b4907667e63b330e9d742004) | `c9e86a3b01199e78b4907667e63b330e9d742004` | Apache-2.0 | create-motion-videos |

## Verification scope

Regression tests execute the local helpers on synthetic inputs, including all 237 sound presets, all 48 theme exports, UI-data contracts, game project tooling, raster decks, and FFmpeg GIF encoding. Existing motion checks validate the augmented style manifest and independent installation. CI also exercises browser capture, output decoding, and existing office/media tooling.

These checks establish script contracts and packaging, not artistic quality or universal game-engine compatibility. The guides were reviewed in Codex; no independent agent production benchmark, human sound listening, real engine game build, paid API call, or hosted deployment is claimed. See the PR verification record and [tests/README.md](tests/README.md) for commands and actual outcomes.
