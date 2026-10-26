---
name: explainer-video
description: Create or revise narration-led educational videos from a topic, source material, or supplied recording, with researched claims, timed diagrams or scene images, captions, and editable source. Use when the explanation and locked narration drive the visuals. Includes a local still-scene renderer; paid speech services are optional and require explicit selection.
license: MIT
compatibility: Python 3.10+, FFmpeg with libx264 and AAC, ffprobe; Bash and jq for delivery finalization. No credentials or network access are required for supplied-audio production.
---

# Explainer video

Deliver a clear explanation whose visuals follow the accepted narration. Keep this skill directory read-only; write the story and all outputs in the user's project. Use its directory as `SKILL_DIR` when running bundled commands. This package works on its own and does not require another skill or a video service.

1. Establish audience, learning objective, source material, language, length, aspect ratio, and sound needs. Ask only about missing choices that materially affect the result; reuse answers already provided. Verify factual claims against attributable sources and retain a claim-to-source record. Label illustrative data and unresolved uncertainty.
2. Write a story spine before visual design. Read [narrative and visual choices](references/story-design.md). Explain a mechanism through visible changes, evidence, or comparisons. Avoid a succession of captions that merely repeat the narration.
3. Lock narration before scene boundaries and captions. Default to a supplied recording or speech from an already available local tool. Request the recording or report a missing local speech capability when neither is available. Never substitute a paid provider silently. Supplied final audio does not imply permission to clone its speaker's voice.
4. Follow [local production](references/local-production.md) to build `story.json`, caption drafts, and timed scene images. Its helper estimates word timing from pauses; listen, align, and correct captions before delivery. A measured recording duration does not make its estimated word timing accurate. Preserve accepted audio and timing when only restyling the visuals.
5. Author readable diagrams, evidence cards, or images appropriate to each scene, then render with the local helper. It produces a still-scene explainer, not continuous animation. Use an independently installed local editor or animation backend when the explanation needs motion; preserve the accepted narrative and timing contract. Do not install a new renderer merely to reproduce a static explanation.
6. Review representative frames, visual transitions, facts, captions, and a preview. Finalize the local render with the bundled delivery helper, then inspect the encoded contact sheet and listen to the final speech. Automated decode and loudness checks establish technical properties, not factual correctness, pacing, or visual quality. Silence used in a draft is never finished narration.
7. Deliver the final video, applicable captions, editable scene assets and timing, narration, source/asset credits, reproducible commands, and a QA note describing actual checks and remaining limits. Publishing is a separate action.

The optional MiniMax route requires `--tts-provider minimax` and existing authorization for text transfer, voice choice, and bounded production cost. An API key alone is not authorization. See [paid speech and provenance](references/sources.md). No live provider call is needed for the complete local route.
