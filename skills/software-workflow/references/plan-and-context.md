# Plan from requirements and evidence

Separate user goals, known facts, assumptions, constraints, non-goals, and proposed implementation. For an uncertain product idea, identify who needs it, the task they struggle with, the useful smallest outcome, and how success can be observed. Interview only for answers that change the work; stop once the requirement is actionable. Do not invent a numeric confidence threshold or require a second approval for work already authorized.

Before adding infrastructure, inspect the existing code and native platform. Compare the smallest plausible alternatives against preservation requirements, implementation cost, and ongoing ownership. Test uncertain behavior with a focused spike. Keep a short decision record for consequential trade-offs; routine edits do not need a design document.

A useful specification states inputs, outputs, important states, failure behavior, exclusions, and acceptance examples. Split substantial work into vertical slices with dependencies and a verification point. Prefer a working end-to-end path before expanding variants. Add a feature flag only when deployment or coexistence actually needs it, with an owner and removal condition.

For a library or protocol question, identify the installed version from the manifest and lockfile, inspect its exported types and implementation, then use matching official documentation. Cite the controlling symbol or file. Do not assume a current web example matches an older dependency or add a local workaround before checking the supported API.

Keep task context restartable: purpose, branch/revision, files changed, decisions and reasons, commands and results, remaining work, and blockers. Store concise state in the project's established location; preserve facts and constraints before conversational history. Do not copy credentials, private prompts, or speculative reasoning into durable notes. Reconcile conflicting instructions through authority and recency, rather than silently combining incompatible plans.

When asked to establish quality constraints, record only agreed dimensions and enforceable thresholds. Where no threshold exists, measure a baseline first. Track exceptions with a reason and review/removal condition. Audit the bar itself: deleted assertions, skipped tests, suppressions, lower budgets, and placeholder implementations can conceal a regression.
