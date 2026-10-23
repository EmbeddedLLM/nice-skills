# Nice Skills

Open source agent skills: reusable instructions and supporting resources for focused tasks.

Published skills live in [`skills/`](skills/README.md). The repository is currently a foundation; no skills have been published yet.

## Using a skill

Browse the [skill catalog](skills/README.md), then read the selected skill's `SKILL.md` for its purpose, requirements, and workflow. Follow your agent's instructions for installing a local skill directory, including any bundled resources. Supported tools and environments are documented by each skill.

Copy the whole selected skill directory, including any bundled resources and dependency manifests. Install only the dependencies needed for the task in a writable project environment; each skill should document any additional setup or network access it requires.

## Repository layout

```text
skills/                  Published skills and their catalog
  <skill-name>/
    SKILL.md             Skill metadata and instructions
    scripts/             Optional executable helpers
    references/          Optional supporting documentation
    assets/              Optional templates and other resources
CONTRIBUTING.md          Authoring, review, and verification guidance
AGENTS.md                Instructions for agents working on this repository
CLAUDE.md                Pointer to the shared agent instructions
.github/workflows/       Repository checks
```

The skill layout follows the [Agent Skills specification](https://agentskills.io/specification).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) before adding or changing a skill. Keep each skill focused and independently usable, and update the catalog when publishing one.

Formatting requires Node.js and npm. CI uses Node.js 24 and Prettier 3.8.3:

```sh
npx --yes prettier@3.8.3 --check '**/*.{md,yml,yaml,json}' .prettierrc
```

The first invocation needs registry access unless that version is cached. CI currently checks formatting; skill behavior must be verified as described in the contribution guide.

The repository foundation is adapted from [Agentic Skills](https://github.com/jiahuei/agentic-skills/tree/8a17f762679feb9df58a26a3fca58468ff157367).

## License

[MIT](LICENSE). Preserve any bundled third-party license notices and attribution.
