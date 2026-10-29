# Migrations, CI, and release handoff

Inventory supported consumers and their observable dependencies before removing an interface. Establish the replacement's required coverage, migration cost, compatibility window, and evidence for retirement. Migrate consumers with verification; remove the old path only after the chosen usage/compatibility condition is met.

For a rolling schema change, separate additive setup, migration/backfill, read cutover, and destructive cleanup so old and new code can coexist. For example, add a replacement field, maintain the required writes, backfill in bounded batches with validation, switch reads, then remove the old field in a later authorized step. Use the database's documented locking and index behavior. Additive DDL can still lock or rewrite a table: test it at the relevant scale. Test rollback where possible and document irreversible steps and recovery; a down migration cannot magically restore deleted data.

Read the repository's release workflow and select checks from the actual diff and consumers. Use pinned tools and least-privilege job permissions. Separate untrusted PR execution from privileged publishing. A new pipeline should automate an existing required check, not invent a repository-wide stack or silently redefine quality thresholds.

A release plan names the artifact, version, compatibility, rollout, observable success/failure, and recovery action. Staging/canary/flags are options justified by impact and the existing platform, not mandatory layers. Preparing a release does not authorize deploying it. Do not publish, merge a stack, tag, force-push, or contact others without relevant authorization. For stacked PRs, inspect the hosting platform's current supported semantics instead of copying a repository-specific API.

Write a PR for the final diff: concrete problem, resulting behavior, material implementation choice, and actual verification. Rewrite stale descriptions after scope changes. Separate local tests, pending CI, and deployment verification. Preserve contributor attribution and required notices. Keep instructions for commands that could mutate real data explicit and scoped.
