---
name: software-workflow
description: Plan and implement substantial software changes, diagnose failures, design API contracts, investigate performance, or prepare migrations and releases using evidence from the existing project. Use for engineering lifecycle work beyond a narrow mechanical edit; a review-only request stays read-only.
license: MIT; see SOURCES.md and LICENSE-addy.txt and LICENSE-deepseek.txt
---

# Evidence-led software work

Use the project's source, installed versions, tests, and workflow as the authority. Distinguish the required outcome from a suggested mechanism. Preserve existing behavior and user work; the smallest adequate change wins. This package needs only source access and the project's own tools. It installs no hooks, services, or runtime.

## Choose the needed reference

| Task | Read |
| --- | --- |
| Unclear outcome, design choices, specification, task breakdown, context handoff | [Plan and context](references/plan-and-context.md) |
| Implement a vertical slice, add meaningful tests, simplify, or review a change | [Build and verify](references/build-and-verify.md) |
| Public API, failures, retries, durable or derived state | [Contracts and state](references/contracts-and-state.md) |
| Reproducible bug, flaky test, process or asynchronous teardown | [Debugging and CI](references/debugging-and-ci.md) |
| Slow interaction, memory growth, profiling, telemetry | [Performance and observability](references/performance-and-observability.md) |
| Deprecation, schema change, release, CI pipeline or PR handoff | [Migration and release](references/migration-and-release.md) |
| Documentation, architecture decisions, translations, explanatory prose | [Documentation](references/documentation.md) |

Read only the applicable references. Do not turn a small fix into the full lifecycle, require an interview when the outcome is clear, or infer permission to commit, publish, deploy, send messages, or rewrite history. Delegate only when the user or governing instructions authorize it.

## Working contract

Record the requested behavior, concrete preservation requirements, relevant evidence, and verification commands. Resolve consequential uncertainty by checking the actual call site, versioned documentation, or a focused experiment. Ask about an ambiguity only when it materially changes behavior, data, security, public interfaces, or architecture; continue independent work.

Use an existing quality bar. New coverage/performance quotas, generalized recovery machinery, or speculative race defenses need evidence and a scope decision. Do not weaken required checks to make a patch pass. Fix proven defects within the authorized task, then simplify the final diff without losing behavior.

Example: "Rename a public field without breaking old clients." Inventory consumers, determine the coexistence window, propose the smallest compatible migration, exercise old and new requests, and state the removal condition. A request to plan this migration does not authorize executing it against production.

Deliver the requested artifact or implementation with actual verification outcomes and remaining limitations. A missing tool or inaccessible system is an unverified path, not a successful check.
