# API contracts, failure ownership, and recoverable state

Define the externally observable contract before changing an API: required/optional inputs, output variants, error identities, authorization boundary, cancellation, ordering, and compatibility. Use the project's naming and error conventions. Validate data at actual trust boundaries; do not add repeated checks between already-validated internal layers without a concrete need.

Prefer additive evolution when supported clients coexist. Distinguish omission, null, and empty values in partial updates. Specify stable ordering and pagination when bounded responses are required. Preserve public error discriminants; display text is not a machine-readable error identity.

For each fallible operation, identify the owner of its state, reporting, cleanup, and recovery. Specify whether failure leaves no effects, partial effects, committed effects, or an unknown outcome. Catching an exception does not roll back mutations. Continue only when the state owner can establish the required invariant; logging is not recovery. Background tasks have the same obligations as foreground work.

When a required operation must be safely retried, bind one idempotency key to one intent, reuse it across attempts, validate that a repeated key has the same payload, and let an atomic store constraint claim it. Choose a bounded pending/duplicate response. Preserve enough state to reconcile an unknown remote outcome; a timeout is not proof that nothing happened. Retention must cover the actual redelivery horizon. Do not add this machinery where retries are harmless and no exactly-once effect is required.

Surface a readable failure summary, the affected operation, and a safe next action. Persistent invalid state needs persistent visibility. Separate diagnostic detail from user-facing text, preserve causes for authorized diagnostics, and avoid leaking secrets. Verify the resulting state and report, not just that the exception was caught.

For event-derived state, persist facts and schemas, not promises, handles, sockets, or process ownership. Recovery/replay must be deterministic and must not repeat external effects. A valid checkpoint plus suffix replay should match full replay. Keep required payloads available to synchronous readers; do not hide I/O in a getter or replace a synchronous API with a promise implicitly. Caches are discardable and cannot become a second recovery implementation. Version recovery semantics when they change, and test missing/incompatible checkpoints and disposal during activation.
