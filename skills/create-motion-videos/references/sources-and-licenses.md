# Sources, attribution, and scope

See the root [SOURCES.md](../SOURCES.md) for the complete source map, original post publication dates, and **2026-10-20** reference retrieval dates.

## Pinned Lemo collection

- Repository: https://github.com/lemomo-ai/lemo-opuscar
- Creator: LemoLab / Lemomo, https://x.com/lemomo_ai
- Snapshot: `b5e8ef93930b6d828f352055a689320f138237b1`, retrieved 20 October 2026.
- Main collection: all 51 real `styles/<slug>/STYLE.md` entries; `_template` is not a style.
- Additional collection: all 98 bilingual reusable prompts in `styleboard/opuscar98_styles.json`. These are film-specific references, not 98 additional full production engines.
- Included material: the published style guides, style metadata, demo explanations and code, shared rendering/audio utilities, package manifests, and textual/vector/data resources. See `upstream-manifest.json` for every included path and SHA-256.
- Omitted material: reference images and audiovisual files listed in the manifest. Generated voices and other optional demo assets can be absent upstream. Required production font URLs have been patched to the bundled originals; see font-replacements.md. A demonstration's source is a technique reference; it is not a promise that its complete media bundle is included.

Files under `assets/lemo/` retain upstream structure; documented font-path/build patches and added OFL font files are identified in the manifest. Style engines remain unchanged. The surrounding skill, catalogue, setup helper, strict browser renderer, and twoclipping family are additions. Do not silently update or rewrite the pinned snapshot during a film task. Use a separate runtime and project directory.

## Licenses

Lemo's [LICENSE](../assets/lemo/LICENSE) grants MIT terms to code and documentation. Preserve that notice when distributing copied or adapted source. Its README separately identifies demo films and stills as CC BY 4.0; retain creator attribution, source link, and change notices if using those demo media. New original films do not require a LemoLab watermark or end card.

Third-party fonts, samples, scientific data, models, scans and imagery keep their own terms. Check the selected demo's `CREDITS` and the actual asset source. Do not label every item in this bundle MIT. Store the credits for assets actually used in the film's `CREDITS` and asset manifest. Treat specimen data as real data only when its provenance supports that claim.

The 98 OPUSCAR references supply visual and camera language. Use them to create the user's own subject and scene plan. Do not carry over a demo's characters, logos, exact shots or music merely because they appear in a reference entry. Film titles identify sources; they do not grant rights to other media from those films.

## Twoclipping addition

Original public sources:

- UI morph: https://x.com/twoclipping/status/2103273003555402193
- Product launch: https://x.com/twoclipping/status/2103835273813496100
- Earlier code-and-footage example: https://x.com/twoclipping/status/2102554209166000267

`twoclipping.md` is independently written guidance about the demonstrated method and aesthetic. It is not a copy of the creator's full prompt, a source-code release, or an endorsed package. The starter and renderer are new implementations. No original video, creator logo, private asset, or purported free license to the social posts is bundled.

Lemo's nearest families are Dark Tech Keynote, Living Screencast, Swiss Motion, Glass Product Render and Pictogram Motion. Their invariants do not provide the same continuous UI transformation family with restrained springs. The overlap rationale is recorded in `twoclipping-overlap.md`.

## Optional Openverse assets

Use [Openverse](https://api.openverse.org/v1/) for existing photos, illustrations, textures, music, ambience, and sound effects when the treatment needs them. Anonymous search needs network access and an HTTP-capable tool, but no paid provider, SDK, or account. It does not supply generated video or narration. Respect local-only requests; use supplied assets or procedural material when discovery is unavailable. Send generic subject queries rather than private project details.

For example, use an available HTTP tool or `curl` to search for forest imagery:

```sh
curl --fail --silent --show-error --max-time 20 --get \
  'https://api.openverse.org/v1/images/' \
  --data-urlencode 'q=forest' \
  --data-urlencode 'license=cc0,pdm,by' \
  --data-urlencode 'page_size=5' \
  --data-urlencode 'mature=false'
```

For bird ambience, use `/v1/audio/` with `q=birds` and the same filters. Keep ordinary searches; collection mode does not support license filters. Check response warnings and each candidate's license. Query examples describe the API contract, not guaranteed availability or cleared media.

Before using a candidate:

1. Open its `foreign_landing_url` and verify the license, creator, and any additional notices. [Openverse does not guarantee license accuracy](https://docs.openverse.org/api/reference/made_with_ov.html). Skip uncertain or inaccessible sources. The default CC0/public-domain/CC BY selection avoids NC, ND, and SA restrictions; widening it requires checking the actual intended use. In particular, music synchronized to moving images is an adaptation under the [CC FAQ](https://creativecommons.org/faq/index.html#when-is-my-use-considered-an-adaptation), so ND music is unsuitable for this normal workflow.
2. Download only selected media into the writable film project, subject to the source host's terms. Check the actual file format, image dimensions, or decoded audio duration/quality. A thumbnail is for selection, not proof of production resolution. Do not substitute stock imagery for measured evidence or a required product asset.
3. Record the Openverse ID, source page, media URL, title, creator, license/version/link, retrieval date, local path, checksum, and changes in the asset manifest. Preserve applicable notices and put required credits in distributed `CREDITS` and an appropriate film/description credit surface. Under [CC BY](https://creativecommons.org/licenses/by/4.0/), retain attribution, link the license, and identify modifications; the license may not cover all other rights.
4. Resolve assets locally and finish decoding before timeline capture. Keep API calls, downloads, and remote hotlinks outside `render(t)` and the final render path. Trim/mix the local soundtrack using the film's cue map, then validate the final duration and sound.

Respect response limits and retry guidance on HTTP 429; do not scrape the catalog or bypass restrictions. On HTTP 403, timeouts, inaccessible media, or exhausted retries, report the gap and use a suitable supplied/procedural alternative within the brief. Do not silently register an account or substitute a paid provider. Follow the [Openverse terms](https://docs.openverse.org/terms_of_service.html) and recheck current API documentation if request behavior changes.

## Cost and verification language

Default to local frame rendering, supplied or openly licensed assets, locally synthesized audio and optional offline TTS. Downloads and software dependencies can still be necessary. Model access, hardware and time are separate costs. Never promise $0 model usage, a one-prompt result, identical performance on another model, or that every style runs without downloads.

Report only executed checks. Distinguish a source audit, a rendered test clip, a preview-frame inspection and a complete audiovisual review. Do not describe all styles as reproduced because one shared renderer passed a smoke test.
