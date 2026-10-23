# Style prompt libraries

Two attributed prompt libraries ship with this skill in `assets/prompt-library/`. They are reference material for art direction: read a prompt for the techniques it names, then build the user's film with this skill's own workflow. Do not paste a whole library prompt as the brief, and do not copy a reference film's story, characters or brand.

```sh
python3 "$SKILL_DIR/scripts/prompt_library.py" libraries
python3 "$SKILL_DIR/scripts/prompt_library.py" list --query "isometric" --limit 5
python3 "$SKILL_DIR/scripts/prompt_library.py" list --technique shader --complete-only
python3 "$SKILL_DIR/scripts/prompt_library.py" show 09-bauhaus
```

Both libraries are bundled under `assets/prompt-library/`; the MG stills, review prompt, authoring template and two CC0 textures live in `assets/mg-styles15/`, and every file is pinned by hash in [vendored-assets.json](vendored-assets.json).

Standard library only, no network access. `list` filters on library, category, technique and free text over id, author, title and prompt; `show` prints one prompt in full.

## `opus55-videos` — 703 community briefs

Code-rendered videos people made in HTML, Canvas, SVG, WebGL/Three.js and CSS, each with the prompt its creator published and a link to the original post. Use them to see how a short brief is phrased for an agent, and to find the name of an effect you recognise but cannot describe.

- `category`: `motion`, `3d`, `explainer`, `interactive`.
- `techniques`: `canvas`, `svg`, `threejs`, `webgl`, `shader`, `gsap`, `css`, `audio`, `playable`, `particles`, `physics`, `pixel`, `ai-image`.
- `prompt_complete: false` means the creator published no full prompt and the record holds their original post. Treat those as descriptions of a result, not as instructions.

**Name the technique before you build it.** The most common way a style request goes wrong is that the user describes an effect by feel ("that building thing that snaps into place") and the agent guesses a different one. Search this library for the vocabulary — isometric, cel boil, collage, morph, HUD, paperclip, pixel, liquid — say the name back to the user in one line, and then build to that name. If no record matches, describe the motion in words (what moves, from where to where, on what curve, over how long) and confirm it.

## `mg-styles-15` — 15 motion-design style prompts

Fifteen canonical motion-design styles, each prompt written around one fixed output spec: a 10-second 1920×1080 film at 30 fps with stereo audio, mastered to −14 LUFS and a true peak of −1 dBTP, saved as `video.mp4`. Each carries five parts:

1. **Role and benchmark** — the model is the director, designer, engineer and sound designer; template-looking results fail; named studios set the bar.
2. **Style** — the Chinese and English name of the style.
3. **Output** — resolution, frame rate, exact duration, codec, audio and loudness.
4. **Suggested technical route** — the stack that suits the style (SVG + GSAP, Canvas, WebGL/Three.js, a raymarched shader), with the freedom to choose better and say why.
5. **Creative seed and signature features** — a second-by-second beat sheet with a palette and sound direction, then the visual traits and key techniques the result is judged against.

The styles are written in Chinese with English directives. Keep the structure and the signature features when adapting them; replace the seed story, brand name, copy and palette with the user's.

| id                | style                                                  |
| ----------------- | ------------------------------------------------------ |
| `01-flat-vector`  | Flat / vector 2D motion graphics (explainer tradition) |
| `02-line-art`     | Single-weight line art                                 |
| `03-isometric`    | Isometric worlds and diagrams                          |
| `04-3d-render`    | Rendered 3D product and abstract scenes                |
| `05-cel-boil`     | Cel animation with a boiling line                      |
| `06-collage`      | Cut-paper and print collage                            |
| `07-liquid`       | Liquid and fluid simulation aesthetics                 |
| `08-morph`        | Shape morphing between distinct forms                  |
| `09-bauhaus`      | Geometric Bauhaus composition                          |
| `10-synthwave`    | Synthwave grid and chrome                              |
| `12-aurora-glass` | Aurora gradients behind glass                          |
| `18-hanazi`       | Hand-drawn frame-by-frame character work               |
| `19-paperclip`    | Bold-outline sticker explainer                         |
| `20-pixel`        | Pixel art and 8-bit motion                             |
| `22-hud`          | Technical HUD and instrument overlays                  |

Each style id has a still from its film at `assets/mg-styles15/stills/<id>.webp`. Look at it before choosing: it shows the finish the prompt asks for far better than the prompt text does. The ids keep the upstream numbering, so they are not contiguous.

The films these prompts produced used a specific set of licensed fonts, which the upstream repository does not ship and neither does this skill. Without them the browser falls back to system faces and the lettering will not match the reference films. Choose faces you may actually use — the type systems in [style-index.md](style-index.md) and the bundled Lemo fonts are safe defaults — and say which ones you used in your report.

## Writing a new style prompt

A skeleton for the five parts is bundled at [`assets/mg-styles15/template.md`](../assets/mg-styles15/template.md). Use the same structure. What makes a style prompt work is that its constraints are **checkable**:

- Name the exact output contract, including duration and audio, so a reviewer can verify it.
- Write the creative seed as a beat sheet with times: hook, escalation, climax, end frame. A prompt without beats produces an even, flat loop.
- Express signature features as numbers a reviewer can measure: `cubic-bezier(0.34,1.56,0.64,1)` for overshoot, a 2–4 frame stagger, a 10% squash, one moving subject at a time. "Make it feel bouncy" is not a constraint.
- Use invented brand names and copy so the result cannot infringe a real mark.
- Name the stack that suits the style but allow a better one with a stated reason.

## The independent review loop

A style prompt is only half of the method: the films were improved by rendering, reviewing with a second agent that did not make the film, and revising. Run the same loop when the user wants a polished result.

A ready-made review prompt is bundled at [`assets/mg-styles15/rubric.md`](../assets/mg-styles15/rubric.md); use it verbatim or as the base for your own. In outline (give it the film and the prompt, not your intentions):

1. Look at the film properly: a contact sheet (a frame every 0.5 s), frame strips around the fastest and most important moves, and full-resolution frames at five to eight key times. Inspect edges, type setting, aliasing, banding, texture and clipping at full resolution.
2. Check the spec: exact duration, resolution and frame rate, audio present, loudness and true peak, no black frames except intended, no unintended static spans, visual hits aligned with audio onsets.
3. Score each dimension from 1 to 10 with these anchors — 5 competent student work, 6 decent template, 7 solid professional, 8 high-end agency, 9 award shortlist, 10 best in the world — and do not inflate: most first renders deserve 5–7. Dimensions: style fidelity, concept and hook, motion craft, design and typography, finish and texture, sound and sync, technical compliance.
4. Give five to ten fixes ordered by impact on the final impression. Each needs a timecode, an observable fault, why it matters, and a concrete technique with numbers. At least one fix must raise the wow factor rather than polish.
5. Flag as critical anything that reads as generic or template-like, unnatural copy in the target language, fallback fonts or tofu, and any spec failure.

**Revision:** paste the review back into the session that made the film. Fix the top findings, re-render, review again. Two rounds is usually enough; stop when the findings are polish.

## Attribution

Both libraries are MIT-licensed and carry their upstream repository, commit, retrieval date and the local transformation in the `source` block of each JSON file, with the full licence texts in [SOURCES.md](../SOURCES.md). Every `opus55-videos` record keeps its creator handle and original post link: if you show a prompt to a user, keep the attribution. The `mg-styles-15` prompts describe reference films that are not bundled.
