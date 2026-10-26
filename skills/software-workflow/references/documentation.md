# Documentation that preserves the contract

Write for the reader's task: quick start, API reference, explanation, migration guide, or troubleshooting. Keep one source of truth and link to it. Verify commands, paths, defaults, errors, and examples against current code; prose copied from a past PR may describe an abandoned design.

Preserve the complete proposition when shortening text: condition, action, reason, consequence, and exception when each changes behavior. Remove conversational scaffolding and obsolete design-session history. Keep comments that explain a non-obvious constraint or ownership decision; omit narration of obvious code. Do not remove a caveat simply because it makes a sentence longer.

For an architectural decision, record the problem, constraints, selected approach, relevant alternatives, and consequences. Keep detail proportional to the decision. Routine edits do not need a new ADR.

For a migration guide, identify affected versions and consumers, exact before/after usage, preservation guarantees, ordered steps, verification, and rollback or recovery limits. For translated documents, preserve headings/links/code/API identifiers and technical claims, track the authoritative source revision, and check that both versions cover the same contract. Do not infer permission to publish translations or create a translation service.

A handoff records completed behavior, relevant files, commands and outcomes, and unresolved work. Store durable project lessons only when supported by evidence; exclude personal data, hidden reasoning transcripts, and one-off preferences.
