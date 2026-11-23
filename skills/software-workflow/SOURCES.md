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
- The core principles, workflow, conflict order, and handoff format follow this repository's `AGENTS.md`: simplicity first, approach validation, owner-first fixes, buy-in for speculative robustness, simplification after implementation, honest verification, and the `## Summary` and `## Verification` pull request structure.
- The eight task references were consolidated into four: plan and design, build and verify, debug and measure, and change and hand off. Web-specific examples were generalized to other platforms and domains. Translation-workflow guidance was removed.
- Retry guidance starts from the duplicate effect to prevent and reuses existing guarantees. Optimization requires evidence, with profiling reserved for uncertain causes or costs. Implementation guidance preserves behavior outside the requested change. Configuration changes verify defaults, inheritance, overrides, and serialization. Checks run in the environment that their manifest or CI job selects.
- Failure handling is limited to failures that a supported path can reach. State ownership guidance requires side-effect-free render and status functions and the discarding of results from superseded requests only.
