---
name: review-agent
description: Perform a read-only review of a code change and report actionable defects with evidence and severity. Use for uncommitted changes, a commit, a base-branch diff, or a requested review scope.
license: MIT
---

# Code review

Read repository instructions, inspect the complete requested change, and report defects the author would reasonably fix. Local Git, file reading, and relevant tests are enough; no paid review service is required.

## Establish the comparison

Inspect status before choosing the diff. For uncommitted work include staged and unstaged changes and relevant untracked files. For a commit, compare with its appropriate parent. For a branch, resolve the requested base and use the merge base so the review covers what would merge, not unrelated changes on the base.

Use a configured upstream when it is the intended, newer comparison; do not silently substitute an unrelated branch. If a ref is missing, identify the limitation rather than reviewing an arbitrary diff. Include enough surrounding code, callers, and tests to assess behavior.

## Evaluate

Review every affected path. A finding must be introduced by the change, discrete, consequential, and supported by a demonstrable scenario. Prioritize correctness, security, data integrity, performance, and behavior. Do not present pre-existing issues, deliberate scope changes, unsupported possibilities, or cosmetic preferences as regressions.

Confirm candidates against callers and tests. Run proportionate read-only or disposable checks when available, recording what ran. Keep the review itself read-only: do not edit source, commit, push, post, or delegate without authorization for those actions.

## Report

List findings in severity order, each with a short title, the smallest useful location in the changed code, the triggering scenario, consequence, and recommended correction.

- `P0`: universal critical blocker.
- `P1`: urgent defect.
- `P2`: ordinary actionable defect.
- `P3`: low-impact defect worth correcting.

If none qualify, say `No findings.` Include an overall assessment and material verification gaps; absence of findings does not establish untested behavior.

Example: “Review this change to monthly invoice aggregation.” Check date boundaries, duplicate records, units, and downstream totals against the actual diff. Report a reproducible boundary error with its affected lines rather than inventing a generic test-coverage finding.
