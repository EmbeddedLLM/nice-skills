# Build, test, review, simplify

Start with the smallest behavior-preserving slice. Locate its callers, state owner, boundary contracts, and existing tests. Prefer stdlib/native features, then installed dependencies. A dependency must remove more work than it adds; use the project's exact pins and lockfiles.

Derive tests from user-observable behavior and preservation requirements. For a defect, reproduce it before fixing it when practical. Use a failing regression, the minimum fix, then cleanup; do not force test-first scaffolding for prose or a trivial reversible edit. Cover errors and state after failure, not only successful return values. A mock proving it was called does not prove an integration works.

Run focused checks first, then the required broader workflow. Exercise real boundaries where feasible: filesystem results, database effects, browser interactions, public APIs, cancellation, or output decoding. Avoid external side effects merely to validate documentation. State skips and environment constraints with exact commands.

Review across correctness, simplicity, architecture, security, and performance, concentrating on the changed paths. Read tests as claims, trace each claim into implementation, and inspect actual consumers. A security concern needs a concrete trust boundary and reachable effect; a performance concern needs a plausible workload and measurement. Do not turn every review into a speculative audit.

A finding names the trigger, faulty behavior, affected contract, location, impact, and smallest fix. Separate a demonstrated defect from a question or preference. Check preservation of ordering, errors, output shape, cleanup, and existing behavior. Use a separate reviewer only when delegation is authorized; otherwise perform a deliberate second pass.

Simplification starts by asking which obligation can be removed. Before deleting a branch, compatibility layer, configuration, or abstraction, prove its consumers and purpose. Merge genuinely shared validation/finalization, keep variant behavior explicit, and avoid helpers that merely move a few lines. Do not infer dead code from an old commit date. Compare the full diff after cleanup and retain the relevant verification evidence.

For security-sensitive changes, map the actual assets, entry points, trust boundaries, and permission checks before selecting controls. Trace authorization at the operation that reads or mutates protected state; validate untrusted data at its boundary, use parameterized queries, and keep secrets out of fixtures and logs. Exercise a permitted request, a denied request, and malformed input with synthetic identities. Reuse the existing secret/dependency scanners and verify findings against reachable code. A generic checklist neither proves safety nor justifies adding unrelated infrastructure. Report residual risk and required checks without weakening an existing control.
