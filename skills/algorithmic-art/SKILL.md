---
name: algorithmic-art
description: Create seeded procedural artwork and interactive exploration in browser Canvas or SVG. Use for flow fields, particle systems, generative patterns, and reproducible visual variants rather than static graphic layout or encoded video.
license: Apache-2.0; see LICENSE.txt and SOURCES.md
---

# Algorithmic art

Translate the brief into a computational idea such as growth, interference, repetition, or constrained motion. Deliver working source and the requested interactive page or image. Native Canvas/SVG needs only a browser; no paid generation service is required.

## Build a reproducible composition

1. Choose the algorithm, canvas, palette, and meaningful parameters from the subject. Keep iteration counts bounded and begin with a still or small simulation.
2. Record the seed, parameters, dimensions, and renderer/library versions. Route all randomness through the seeded generator and reset buffers, particles, and generators before regeneration.
3. For reproducible motion, compute state from explicit frame indices or fixed simulation steps. Do not integrate from wall-clock time. If using p5.js, seed both random and noise functions and pin/bundle that optional dependency for offline use.
4. Expose only controls that change the artwork meaningfully, with labels, useful bounds, a visible seed, reset/regenerate, and export. Keep controls keyboard accessible and provide pause/static behavior for reduced-motion users.

For a dependency-free starting point, copy both [viewer.html](assets/viewer.html) and [generator_template.js](assets/generator_template.js) to a writable project directory. Open the HTML in a browser and replace `drawArt` with the requested algorithm. Both files are needed unless the script is inlined; do not edit the installed skill.

## Verify and deliver

Regenerate the same seed twice in the same renderer and compare results. Confirm a changed seed affects the intended structure. Exercise parameter limits, reset, resize, and export; exports must match the art and exclude controls. Inspect dense areas for clipping and noise. Determinism does not imply pixel-identical results across browsers or fonts.

Example: “Make a seeded flow-field print with density and curvature controls.” Deliver the page, selected PNG, seed, and parameter values. If high density stalls the browser, bound the control and explain the practical limit instead of shipping an unresponsive viewer.
