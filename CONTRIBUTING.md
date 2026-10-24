# Contributing

Contributions should add a useful, focused skill or improve an existing skill's reliability and clarity. For large changes, describe the intended use case in an issue before investing in implementation.

## Add a skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Add only the supporting resources the workflow needs inside that directory.
3. Verify the skill as described below.
4. Add a relative link and a short purpose statement to [the catalog](skills/README.md).
5. Open a pull request describing the resulting behavior and verification.

Use this minimal entry point as a starting point, replacing the example name and instructions:

```markdown
---
name: example-skill
description: Summarizes a local project README into a concise overview. Use when asked for a project summary based on its README.
license: MIT
---

# Project overview

## Workflow

1. Locate the README in the user-selected project.
2. Read it and identify the project's purpose, setup steps, and usage.
3. Return a short overview grounded in the file. Identify missing information without inventing details.

## Verification

Confirm that each factual statement is supported by the README.
```

This example belongs in documentation until replaced with a complete, useful skill.

## Format and resources

Follow the [Agent Skills specification](https://agentskills.io/specification):

- Start `SKILL.md` with YAML frontmatter containing `name` and `description`.
- Use a lowercase name of 1-64 letters, digits, or hyphens matching the directory. Do not use leading, trailing, or consecutive hyphens.
- Keep the description nonempty and at most 1,024 characters; state what the skill does and when to use it.
- Use optional `compatibility` metadata when environment requirements matter.
- Keep the entry point concise; move detailed guidance into linked `references/` files.
- Put executable helpers in `scripts/` and templates or other resources in `assets/` when needed. Use relative paths from the skill directory.

Repository conventions:

- Document prerequisites and expected outputs. Include a representative example and explain missing-input or failure behavior where relevant.
- Keep each skill usable when copied on its own. Bundle required resources, and identify external dependencies explicitly.
- Use portable paths and synthetic data. Never commit credentials or private user material.
- Make side effects clear and respect the host agent's authorization model.
- Record every added or changed external dependency, optional tier, and minimum version in [DEPENDENCIES.md](DEPENDENCIES.md).
- Preserve third-party notices. Original contributions use the repository's [MIT license](LICENSE); identify any separately licensed bundled materials.

## Verification

For every skill addition or behavior change:

1. Check the frontmatter against the specification and confirm the name matches the directory.
2. Resolve all bundled references from the skill directory.
3. Try a representative request in an intended agent environment; check the expected output and any relevant missing-input case.
4. Run changed helpers with representative inputs and relevant failure cases. Keep tests local and deterministic where practical.
5. Record what ran, the environment, and any limitations in the PR.

CI checks formatting, published skill metadata, local helper contracts, and skill-local regressions. See [tests/README.md](tests/README.md) for the pinned environment, commands, coverage, and optional skips. These checks do not execute the complete skills in an agent or establish visual quality. If agent behavioral verification is unavailable, say so explicitly so reviewers can assess the remaining work.

From the repository root, run the same pinned formatter as CI:

```sh
npx --yes prettier@3.8.3 --check '**/*.{md,yml,yaml,json}' .prettierrc
git diff --check
```

Use `npx --yes prettier@3.8.3 --write <paths>` to format edited files. The initial invocation requires registry access unless the package is cached. CI uses Node.js 24.

Keep intentional fixtures trackable. If a fixture must retain exact whitespace, add a narrow path exception to `.prettierignore` and explain why.

## Pull requests

Use this structure and include actual outcomes:

```markdown
## Summary

- Describe the problem and resulting behavior.

## Verification

- List commands and behavioral checks, their results, and any limitations.
```

Keep the change focused, update the catalog and relevant documentation, and avoid generated output or unrelated dependency changes.
