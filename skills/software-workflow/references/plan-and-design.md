# Plan and design

## Requirements

Separate user goals, known facts, assumptions, constraints, non-goals, and the proposed implementation. For an uncertain product idea, identify who needs it, the task they struggle with, the smallest useful outcome, and how success can be observed. Ask only for answers that change the work. Do not require a second approval for work that is already authorized.

A useful specification states inputs, outputs, important states, failure behavior, exclusions, and acceptance examples. Split substantial work into vertical slices, each with a verification point. Make one end-to-end path work before adding variants. Add a feature flag or configuration option only when deployment or coexistence needs it, and give it an owner and a removal condition.

## Evidence

For a question about a library, framework, SDK, engine, or protocol, find the installed version in the manifest or lockfile. Read its exported interface, then use the official documentation for that version. A current web example may not match an older dependency. Test uncertain behavior with a focused experiment. For a consequential trade-off, record the problem, constraints, selected approach, alternatives, and consequences. Routine edits do not need a design document.

## Interfaces

An interface is any boundary that other code or people depend on: a function, an API, a command-line tool, a file format, a message, a configuration key, or user-visible behavior. Before changing one, define its observable contract: inputs, outputs, errors, ordering, cancellation, permissions, and compatibility. Follow the project's naming and error conventions. Prefer additive changes when old and new consumers coexist. Keep machine-readable error identities stable, because display text is not an identity. Validate untrusted data once, at the trust boundary. Do not repeat the check between internal layers that already received validated data.

## State ownership

Give each piece of state one owner. Derive displayed, formatted, or cached values from that owner instead of storing a second copy. When a default depends on other state, decide whether the owner stores it or computes it on read. Store it when later updates must keep it.

Keep functions that render, format, or report status free of side effects. When such a function changes state, starts work, or requests permission, the behavior depends on call order and frequency, and it becomes hard to reproduce.

For asynchronous or concurrent work, tag each request with a generation or token. Discard a result that no longer matches the current state, so that an obsolete result cannot replace newer state. Keep thread-bound state, such as UI state, on its required thread or actor. Do not hide I/O in a getter or property.

## Failure handling

Handle a failure only when a supported path can reach it. An operation is not fallible merely because its type can throw or return an error. When an earlier layer already guarantees the condition, rely on that guarantee. Duplicate handling adds code to maintain, and it suggests to readers that the failure is possible.

For each reachable failure, identify the owner of its state, reporting, cleanup, and recovery. State whether the failure leaves no effects, partial effects, committed effects, or an unknown outcome. Catching an error does not roll back changes, and logging is not recovery. Background work has the same obligations as foreground work. When the failure affects the user, show what failed and a safe next action. Keep diagnostic detail and secrets out of user-facing text.

When an operation with external effects must be retried safely, bind one idempotency key to one intent and reuse it across attempts. Keep enough state to reconcile an unknown outcome, because a timeout does not prove that nothing happened. Do not add this machinery when retries are harmless.

For persisted or replayed state, persist facts and schemas, not handles, connections, or process ownership. Recovery must be deterministic and must not repeat external effects. Caches can be discarded, so they must not become a second source of truth.
