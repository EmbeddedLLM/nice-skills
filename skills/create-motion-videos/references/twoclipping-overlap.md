# Overlap decision: add one family, with two variants

**Recommendation:** add `continuous-ui-morph`, presented as a twoclipping-inspired independent adaptation. Use `ui-morph` and `product-launch` as variants of the same family. Do not add two separate generic product-video styles.

Checked the current Lemo README and the relevant `STYLE.md` files on October 20, 2026. The local upstream checkout is commit `b5e8ef93930b6d828f352055a689320f138237b1`. Its named library has 51 styles. The separate OPUSCAR 98 film-reference collection is a different catalogue; this memo evaluates the main reusable styles and the nearest production grammars.

## Closest existing styles

| Lemo style | Meaningful overlap | Reason the new family remains useful |
| --- | --- | --- |
| [Dark Tech Keynote](https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/dark-keynote/STYLE.md) | Product film, cursor, abstract UI, beat-aligned motion, expansion/collapse transitions, slight overshoot | Its authored identity is a dark lit stage with invented interface pieces and a Canvas engine. It does not center a persistent light UI component continuously becoming functional states, nor an optional photo/footage-led launch. This is the closest conceptual neighbor. |
| [Living Screencast](https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/living-screencast/STYLE.md) | HTML/CSS/SVG, cursor camera, continuous walkthrough, DOM measurement | Its defining pair is a faithful product UI plus a pixel mascot acting inside it. The new family needs neither a mascot nor a full walkthrough and permits the interface itself to change identity. This is the closest implementation neighbor. |
| [Swiss Motion](https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/swiss-motion/STYLE.md) | Sparse light palette, strong typography, beat grid, precise 2D layout | It explicitly excludes springs and overshoot, uses flat print-like forms, and organizes motion around a typographic grid. Spring-driven functional UI transformations and translucent/photo surfaces would weaken that style's rules. |
| [Glass Product](https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/glass-product/STYLE.md) | Premium launch feel, glass, highlights, music alignment | Its subject is a physical fictional glass object rendered with Three.js materials and studio lighting. Twoclipping-style liquid glass is a 2D UI effect over imagery, so treating these as the same style would select the wrong renderer and story. |
| [Pictogram Motion](https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/pictogram-motion/STYLE.md) | Compact graphic film, mask-revealed type, beat timing, temporal blur | Its chapter cards, patterns, and geometric figures form a catalogue. The new family preserves the identity of a component across useful states rather than presenting successive item cards. |
| [Whiteboard](https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/whiteboard/STYLE.md) | Continuous 2D space, visual explanation, deterministic frame capture | Stroke-by-stroke handwriting, physical board materials, and a traveling pen serve a lesson. It should remain the route for a diagram-led explanation, not absorb a short UI teaser. |

## Distinctive core to preserve

The new entry earns its place through **persistent object identity, cursor-caused functional changes, restrained analytical springs, and a light UI/product language**. A 60 fps capture path with optional grouped subframe blur supports that grammar, but frame rate alone does not define the style. Keep photography and footage optional in `product-launch`; their preparation is a workflow extension, not a requirement for `ui-morph`.

The variants share a declarative timeline and the same frame-at-time contract. In the local upstream renderer, `await page.evaluate(t => window.render(t), ...)` permits a returned Promise, so a `render(t)` adapter can preserve an asynchronous `seek(t)`. Upstream's ordinary capture loop performs one screenshot per output frame; temporal supersampling must be added explicitly or omitted honestly.

## Attribution and operating defaults

The new reference is original guidance, not a redistributed social prompt or recovered source project. It links the three original X posts and states that it is neither endorsed by the creator nor the implementation used in the examples. It defaults to local rendering, code-drawn or supplied assets, locally produced sound, and optional local/user voice. It distinguishes avoiding paid services from model and compute costs.

Read the completed [twoclipping family guide](twoclipping.md). The six upstream guides used for comparison are bundled under `assets/lemo/styles/`: `dark-keynote`, `living-screencast`, `swiss-motion`, `glass-product`, `pictogram-motion` and `whiteboard`. Their exact guide paths and source URLs appear in the [style index](style-index.md) and [catalogue](catalogue.json).
