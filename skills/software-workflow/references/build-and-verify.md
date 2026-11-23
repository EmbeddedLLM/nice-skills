# Build and verify

## Implement

Start with the smallest slice that preserves existing behavior. Locate its callers, the state owner, the boundary contracts, and the existing tests. Follow the existing style of each file and use meaningful names.

Prefer platform conventions and components: the standard library, native controls and dialogs, and idiomatic types. A platform component already provides accessibility, localization, and system behavior that a custom copy must rebuild. A new dependency must remove more work than it adds. Pin its exact version and commit the lockfile.

Write comments only to explain why. Comment logic that is surprising, encodes a business rule or architectural decision, deviates from a convention, reflects a trade-off or workaround, or depends on ordering or a non-obvious invariant. State the problem, the requirement, and the consequence of violating it. Do not narrate the code. Remove comments that become obsolete.

## Test

Derive tests from observable behavior and preservation requirements, not from the implementation. For a defect, reproduce it first when practical: write a failing regression test, make the minimum fix, then clean up. Cover error paths and the state after a failure, not only successful results. A mock that was called does not prove that an integration works. State the purpose of each test in its name or docstring, for example "Ensures that ...".

Exercise real boundaries where feasible: the file system, a database, a child process, a device, input events, a public API, or cancellation. Keep tests isolated and deterministic with synthetic fixtures.

Run focused checks first, then the project's CI checks for formatting, linting, static analysis, and tests. Use the commands and tool versions that CI defines. Do not weaken the quality bar to make a check pass: deleted assertions, skipped tests, suppressions, lowered budgets, and placeholder implementations can hide a regression. Do not reformat unrelated files. When a check needs an environment you do not have, such as a device, an operating system, or a visual inspection, report it as unverified with the exact command or manual step.

## Review

Review correctness, simplicity, architecture, security, and performance on the changed paths. Read tests as claims and trace each claim into the implementation. Check that ordering, errors, output shape, cleanup, and public interfaces are preserved.

A finding names the trigger, the faulty behavior, the location, the impact, and the smallest fix. Separate a demonstrated defect from a question or a preference. A security concern needs a concrete trust boundary and a reachable effect. A performance concern needs a plausible workload. Use a separate reviewer only when delegation is authorized. Ask reviewers to challenge whether the mechanism is necessary, not only whether it is correct.

## Simplify

Start by asking which obligation can be removed. Before you delete a branch, a compatibility layer, or an abstraction, prove that it has no remaining consumers. Put genuinely shared validation, state updates, and finalization in one place, and keep variant-specific behavior explicit. Avoid helpers that only move a few lines. Prefer sufficient correctness over absolute correctness, for example eventual consistency or a simple retry when failure is cheap and recoverable. Compare the full diff after cleanup.

## Security

For a security-sensitive change, map the assets, entry points, trust boundaries, and permission checks before you choose controls. Check authorization at the operation that reads or changes protected data. Validate untrusted input at its boundary, use parameterized queries, and use the platform's permission and sandbox APIs. Keep secrets out of fixtures and logs. Test a permitted request, a denied request, and malformed input with synthetic identities. Reuse the project's existing scanners. A generic checklist does not prove safety.
