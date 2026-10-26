# Sources and notices

## Upstream source

| Field | Value |
| --- | --- |
| Project | security-audit-skill |
| Publisher | Cloudflare, Inc. |
| Repository | [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) |
| Exact snapshot | [`c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`](https://github.com/cloudflare/security-audit-skill/tree/c1c8a8c1471069fb0e188eeaff69b8e8db6564a8) |
| Retrieved | 2026-10-22 |
| Licence | MIT, copyright 2025-2026 Cloudflare, Inc.; full text in [LICENSE.txt](LICENSE.txt) |
| Announced in | [Build your own vulnerability harness](https://blog.cloudflare.com/build-your-own-vulnerability-harness) |

The upstream `skills/security-audit/` package is redistributed here with its MIT notice intact. The prose, schema, validators, and validator tests are upstream material; no upstream runtime dependency, account, or service is required.

## Local changes

- Expanded remediation guidance with YAGNI, reuse, preservation requirements, user buy-in for speculative hardening, and root-cause regression checks; the evidence bar and full-audit verification requirements remain intact.
- Moved the fourteen companion guides into `references/` and the schema plus two validators into `scripts/`, so the package follows this repository's layout. Every cross-document link and every validator invocation was rewritten for the new paths.
- Moved the two validator test files into `tests/` and repointed their `require` targets at `scripts/`.
- Added the `license` frontmatter field, a Node.js prerequisite note, and this notice.
- Omitted the upstream repository `README.md`. It duplicates the entry point's purpose statement and documents a copy-into-a-config-directory installation that does not apply to this catalog.

Test fixtures are synthetic. Validator tests build temporary documents in the system temp directory and make no network calls.

## Excluded material

The upstream repository contains no third-party assets beyond the MIT-licensed documentation and JavaScript. Ledger and findings sample content in the test files is synthetic fixture data, not audit output from a real target.
