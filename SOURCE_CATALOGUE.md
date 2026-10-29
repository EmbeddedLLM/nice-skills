# Externally sourced material catalogues

[The repository index](SOURCE_CATALOGUE.json) points to `references/material-catalogue.json` in each of the 27 published skills. The catalogues describe the external material already present: its purpose, local location, recorded source, revision, and license notices. They introduce no new source material or runtime dependencies.

Start with the relevant skill, then filter `entries` by `collection`, `category`, `uses`, or `title`. Open only the selected local paths. The 48 Hallmark recipes, 237 sound presets, 76 game guides, 44 vector styles, motion references/prompts/fonts, and named design-taste recipes have individual entries. Implementations, large datasets, and source-synthesis manifests are indexed as bundles; their linked manifests remain the authority for internal files and per-item provenance. References to external websites, photographs, or font catalogs do not mean those assets are bundled.

Examples:

```sh
jq '.entries[] | select(.collection == "hallmark") | {title, source_url, paths}' skills/theme-factory/references/material-catalogue.json
jq '.entries[] | select(.source_url == "Unknown")' skills/create-motion-videos/references/material-catalogue.json
jq -r '.catalogues[].catalogue_path' SOURCE_CATALOGUE.json
```

These are optional queries with an existing JSON reader; the catalogues themselves need no executable tooling.

## Record format

All `paths`, `notice_paths`, and `provenance_path` values are relative to the owning skill directory. Repository index paths are relative to the repository root.

| Field | Meaning |
| --- | --- |
| `id`, `collection` | Stable identifier and source/material family within the skill |
| `title`, `category`, `description`, `uses` | What the material is and what it supports |
| `paths` | Bundled files or directories containing the material; a directory denotes a bundle, not a claim that every file has one license |
| `record_locator` | Optional original record ID within a shared JSON/HTML dataset; read that dataset for the complete record |
| `source_url` | Recorded original source link, exact upstream file when available, or known source repository when file-level mapping is unavailable |
| `source_commit` | Recorded revision of that source; `"Unknown"` when not established or the source is an unversioned page/post |
| `distribution_url`, `distribution_commit` | Optional known intermediary repository and revision, kept separate when the original source is a post or is unresolved |
| `license` | Recorded license or source-terms label for the specified material; not a new license grant |
| `notice_paths` | Bundled applicable notices; an empty list means no notice file is identified for this record, not that attribution is unnecessary |
| `provenance_path`, `notes` | Supporting local evidence, adaptation boundaries, mixed-source exceptions, and limitations |

`"Unknown"` is the literal sentinel for unresolved source URLs, revisions, or licenses. Do not substitute an empty string, `null`, a guessed repository, or the repository's MIT license. A known repository with unknown file mapping remains useful evidence; its notes disclose that limit. A supplied reference package can have an unknown public location while its contributing upstream sources are known and separately indexed.

Catalogues record existing evidence. They do not retroactively establish missing redistribution rights or authorize importing new material with unknown rights. The relevant `SOURCES.md`, retained license texts, per-asset credits, and upstream manifests still govern reuse. Scores, review dates, and provenance claims carried by upstream datasets are not newly verified by this indexing work.

## Existing provenance records

- The motion [style catalogue](skills/create-motion-videos/references/catalogue.json) continues to drive style lookup and retain engine/constraint details. Its new material catalogue also covers prompt libraries, kits, fonts, and adaptations. The runtime style catalogue is unchanged.
- [Design research data provenance](skills/design-research/data/data-provenance.json) is UI UX Pro Max's audit record for selected dataset rules, styles, contracts, and font/icon catalog snapshots. It records source references, upstream review dates, statuses, and confidence where supplied. `validate_data.py` checks those records and their consistency. This is dataset-level evidence, not an inventory of every skill file or proof that a source remains current; the material catalogue points to it without replacing it.
- Source manifests for office/research guidance, asset hash manifests, and original font/photo notices remain intact. The catalogues summarize and link them rather than copying their complete contents.

## Maintenance

When adding or removing an imported material, update its skill catalogue, the repository index counts, source evidence, and notices together. Use an exact verified source path when available; keep unresolved values as `"Unknown"`. Update `updated_utc` for changed catalogues. Do not regenerate or alter imported datasets merely to make them fit this format.

`tests/test_material_catalogues.py` checks catalogue/index coverage, identifiers, counts, local path containment, required fields, and membership of the independently selectable collections. The normal repository formatting and packaging checks also apply. No live-source availability or authorship audit is implied by those checks.
