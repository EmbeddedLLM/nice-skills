---
name: software-workflow
description: Plan and implement multi-file software changes, diagnose reproducible failures, design API or state contracts, build native or UI features, investigate performance, or prepare migrations and releases using evidence from the existing project. Use when a change needs a plan, a root cause, or a compatibility decision. Do not use for a single-file edit, a mechanical rename, or a question that needs no code change. A review-only request stays read-only.
license: MIT; see SOURCES.md and LICENSE-addy.txt and LICENSE-deepseek.txt
---

# Evidence-led software work

Project instructions always override this skill. When `AGENTS.md`, `CLAUDE.md`, or another project instruction file conflicts with this skill, follow the project file and ignore the conflicting guidance here.

Use the project's source, installed versions, tests, and workflow as the authority. Distinguish the required outcome from a suggested mechanism. Preserve existing behavior and user work; the smallest adequate change wins. This package needs only source access and the project's own tools. It installs no hooks, services, or runtime.

## Choose the needed reference

| Task | Read |
| --- | --- |
| Unclear outcome, design choices, specification, task breakdown, context handoff | [Plan and context](references/plan-and-context.md) |
| Implement a vertical slice, add meaningful tests, simplify, or review a change | [Build and verify](references/build-and-verify.md) |
| Desktop, mobile, or browser UI; view state; main-thread work; accessibility | [UI and native apps](references/ui-and-native-apps.md) |
| Public API, failures, retries, durable or derived state | [Contracts and state](references/contracts-and-state.md) |
| Reproducible bug, flaky test, process or asynchronous teardown | [Debugging and CI](references/debugging-and-ci.md) |
| Slow interaction, memory growth, profiling, telemetry | [Performance and observability](references/performance-and-observability.md) |
| Deprecation, schema change, release, CI pipeline or PR handoff | [Migration and release](references/migration-and-release.md) |
| Documentation, architecture decisions, translations, explanatory prose | [Documentation](references/documentation.md) |

Read only the applicable references. Do not turn a small fix into the full lifecycle, require an interview when the outcome is clear, or infer permission to commit, publish, deploy, send messages, or rewrite history. Delegate only when the user or governing instructions authorize it.

## Apply rules in proportion

Each rule in this skill applies only when its condition is present in the actual change. The references are compressed, so do not extend a rule beyond the case it names. A rule for public APIs does not apply to private helpers. A rule for failure reporting does not apply to a failure that cannot occur.

When two rules conflict, use this order:

1. Project instructions and the user's explicit request.
2. Demonstrated defects and required behavior that must be preserved.
3. The smallest change that meets them.
4. Other guidance in this skill.

For example, the failure-reporting rule in [Contracts and state](references/contracts-and-state.md) does not override the rule against speculative defenses. Add error handling, user messages, or tests for a failure only when a supported path can reach it. When an earlier layer already guarantees the condition, rely on that guarantee. Duplicate handling adds code to maintain and suggests to readers that the failure is possible.

## Working contract

Before editing, identify the requested behavior, concrete preservation requirements, relevant evidence, and verification commands. Keep this in your working notes or reply. Do not create a planning file unless the project or user asks for one. Resolve consequential uncertainty by checking the actual call site, versioned documentation, or a focused experiment. Ask about an ambiguity only when it materially changes behavior, data, security, public interfaces, or architecture; continue independent work.

Use an existing quality bar. New coverage/performance quotas, generalized recovery machinery, or speculative race defenses need evidence and a scope decision, because each one adds permanent code and review cost. Do not weaken required checks to make a patch pass. Fix proven defects within the authorized task, then simplify the final diff without losing behavior.

Examples:

- "Rename a public field without breaking old clients." Inventory consumers, determine the coexistence window, propose the smallest compatible migration, exercise old and new requests, and state the removal condition. A request to plan this migration does not authorize executing it against production.
- "Let users open a folder in the gallery." Find the existing open, selection, and refresh paths and extend them. Keep the selection state in one owner and derive the displayed state from it. Reuse the platform's native folder icon and permission flow. Test the folder list and the selection after refresh. Do not re-validate entries that discovery already filtered.

Deliver the requested artifact or implementation with actual verification outcomes and remaining limitations. A missing tool or inaccessible system is an unverified path, not a successful check.
