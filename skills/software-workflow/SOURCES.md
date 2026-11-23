# Sources and notices

Browse the [material catalogue](references/material-catalogue.json) for local paths, uses, source links, revisions, and recorded licenses. Unresolved provenance fields are written as `"Unknown"`; the catalogue does not replace the notices and scope below.

## addy: adaptation retrieved 2026-10-26

Source: [https://github.com/addyosmani/agent-skills](https://github.com/addyosmani/agent-skills/tree/aeac41d4d005999432bb7312f7ff06383a91d59d), revision `aeac41d4d005999432bb7312f7ff06383a91d59d`. License: MIT; retained in [LICENSE-addy.txt](LICENSE-addy.txt).

Consolidated all 25 engineering skill topics into task-routed references. Removed mandatory interviews, universal fixed thresholds, sibling-skill dependencies, automatic commits/deploys, and speculative infrastructure. Existing project rules and user scope remain authoritative.

## deepseek: adaptation retrieved 2026-10-26

Source: [https://github.com/deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness/tree/22ddee3792402c3e70ec5f86a63c3e3e895a2f60), revision `22ddee3792402c3e70ec5f86a63c3e3e895a2f60`. License: MIT; retained in [LICENSE-deepseek.txt](LICENSE-deepseek.txt).

Adapted failure ownership, CI isolation, performance measurement, simplification, session-derived state, documentation, migration, and handoff practices. Excluded DSH-only Cordis APIs, stack APIs, package paths, artwork conventions, translation tooling, and AI grading policy.

## Local revisions

- The first instruction in `SKILL.md` states that project instruction files, such as `AGENTS.md`, override this skill.
- `SKILL.md` adds a narrower trigger description, a conflict order, a rule for proportional application, a UI example, and a note that working records stay out of new files unless requested.
- `references/contracts-and-state.md` limits failure ownership and failure messages to failures that a supported path can reach.
- `references/ui-and-native-apps.md` is locally authored. It does not adapt either upstream source.
