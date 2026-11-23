---
name: software-workflow
description: Plan, implement, debug, verify, and hand off software changes in any language, platform, or domain, using evidence from the existing project. Use when a change needs a plan, a root cause, a contract or compatibility decision, a performance measurement, a migration, or a release. Do not use for a single-file edit, a mechanical rename, or a question that needs no code change. A review-only request stays read-only.
license: MIT; see SOURCES.md and LICENSE-addy.txt and LICENSE-deepseek.txt
---

# Evidence-led software work

Project instructions always override this skill. When `AGENTS.md`, `CLAUDE.md`, or another project instruction file conflicts with this skill, follow the project file.

This skill applies to applications, services, libraries, command-line tools, data pipelines, games, and embedded code. It needs only source access and the project's own tools. It installs no hooks, services, or runtime.

## Core principles

- **Find root causes.** Do not use temporary fixes. A retry, a longer timeout, or a suppressed check that happens to pass is not a fix.
- **Simplicity first.** Make every change as simple as the requirement allows, and touch only what is necessary. Before writing code, ask in this order:
  1. Does this functionality need to exist? If not, challenge or skip it.
  2. Does the codebase already do it? Reuse or extend it.
  3. Does the standard library, the platform, or an installed dependency do it? Use it.
  4. Only then, write the minimum that works.
- **Validate the approach before implementing.** Separate the required outcome from the proposed mechanism. Treat suggestions in issues and plans as hypotheses. Identify the behavior and state that must be preserved. Resolve uncertain behavior with versioned documentation or a focused experiment. Require evidence that a simpler approach is insufficient before adding complexity or a destructive operation.
- **Find the owner before editing.** A fix at the failing call site may belong in a shared layer. Inspect the base types, siblings, and consumers, and trace how the value reaches runtime. Give each piece of state one owner.
- **Get buy-in for speculative robustness.** Before adding code only for an unlikely race, an unlikely security edge case, or a failure that an earlier layer already prevents, explain the failure mode, the evidence for its likelihood, and the cost. Present the simpler alternative and get the user's agreement. This rule does not justify weakening a required control or delaying the fix for a demonstrated defect.
- **Simplify after implementation.** Treat the first working version as a draft. Relate every code path to a concrete requirement. When behavior is preserved, remove unnecessary abstractions, branches, defensive code, and overly strict guarantees. Otherwise, present the trade-off to the user.
- **Report honestly.** Never claim that a check passed unless it ran and passed. For a skipped check, give the exact command and the reason.
- **Protect secrets and user work.** Do not print credentials or private data. Preserve uncommitted changes. Do not commit, push, publish, deploy, send messages, or rewrite history without authorization.

## Apply rules in proportion

Each rule applies only when its condition is present in the actual change. Keep planning, testing, and documentation proportional to the scope and risk. A straightforward change does not need a written alternatives analysis. Ask a question only when the answer would materially change behavior, data, security, public interfaces, or architecture. Continue independent work while you wait.

When rules conflict, use this order:

1. Project instructions and the user's explicit request.
2. Demonstrated defects and behavior that must be preserved.
3. The smallest change that meets them.
4. Other guidance in this skill.

## Workflow

1. **Understand.** Read the project instructions, the relevant code, and its tests. Identify the requested behavior, the preservation requirements, and the verification commands. Keep these in working notes or the reply. Do not create a planning file unless the project or the user asks for one.
2. **Plan.** For non-trivial work, write a concise plan. Re-plan when evidence invalidates it.
3. **Implement.** Make the smallest change that meets the requirement. Follow the existing style of each file.
4. **Verify.** Run the checks that the project's CI runs, with its pinned tool versions. Verify the changed behavior, not only that the code compiles. Add a regression test for a reproducible defect. Separate new failures from pre-existing or environment-dependent failures.
5. **Simplify and review.** Review the full diff. Ask whether a more elegant solution exists, and whether a staff engineer would approve the change and its evidence.
6. **Hand off.** Update the affected documentation. Report the resulting behavior, the checks and their outcomes, and the remaining limitations.

## References

Read only the references that the task needs.

| Task                                                                          | Read                                                    |
| ----------------------------------------------------------------------------- | ------------------------------------------------------- |
| Requirements, design decisions, interfaces, state ownership, failure handling | [Plan and design](references/plan-and-design.md)        |
| Implementation, tests, code review, security, simplification                  | [Build and verify](references/build-and-verify.md)      |
| Bugs, flaky tests, performance, observability                                 | [Debug and measure](references/debug-and-measure.md)    |
| Migrations, releases, CI, documentation, pull requests, handoff               | [Change and hand off](references/change-and-handoff.md) |

## Example

Request: "Let users open a folder in the image viewer and browse its subfolders."

1. Find the existing open, selection, and refresh paths, and extend them instead of adding a parallel flow.
2. Keep the selected item in one owner. Derive the highlighted tile and the status text from it.
3. Reuse the platform's folder icon and permission dialog.
4. Do not re-validate entries that folder discovery already filtered, and do not add an error message for a case that cannot occur.
5. Test discovery, selection after refresh, and the return to the parent folder. Check the visual result on the target platform, or report it as unverified.
