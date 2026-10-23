# Sources, changes, and optional paid speech

This is a selective adaptation of the user-designated [explainer archive](https://github.com/jiahuei/agent-skills/tree/235e920a4e494b74b46af67f813167699257c039/archive/explainer-video), reviewed on 2026-10-21. It keeps a standalone narration-first workflow without the archive's second browser rendering stack, unavailable kit references, CDN resources, or provider requirement.

The archive identifies [Lanshu at commit 762d3ee42623b75a4ec63ad6aa61ace69d78ce6e](https://github.com/cclank/lanshu-create-ai-presenter-video/tree/762d3ee42623b75a4ec63ad6aa61ace69d78ce6e) as the MIT source for its story, subtitle, and delivery tools. The original [Lanshu license](../LICENSE-lanshu.txt) is retained. `scripts/story.py`, `scripts/srt.py`, and `scripts/finalize_delivery.sh` were taken from the pinned archive snapshot. Changes here require explicit paid TTS selection, reject conflicting speech modes, adjust script paths and subtitle-directory loading to this package, preserve millisecond audio duration, keep estimated timing forward when no speech span is detected, preserve authoritative caption end times, preserve accepted audio on failed local replacement, write story metadata atomically, leave loudness normalization to delivery finalization, and clarify draft output. The finalizer additionally protects dangling symlinks and files created during encoding, stages on the destination filesystem, and publishes with exclusive file links and the report last. The entry point, reference guides, local still-scene renderer, and repository tests are this repository's adaptations/additions under the included [MIT license](../LICENSE.repository.txt).

No HyperFrames material, browser kit, font binary, generated voice, stock media, or model is bundled. The archive's HyperFrames Apache notice and its broad third-party manifest apply to omitted components and are not presented as covering these files. Runtime software, models, and production assets keep their own terms. User-supplied media and independently downloaded assets require their own credits and permissions.

## Optional MiniMax speech

The imported tool retains its original MiniMax `speech-2.8-hd` integration for users who explicitly choose it. Before using it, verify the provider's current official API, available model/voice, region, retention terms, and price. Do not assume the historical endpoint or model remains available. This optional integration has offline request-contract tests; no live paid service quality or availability is established by those tests.

Establish the authorized text transfer, stock voice or separately authorized cloning input, estimated cost, and budget first. Then supply credentials through the environment without printing or saving them in project files:

```sh
python3 "$SKILL_DIR/scripts/story.py" "$PROJECT/story" --tts-provider minimax
```

The tool reads `MINIMAX_API_KEY`; `MINIMAX_BASE_URL` optionally selects an authorized regional endpoint. Metadata can select `voice`, `speed`, and pronunciation entries. It sends one request per uncached narration line, stores returned audio/timestamps under `audio/tts/`, and reuses completed cache entries. It does not implement spending limits or submission reconciliation. If a request outcome is uncertain, stop and inspect the provider's records before retrying; a missing local cache does not prove that no charge occurred. Keep the authorized budget and number of lines small enough to review before execution.

Provider timestamps still require listening and caption review. An API key being present never changes the default local route. If a provider fails, keep accepted work and use supplied/local audio where appropriate; do not silently change provider, upload inputs elsewhere, or make another paid attempt.
