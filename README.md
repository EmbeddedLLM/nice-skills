# Nice Skills

Open source agent skills: reusable instructions and supporting resources for focused tasks.

The [skill catalog](skills/README.md) contains 27 focused, independently usable skills for research, documents, design, media, security, and development. They use local tools and supplied assets without requiring paid model-provider services. Narrated explainers and presenter edits have complete local routes; paid generation is optional and must be explicitly selected.

## Using a skill

Browse the [skill catalog](skills/README.md), then read the selected skill's `SKILL.md` for its purpose, requirements, and workflow. Follow your agent's instructions for installing a local skill directory, including any bundled resources. Supported tools and environments are documented by each skill.

Copy the whole selected skill directory. Python requirements and optional Node lockfiles belong to that skill; install only the dependencies needed for the task in a writable project environment. The [software and dependency reference](DEPENDENCIES.md) lists each skill's required and optional tools, the tested versions, and install commands. Browser binaries, Office-compatible renderers, and media tools may need separate setup. Network access may be needed for initial downloads, but no OpenAI, Anthropic, Minimax, or other paid production API is a prerequisite.

## Repository layout

```text
skills/                  Published skills and their catalog
  <skill-name>/
    SKILL.md             Skill metadata and instructions
    scripts/             Optional executable helpers
    references/          Optional supporting documentation
    assets/              Optional templates and other resources
tests/                   Helper contracts, coverage inventory, and media integration tests
site/                    Homepage HTML, styles, and browser interactions
tools/                   Homepage builder and optional reference-corpus audit tools
DEPENDENCIES.md          Required and optional software per skill
Dockerfile              Sample Ubuntu 24.04 environment with every dependency
CONTRIBUTING.md          Authoring, review, and verification guidance
AGENTS.md                Instructions for agents working on this repository
CLAUDE.md                Pointer to the shared agent instructions
.github/workflows/       Repository checks and GitHub Pages deployment
```

The skill layout follows the [Agent Skills specification](https://agentskills.io/specification).

## Repository homepage

The homepage showcases every published skill with search, focus filters, local requirements, and all 51 theme-factory palettes. The selected theme is saved in the visitor's browser. Skill links and setup guidance remain available without JavaScript.

Build and preview locally with Python 3.12 or later; no additional packages are needed:

```sh
python3 tools/build_site.py
python3 -m http.server 8000 --directory dist
```

Open `http://localhost:8000`. The builder reads `skills/README.md` and the theme-factory guide, verifies catalog completeness and theme contrast contracts, and writes only homepage assets to ignored `dist/`. Edit the page layout in `site/`; update skill descriptions in the catalog and palettes in their original guide. `--output <directory>` selects another build destination. `--source <directory>` reads homepage/catalog/theme inputs from a snapshot, and `--source-ref <commit>` points skill links at that commit; Python helpers always execute from the trusted builder checkout. Invalid catalog paths, incomplete catalog coverage, or invalid theme data fail the build with an error.

The [GitHub Pages workflow](.github/workflows/pages.yml) follows the snapshot deployment pattern in [pdf-unlocker](https://github.com/jiahuei/pdf-unlocker/blob/main/.github/workflows/deploy.yml). Every deployment includes current `main` at the root and every open same-repository PR targeting `main` at `pr-preview/<number>/`. Opening, reopening, updating, or closing a PR rebuilds that set; pushes to `main` and manual runs from `main` rebuild it too. Closed or merged previews disappear at the next successful deployment. Runs are serialized so production and previews share one complete Pages artifact.

After deployment, a bot comment on each PR links to its preview and exact source commit. The existing comment updates on new commits; closed PR comments are marked removed. Fork PRs are excluded, matching the reference workflow. Relative assets support repository Pages URLs and custom domains.

In **Settings > Pages > Build and deployment**, select **GitHub Actions** as the source. The production URL is shown by the deployment's `github-pages` environment. The `github-pages` environment must allow deployments from `main`, and repository Actions settings must allow the workflow's `pull-requests: write` token to create comments. No repository settings are changed by the workflow. Preview automation becomes active once this workflow and its helpers are on `main`; it cannot preview its own initial implementation before merge.

Preview jobs use `pull_request_target` with an explicit trusted `main` checkout. [GitHub's event documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target) explains this execution context and why PR code must not run there. The snapshot helper reads only regular Git blobs for the homepage assets, skill catalog, published skill markers, and theme guide. It never checks out or executes PR Python helpers. Consequently, previews reflect PR HTML/CSS/JavaScript, catalog, and palette data; changes to Python rendering logic take effect after merge. Invalid or unsafe inputs fail packaging before replacing the previous output, and the live deployment remains unchanged.

`python3 tools/pages_preview.py build` requires Git, network access, `GITHUB_REPOSITORY`, a read-only `GITHUB_TOKEN` with contents/PR access, and the Actions `GITHUB_OUTPUT` file. It fetches current immutable commits, renders the site into `dist/`, and exports the packaged preview list. `python3 tools/pages_preview.py comment` uses `PAGE_URL` and `DEPLOYED_PREVIEWS` from the successful deployment plus a token with PR write access to reconcile comments. Both commands run automatically in the workflow; local tests use temporary repositories and mocked API calls without publishing or commenting.

The website uses Python's standard library to build and native HTML/CSS/JavaScript in the browser. Browser checks reuse the existing locked media-test Chromium; see [tests/README.md](tests/README.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) before adding or changing a skill. Keep each skill focused and independently usable, and update the catalog when publishing one.

Formatting requires Node.js and npm. CI uses Node.js 24 and Prettier 3.8.3:

```sh
npx --yes prettier@3.8.3 --check '**/*.{md,yml,yaml,json}' .prettierrc
```

The first invocation needs registry access unless that version is cached. CI also runs helper contracts, provenance checks, synthetic audit-tool tests, and browser/media integration described in [tests/README.md](tests/README.md). Agent behavior still needs separate verification as described in the contribution guide.

The skills and supporting tests are adapted from [Agentic Skills](https://github.com/jiahuei/agentic-skills/tree/8934585901d6ee46ff8d2de212ddee61f1b2397c). Bundled source records and third-party notices retain their upstream attribution.

## License

[MIT](LICENSE). Preserve any bundled third-party license notices and attribution.

The [source adaptation review](SOURCE_REVIEW.md) documents the additional design, motion, game, sound, and engineering sources reviewed on 2026-10-26, including material excluded from redistribution.

Browse the [external material catalogues](SOURCE_CATALOGUE.md) for per-skill source links, local paths, uses, licenses, and explicit `"Unknown"` provenance fields.
