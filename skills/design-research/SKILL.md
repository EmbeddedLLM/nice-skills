---
name: design-research
description: Search offline UI style, palette, typography, chart, motion, usability, and framework guidance or propose a design system from a product brief. Use when concrete design options or stack-specific references are needed; preserve an established design system during ordinary UI edits.
license: MIT; see LICENSE.txt and SOURCES.md
---

# Offline UI design research

Use the bundled Python standard-library search against credited UI UX Pro Max catalogs. No package installation, account, browser, or network is needed. Resolve script paths from this skill directory.

1. Identify product, audience, user action, platform, and existing design constraints. Research a missing choice rather than re-theming a working product by habit.
2. Search a specific domain or the project's stack. Read the retrieved guidance and its applicability, not just the rank.
3. Compare a small set of coherent choices, preserve user constraints, and document the trade-off. Retrieval scores do not certify quality, accessibility, license rights, or compatibility with an installed framework version.
4. Apply only the relevant choices in the destination project, then verify in a browser or target platform.

```sh
python scripts/search.py "accessible analytics dashboard" --domain ux --max-results 3
python scripts/search.py "forms and validation" --stack react
python scripts/search.py "public library booking" --design-system -p "Library Booking"
```

Default commands print recommendations. Use `--help` for supported domains, stacks, and JSON output. `--persist` writes design documents; use it only for a requested saved system and a new output directory, then review before replacing an existing document. Do not run searches as part of an application's startup.

Font and icon catalogs contain metadata and links, not binaries. Verify the actual asset license before acquisition and retain notices. Stack/API guidance must match the project's installed version; consult primary documentation for uncertain behavior. If a search returns no useful result, state the gap and reason from the project's needs rather than forcing an unrelated match.

Example: "Give me three accessible typography and chart options for an operations dashboard." Search those domains independently, compare readability and data tasks, and distinguish suggestions from tested UI behavior. [SOURCES.md](SOURCES.md) records the pinned catalog and adaptation boundary.
