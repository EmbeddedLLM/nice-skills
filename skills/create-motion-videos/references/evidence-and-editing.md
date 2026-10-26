# Evidence-led films and music-led editing

Adapted from Lemo's updated documentary styles and Shotcraft's production guidance; see [SOURCES.md](../SOURCES.md). These workflows use this package's existing local renderer, supplied/verified assets, and original story treatment.

## Choose the documentary grammar

| Style                | Useful distinction                                                                            |
| -------------------- | --------------------------------------------------------------------------------------------- |
| Caption News         | Sound-off comprehension, caption chunks, on-screen source tags                                |
| City Symphony        | Place and daily rhythms carried by footage and sound rather than an anchor                    |
| Countdown            | Chronology and a meaningful time constraint, not arbitrary number decoration                  |
| Kino Montage         | Meaning from shot juxtaposition and rhythmic visual relationships                             |
| News Package         | Clear report structure, source identity, contextual graphics, understandable spoken narrative |
| Newsreel             | Archival report grammar with historical context and honest dates                              |
| Telestrator          | Annotations tied to the actual image geometry and time                                        |
| Visual Investigation | Explicit claim/evidence relationships and distinguishable uncertainty                         |

Load the selected guide through `scripts/styles.py show lemo:<slug>`. These eight additions contain STYLE.md and metadata only. The 51 earlier demo packages and their patched runtime remain intact. Use `prepare_project.py` to make a new browser-starter project; it does not promise a ready-made documentary film or acquire missing footage.

## Keep evidence attached to the edit

Create a source ledger for each factual claim and media item: exact origin, date/page/time span, supported claim, license/permission, creator/credit, and transformations. Mark reconstructed, illustrative, archival, or synthetic material visibly when viewers could mistake it for recorded evidence. A source link is not permission to redistribute its media; a licensed photograph is not proof of an unrelated claim.

Let the viewer inspect the relevant document, scene, or comparison before drawing the conclusion. Keep units, dates, geography, denominator, and uncertainty consistent across narration, captions, charts, and source tags. Avoid implying causation through montage when the evidence supports only sequence or correlation. Use readable source labels and deliver the full ledger/credits alongside the film.

For captions-first work, watch muted at delivery size. Each beat must remain understandable and text must stay on screen long enough to read. For tracked annotations, verify the anchor through the whole shot, not only one frame; a planar homography does not describe objects at different depths.

## Plan the cut around actual material

For a product film, capture the real product and preserve the task's action/result sequence. Do not substitute invented UI for available working behavior. Inventory the captured states, then give each shot a purpose, focal element, entry/exit, duration, and continuity relationship. A shot recipe supplies a technique; it does not authorize reproducing another creator's branded sequence or imagery.

Use an energy arc with contrast: setup, development, a clear reveal, and enough rest for the final message. Continuous maximal motion erases emphasis. Prove the most difficult shot with representative assets before filling the timeline.

When music is supplied and drives the film, fit beat interval and phase to the detected onset sequence rather than trusting a single tempo scalar. Check residuals across the track and half/double-tempo ambiguity; variable-tempo sections need separate grids. Keep times in floating-point seconds and round once at the frame/sample boundary. If narration leads, preserve its meaning and breathing room instead of forcing every line onto a beat.

Align effects by their meaningful attack or peak, allow pre-roll and full tails, and check music/speech masking. Verify sync and text readability on decoded final frames and audio after muxing. A timeline assertion cannot establish the encoded film's synchronization or subjective quality.

## Preserve the local production path

No Remotion, HyperFrames, paid video model, hosted editor, or posting service is required. Existing HTML/Canvas/Three.js time-driven rendering already provides the production mechanism. Optional external engines remain project choices with their own licenses, pins, and dependencies. Do not replace a working renderer solely because a source uses a different one.

## Compose and review at delivery scale

Adapted from the licensed Snapcn and HyperFrames workflow guides recorded in SOURCES.md. Choose a ready layout, composition of existing parts, or a new component according to the actual content. Each beat needs a role in the story and enough time for its component to enter, communicate, and leave. A component's natural animation duration is part of the shot budget; arbitrary sequence lengths can clip its payoff. Distinguish time-scaled animation from state keyed to the timeline when reusing UI primitives.

Review representative frames near each scene's start and middle, on either side of cuts, and at the intended small-screen delivery size. Inspect motion between stills around the hero move. Check reading time in the rendered file: a readable contact sheet does not establish that a sentence stays visible long enough. Let intentional stillness remain when it serves the message.

Record each issue as time, location, observed problem, concrete edit, and behavior to preserve. Fix broken comprehension, factual errors, clipping, and unreadable text first; then weak timing and polish. Recheck the changed spans and the final encode. Report separately what was measured, visually inspected, heard, and left unverified. Do not turn a numeric quality score into a substitute for actionable findings.
