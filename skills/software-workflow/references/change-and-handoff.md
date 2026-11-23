# Change and hand off

## Migrations and deprecations

Before you remove or change an interface, file format, schema, configuration key, or stored data, list its consumers and what they depend on. Separate additive setup, data migration, the switch to the new path, and cleanup, so that old and new versions can coexist. Migrate data in bounded batches and validate each batch. Check whether a storage change locks or rewrites data at the expected scale. Test rollback where possible, and document irreversible steps. Remove the old path only after the agreed condition is met.

## CI and release

The project's CI workflows are the source of truth for check commands and tool versions. Read them before you run checks. In a workflow, pin tools, use least-privilege permissions, and separate untrusted pull request code from publishing jobs. A new pipeline automates an existing required check. It does not redefine the quality bar.

A release plan names the artifact, version, compatibility, rollout, success signal, and recovery action. Use staging, canaries, or flags only when the impact and the existing platform justify them. Preparing a release does not authorize publishing, tagging, merging, or force-pushing.

## Documentation

After every change, check whether documentation needs an update, even when the task did not mention it. Write for the reader's task, keep one source of truth, and link to it. Verify commands, paths, defaults, and examples against the current code.

Write for understanding on the first read. Use familiar words and consistent terms. Put one main idea in each sentence. Prefer active voice, and make conditions, actions, and consequences explicit. When you shorten text, keep each condition, reason, and exception that changes behavior.

## Pull requests and handoff

Before you choose a pull request title, follow the style of recent commits on the main branch. Describe the final diff for a reviewer who has not read the conversation:

```markdown
## Summary

- <Problem, completed change, and resulting behavior>

## Verification

- `<command>`: <outcome, or the reason it was not run>
```

Use declarative statements. List failed and skipped checks with their reasons. Separate local verification from pending CI and from deployment. When you update a pull request, rewrite the summary so that it describes the whole current diff. Do not append one bullet for each new commit.

Keep task context restartable: the purpose, branch or revision, changed files, decisions and reasons, commands and results, remaining work, and blockers. Store durable lessons only when evidence supports them. Do not store credentials, personal data, or speculative reasoning.
