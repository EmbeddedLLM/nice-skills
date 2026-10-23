# Apply and validate

## Website

Exported CSS scopes tokens to `[data-palette="SLUG"]`. Put the exact slug on the root element. Use the generated `.theme-primary` class, or wire equivalent component rules:

```css
body {
  background: var(--mca-background);
  color: var(--mca-text);
}
.primary-button {
  background: var(--mca-action, var(--mca-primary));
  color: var(--mca-on-action, var(--mca-on-primary));
  border: 1px solid var(--mca-border-interactive);
}
.primary-button:hover {
  background: var(--mca-action-hover, var(--mca-primary-hover));
  color: var(--mca-on-action-hover, var(--mca-on-primary-hover));
}
.primary-button:focus-visible {
  outline: 3px solid var(--mca-focus-ring);
  outline-offset: 3px;
}
```

Use link tokens on their intended canvases. Keep link underlines and non-colour selected-state cues. Decorative borders are not control boundaries. Check disabled, validation, error and other task-specific states separately: they are not supplied as a complete design system.

## PowerPoint

The XML is an Office colour scheme (`a:clrScheme`), not a complete `.thmx` or `.pptx`. It has no fonts, effects or slide layouts. Use the twelve values in PowerPoint's custom colours workflow, or use a presentation editing tool to set the real theme colour slots. Set the actual slide canvas and text according to the record. Dark schemes need a dark canvas; importing colours alone does not make the master dark.

Accents 1–3 match the applied primary/secondary/accent. Accents 4–6 are related shades in the refreshed collection. Lavender repeats its exact supplied colours to fill twelve slots. `label_colors` gives guidance for text placed on accent fills; the XML itself does not enforce these pairings. Closely related series require direct labels or other distinctions.

## Custom records and refreshes

Work on a copy unless the user requests an installed-skill update. Retain `source_colors`, source URL, observed date and displayed likes as evidence. Recompute core roles, all related web states, Office slots, label colours and XML together. Update explanatory notes when changing the derivation method. Use explicit identifiers for new records; do not overwrite a different named source's identity.

For custom palettes without published references, label them as user-supplied or newly designed. Do not fabricate likes, licences or provenance. For a refreshed guide, keep ten moods with five choices each plus Lavender unless the user asks for a different structure.

## Validation limits

`verify` checks schema essentials, 50+1 coverage, HEX values, twelve-slot XML agreement, key normal-text pairings, button normal/hover labels, selected text, input boundaries, focus contrast against the two base canvases, and Lavender's nine exact colours. It does not prove chart distinguishability, focus appearance in every implementation, colour-vision accessibility, performance, layout quality or native PowerPoint compatibility. Inspect the real artifact after application. Opacity, images, gradients and different adjacent surfaces require fresh checks.
