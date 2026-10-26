# Material, purpose, and targeted design review

Adapted from the pinned Hallmark, Impeccable, and Elaya sources in [SOURCES.md](../SOURCES.md). Keep the user's design system and requested scope authoritative.

## Let the content determine the page

Inventory real product captures, photographs, facts, quotes, and licensed assets; identify missing evidence explicitly. Do not invent social proof, customer counts, metrics, or working form submissions. A placeholder should be visibly illustrative and replaceable, not a fabricated claim.

Name what the visitor needs to do: book, buy, compare, learn, attend, subscribe, or operate a tool. Put the relevant action and decision information where that task needs them. A menu, booking availability, changelog, product comparison, or working interaction can be the page's main content; do not default every brief to a hero, three cards, testimonials, and signup band.

Choose material separately from composition. Typography, palette, surfaces, and texture can be consistent while section layouts vary with their content. Use one subject-specific focal element that shows the actual product or offer. Existing brand tokens beat a catalog suggestion. Theme recipes are options, not permission to replace a project's identity.

## Choose the review mode

- **Audit:** inspect and report concrete issues without changing the page.
- **Critique:** assess hierarchy, subject fit, composition, and the primary task; explain the impact and proposed direction.
- **Polish:** correct spacing, type, alignment, state transitions, and responsive details within the chosen design.
- **Distill:** remove redundant content or visual machinery while preserving necessary information and functionality.
- **Harden:** exercise long/translated content, missing assets, loading, empty, error, keyboard, touch, reduced motion, and real backend failures.
- **Redesign:** change the visual system only when requested; preserve content, routes, form destinations, analytics, accessibility semantics, and other wiring unless the scope explicitly changes them.

Separate blocking functional/accessibility defects from stylistic preferences and optional finish work. Do not enforce arbitrary font bans, section counts, or visual lint scores as universal requirements. A style exception needs a design reason, not a weakened accessibility requirement.

## Components and motion

Reuse project components first. A public component catalog such as Galaxy is a source of candidates, not an instruction to import thousands of widgets or trust their accessibility. For a chosen snippet, inspect its actual source and license, preserve notices, replace global styles with scoped tokens, and test semantic controls, keyboard/focus, contrast, touch, and reduced motion. No component or catalog artwork is bundled here.

For scroll scenes, keep essential content visible by default, trigger finite intros with viewport observation, and pause optional continuous work while offscreen. Reduced motion should show a useful final composition without requiring animation. Keep input response immediate; do not animate every interaction through a slow showcase curve.

For design-to-motion, first reproduce the still in the destination renderer. Separate moving layers only when the source allows it, keep z-order and clipping, and distinguish layout bounds from rendered bounds including strokes/shadows. Normalize layer positions to the reference origin. A flattened screenshot cannot provide unseen layers. Show an unavailable layer as a limitation rather than inventing perfect fidelity.

On a website, animate only the parts that help the user understand the interface. On a requested showcase, plan a readable sequence and loop seam. Export only requested formats. Check both the final static design and the intermediate motion at the delivered size.
