# Nice Skills

Open source agent skills: reusable instructions and supporting resources for focused tasks.

The [skill catalog](skills/README.md) contains 22 focused, independently usable skills for research, documents, design, media, security, and development. They use local tools and supplied assets without requiring paid model-provider services. Narrated explainers and presenter edits have complete local routes; paid generation is optional and must be explicitly selected.

## Using a skill

Browse the [skill catalog](skills/README.md), then read the selected skill's `SKILL.md` for its purpose, requirements, and workflow. Follow your agent's instructions for installing a local skill directory, including any bundled resources. Supported tools and environments are documented by each skill.

Copy the whole selected skill directory. Python requirements and optional Node lockfiles belong to that skill; install only the dependencies needed for the task in a writable project environment. Browser binaries, Office-compatible renderers, and media tools may need separate setup. Network access may be needed for initial downloads, but no OpenAI, Anthropic, Minimax, or other paid production API is a prerequisite.

## Repository layout

```text
skills/                  Published skills and their catalog
  <skill-name>/
    SKILL.md             Skill metadata and instructions
    scripts/             Optional executable helpers
    references/          Optional supporting documentation
    assets/              Optional templates and other resources
tests/                   Helper contracts, coverage inventory, and media integration tests
tools/                   Optional reference-corpus audit and maintenance scripts
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

The first invocation needs registry access unless that version is cached. CI also runs helper contracts, provenance checks, synthetic audit-tool tests, and browser/media integration described in [tests/README.md](tests/README.md). Agent behavior still needs separate verification as described in the contribution guide.

The skills and supporting tests are adapted from [Agentic Skills](https://github.com/jiahuei/agentic-skills/tree/8a17f762679feb9df58a26a3fca58468ff157367). Bundled source records and third-party notices retain their upstream attribution.

## License

[MIT](LICENSE). Preserve any bundled third-party license notices and attribution.
