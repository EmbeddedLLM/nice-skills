# Continuous UI Morph — twoclipping-inspired family

## Contents

- [Choose this family](#choose-this-family)
- [Starting defaults](#starting-defaults)
- [Visual grammar](#visual-grammar)
- [Build a deterministic composition](#build-a-deterministic-composition)
- [Assets, audio, and service policy](#assets-audio-and-service-policy)
- [Rendering](#rendering)
- [Review the risks that matter](#review-the-risks-that-matter)
- [Sources and scope of adaptation](#sources-and-scope-of-adaptation)

**Family ID:** `continuous-ui-morph`

**Variants:** `ui-morph`, `product-launch`

**Intent:** short product films in which a recognisable interface element carries the viewer from one useful state to the next. Movement explains an action or a benefit; a decorative transition is secondary.

This is original reusable guidance informed by public demonstrations and technical descriptions from zero / [@twoclipping](https://x.com/twoclipping). It is an independent adaptation, not the creator's prompt, source implementation, or endorsement. It adds defaults and engineering guidance for this skill. The source posts attribute their examples to Opus 5.5; this guide does not guarantee the same result from any model.

## Choose this family

Use it for a concise SaaS teaser, a feature sequence, a compact interaction demo, or a product launch where UI and imagery connect into a continuous visual argument.

- Choose **ui-morph** when the identity of one changing component is the main attraction. A capsule can become a search field, a result panel, a useful control, and a completion state. Choose states that make sense for the actual product; do not reproduce the source demo's sequence by default.
- Choose **product-launch** when the film must connect a promise, two or three useful product moments, and an outcome. Photos, product images, or short user-provided footage may participate in the transformations. Keep the composition mainly two dimensional.
- Prefer Lemo **Swiss Motion** for strict typographic grids and non-spring motion; **Dark Tech Keynote** for a dark staged software reveal; **Living Screencast** for a faithful walkthrough with a mascot; **Whiteboard** for an explanation that needs diagrams and time to learn.

## Starting defaults

Use the user's requirements whenever supplied. Otherwise begin with these defaults and continue without a separate approval gate:

| Decision           | ui-morph                                              | product-launch                                                 |
| ------------------ | ----------------------------------------------------- | -------------------------------------------------------------- |
| Length             | 12–18 seconds                                         | 20–35 seconds                                                  |
| Shape of the story | 5–7 meaningful states, seamless loop when useful      | Promise → action → result → closing identity                   |
| Canvas             | 1440×1440 square                                      | 1920×1080 landscape; square for a social post                  |
| Finish             | 60 fps; preview can be smaller and 30 fps             | 60 fps; preview can be smaller and 30 fps                      |
| Palette            | Warm light neutral, dark text, one accent             | The same base, with colors from supplied imagery               |
| Sound              | Original local pulse and restrained clicks, or silent | Original local score; narration only if it helps the message   |
| Voice              | None                                                  | None until the brief benefits from speech                      |
| Assets             | Code-drawn components and local fonts                 | User assets first; code-drawn substitute if none are available |

A tempo near 120 BPM is a useful starting point, not a requirement. Align important arrivals with the selected track or the locally composed score. Reading and comprehension take priority over an arbitrary beat count. Leave a short explanation on screen long enough to be understood; extend the film or simplify the sentence before accelerating every transition.

## Visual grammar

1. **Preserve identity across transitions.** Keep a shared outline, anchor, color, or image so the viewer can follow the same object. Change only the properties needed for the new state. A component should become something useful, not merely stretch and reveal unrelated content.
2. **Keep one focus.** A large component, a clear cursor action, and generous surrounding space usually suffice. Supporting labels enter after the main shape has become readable.
3. **Use typography consistently.** Use a locally available or openly licensed sans family, with a small set of weights and sizes. Measure the final font before planning masks and alignment. Real product labels and supplied facts take precedence over decorative filler.
4. **Make the cursor causal.** Show its approach, contact, drag or release, and the corresponding result. Calculate it from the same timeline as the UI. It must not click an absent element, move through an unrelated scene, or jump when the camera changes.
5. **Use a controlled camera.** Reframe only to expose a new action or detail. Keep a single coordinate transform for the scene and cursor. Avoid simultaneous zoom, rotation, and text change that make the viewer search for the subject.
6. **Use small material cues.** Thin borders, restrained shadows, and limited translucency can separate surfaces. Liquid-glass distortion is optional and should never obscure the useful image or text. A light product film does not need a physical 3D glass object.
7. **Let the transition carry meaning.** A result expands into its detail; a selected image becomes the product preview; a completed control becomes the receipt or outcome. Reserve shape floods and irises for an intentional bridge, not every scene.

For **ui-morph**, continuity and a clean return matter more than a collection of effects. For **product-launch**, retain continuity within each feature beat, while allowing a new composition when the meaning changes. Do not force the entire product story through a tiny button if it damages clarity.

## Build a deterministic composition

Prefer HTML/CSS for UI layout and type, SVG for icons and masks, and small Canvas helpers only where useful. Build one page backed by a declarative timeline. Separate the content, layout, timing, and rendering functions so a wording change does not require rebuilding the film.

Expose `window.DUR`, `window.READY`, and `window.seek(t)`. `seek(t)` must produce the complete state for that timestamp, including camera, cursor, text, masks, media positions, and optional overlays. It may return a Promise while an image or video frame becomes ready. For the Lemo capture interface, expose `window.render = t => window.seek(t)` and keep the Promise intact. The integrated renderer must await it before taking a screenshot.

During capture, do not depend on a live animation clock, `setTimeout`, an incrementing frame counter, an unseeded random generator, or a CSS transition that remembers the previous style. Reassign the complete state, including elements that should be hidden. CSS can describe the appearance; JavaScript computes the appearance at time `t`. This is a timestamp-controlled composition, not a claim of CSS-only animation.

Wait for fonts and required assets before setting `READY`. After a requested DOM layout change, finish any necessary measurements before capture. Keep measurements in the same coordinate system as the camera. A random-access call at 8 seconds should give the same result whether the previous call was at 0, 3, or 12 seconds.

### Springs without simulation drift

Use an analytical spring response when a component needs a small settle. A critically damped response is suitable for text containers and controls that should not overshoot. An underdamped response with damping ratio roughly 0.82–0.95 can give larger shapes a restrained overshoot. Start with natural frequency around 18–24 radians per second and adjust by watching the actual move, not by treating those values as mandatory.

For a unit step, let the response be zero before its start. With critical damping, use `S(u) = 1 - (1 + ωu) exp(-ωu)` for `u >= 0`. A property with successive target changes can be evaluated as its initial value plus the sum of each target delta multiplied by `S(t - eventTime)`. The equivalent closed-form underdamped solution is also acceptable. Do not integrate spring velocity frame by frame during export.

Different edges can use slightly different responses to suggest stretch, but preserve valid geometry: positive width and height, bounded corner radii, and content that stays inside its mask. During a drag, derive position from the planned cursor path; after release, derive the return from the release pose and time. Do not abruptly switch to a spring that assumes another starting position.

## Assets, audio, and service policy

The default production path uses **no paid external service**. It still consumes the user's model access, local compute, and storage. It may require installation or download of free tools and local model assets. Do not describe that as a guarantee of a zero-cost model run.

- Use supplied imagery or draw original interface assets locally. If the brief needs photography, use user-provided material or a source whose relevant reuse terms have been checked. Record the origin and license of each external asset. Do not silently substitute a paid stock or generation service.
- Do not invent customer counts, test results, prices, endorsements, or product capabilities. If a claim is unavailable, express a feature qualitatively or use the user's provided facts.
- Default to locally synthesized music and modest procedural interaction sounds. User-supplied music is appropriate when its use is authorized. Free downloadable music is optional, not a dependency of the style.
- Set audio events from the same timeline as the visuals. Align the audible onset with the event rather than assuming the file begins at its loudest point. Keep repeated clicks quiet enough to support the sequence.
- Use narration only when it carries information that the interface cannot convey efficiently. Prefer a user recording or available local TTS. Fit the picture around the measured speech and provide captions. An online free TTS endpoint is still an external service; do not introduce one automatically when a local-only workflow is requested.
- Keep music below speech and check the final mix for clipped peaks and intelligibility. Approximately −14 LUFS is a reasonable delivery starting point, not a substitute for listening.

## Rendering

Capture exact timestamps with a local Chromium automation tool and encode with FFmpeg. For a video of duration `T` at `F` frames per second, render the agreed integer frame count on `t = frameIndex / F`; make the final duration explicit. For a loop, make the pose at `T` meet the pose at 0, and encode the interval before `T` so the boundary frame is not duplicated.

For fast camera moves or large shape travel, use optional temporal supersampling: evaluate several times inside each output frame's shutter interval and blend those samples into that one frame. Four samples are a practical final-quality starting point. Reduce or disable blur when it harms text. Keep the audio timeline unchanged.

The standard Lemo video renderer captures one state per output frame. Requesting 60 fps alone does not add temporal supersampling. Use a renderer that explicitly supports grouped subframe accumulation, add an isolated local capture adapter if needed, or deliver a clean unblurred render and state that choice. Do not label a sliding average of unrelated final frames as equivalent sampling.

If the launch uses video footage, choose a deterministic preparation route: pre-extract frames to numbered images, or use seekable media that is paused and awaited at each required time. For the latter, use independently decodable frames where practical and ensure the serving method supports the needed reads. For image sequences, await decoding before capture. Avoid stale decoded frames masquerading as successful seeks.

Keep sources, media manifests, the timing data, capture settings, and the final MP4 together. Provide enough information to change a headline, replace an asset, or rerender at the requested dimensions. A preview page is not the completed MP4 export.

## Review the risks that matter

Before the long render, inspect a few representative style frames and the beginnings, middles, and ends of the most difficult transitions. Then check the finished film at playback speed with sound. Do not replace this review with a large suite of tests that merely echoes the implementation.

| Failure | What to check or change |
| --- | --- |
| A component jumps when sampled out of order | Find hidden state, a free-running CSS animation, an incremental spring, or unseeded randomness; evaluate the same timestamp before and after a distant timestamp. |
| Old and new labels overlap inside a morph | Give each label its own visibility interval and mask; change the text after its container can hold it. |
| A pill folds or becomes negative during stretch | Check both edges and radius constraints; reduce overshoot or separate visual stretch from the hit area. |
| Cursor and component disagree | Use one coordinate conversion; measure anchors after layout; include cursor state in `seek(t)`. |
| Zoomed text looks soft | Check font readiness, transform hierarchy, compositor layers, capture scale, and motion blur; remove unnecessary `will-change` hints. |
| Glass looks dirty or distorts the wrong scene | Reduce the effect, test the specific browser's SVG filter behavior, and use a controlled copy of the background if a backdrop filter is unreliable. |
| A full-frame mask leaves corners uncovered | Test the mask at the actual aspect ratio and camera scale; size its coverage geometrically. |
| A footage frame repeats unexpectedly | Await the seek or image decode and verify the selected source frame. |
| An effect suddenly appears for one frame | Inspect the transition boundary on both sides; check visibility inheritance and every property that was not reset. |
| A loop hesitates at its seam | Compare the boundary pose, cursor, camera, audio phase, and motion direction; remove an accidental duplicated endpoint. |
| The film is stylish but hard to understand | Remove a state, lengthen the reading interval, or replace a transition with a stable view of the result. |

Final checks: correct dimensions and duration; expected frame rate; no clipped labels; no missing media; understandable product sequence; clean beginning and end; final audio present when requested. Report only checks actually performed.

## Sources and scope of adaptation

Public demonstrations and shared technical descriptions consulted:

- [UI morph loop, September 24, 2026](https://x.com/twoclipping/status/2103273003555402193): persistent component transformations, timestamp-based styles, analytical springs, and sampled export.
- [Product launch film, September 26, 2026](https://x.com/twoclipping/status/2103835273813496100): image-led launch sequence, asynchronous seeking, glass effects, and rendering checks.
- [Earlier product-film example, September 23, 2026](https://x.com/twoclipping/status/2102554209166000267): real footage and audio integrated with code-driven motion.

The examples inspired this family's visual and timing principles. The scene plans, defaults, local-audio policy, integration contract, and review guidance above are this skill's adaptation. The original posts' promotional cost claims are not reproduced as a promise. The creator's branding and exact example sequences are not bundled.
