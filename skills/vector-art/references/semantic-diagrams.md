# Semantic diagrams as editable SVG

Adapted from Cathryn Lavery's diagram-design under [LICENSE-diagram.txt](../LICENSE-diagram.txt); see [SOURCES.md](../SOURCES.md). No upstream icons, product marks, or font outlines are bundled.

Choose the diagram by the relationship the reader needs to understand: flow for decisions, sequence for time-ordered interactions, containment for ownership, deployment for runtime placement, ER for data relationships, state for transitions, and timeline for dated events. Do not use a tree merely because boxes are easy to draw.

Write the entities and relationships before geometry. Label arrow direction and meaning consistently; a line must not ambiguously mean data flow, ownership, and chronology. Preserve sequence order, cardinality, units, and legends from the source. Distinguish an observed architecture from a proposed one and mark changed/unchanged elements in a before/after view.

Choose an overview-sized complexity budget. If labels, crossings, or nesting make the result unreadable, split overview and detail with explicit cross-references rather than shrinking text. Use a consistent structural grid, edge ports, spacing, text hierarchy, and alignment. Data-driven coordinates and crisp stroke offsets need not obey a decorative grid.

Route connectors around labels and nodes; render before deciding they are clear. Use text/shape differences as well as color. Keep a useful static state and reduced-motion behavior for animated process diagrams. Give SVG a viewBox, title/description, semantic groups, and selectable text where practical.

Deliver plain SVG when that is sufficient, or a self-contained HTML file with inline SVG for requested interaction. Keep brand tokens local, preserve source notices, and test with network disabled for offline delivery. Imported Mermaid/draw.io/Excalidraw content must preserve graph semantics, not only a visual approximation. Verify each required node and relationship against the supplied model and inspect the actual export.
