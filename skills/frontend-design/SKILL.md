---
name: frontend-design
description: Design and implement websites, application interfaces, and portable interactive HTML artifacts with responsive layouts and usable interaction states. Use for new UI, substantial redesigns, or a shareable HTML deliverable.
license: Apache-2.0; see LICENSE.txt and SOURCES.md
---

# Frontend design

Build the requested interface in the project's existing stack, or use plain HTML/CSS/JavaScript for a small standalone artifact. Source editing and a local browser suffice; paid design tools, generation APIs, hosting, and external fonts are optional.

## Keep implementation proportional

Before a substantial change, separate the required user experience from the proposed implementation and identify existing behavior, content, and state to preserve. Apply YAGNI: add only features and infrastructure needed for this interface. Reuse project components first, then standard-library or native HTML/CSS/browser capabilities, then installed dependencies before adding a library. Resolve uncertain browser behavior with a focused experiment or matching documentation; a new framework, backend, state layer, or generic component system needs evidence that the simpler route is insufficient.

Keep edits focused and fix root causes. Derive checks from the user flow and preservation requirements. After the interface works, remove unused state, duplicated logic, speculative options, and abstractions that only move complexity. Preserve accessibility and the requested visual richness; discuss trade-offs before simplifying away required behavior.

Before adding complexity for a speculative or vanishingly unlikely race or security edge case, explain the concrete failure mode, evidence for its likelihood (or uncertainty), implementation and maintenance cost, and simpler alternative. Get user buy-in for that scope expansion unless existing approval already covers the trade-off. Do not silently add theoretical robustness, weaken required controls, or delay an already-authorized fix for a demonstrated defect.

## Establish direction and build

1. Inspect the project, content, audience, primary action, and supplied design system. Preserve established components during narrow edits. Ask only about missing choices that change the product.
2. Make a compact design plan: hierarchy and layout, named color roles, available heading/body fonts, type scale, and one subject-specific visual decision. A dashboard should prioritize its task; a landing page should communicate its actual subject. **Let the layout do the explaining:** remove secondary labels, kickers, helper sentences, and captions that only restate a heading, and carry that meaning through hierarchy, grouping, scale, and position instead. Order the content so the structure is legible without labels.
3. Use semantic controls, consistent tokens, clear focus, responsive reflow, and readable line lengths. Prefer supplied assets or local SVG/CSS illustrations. Do not require paid imagery to complete the interface.
4. Implement action labels and loading, empty, success, and error states as part of behavior. Label illustrative data. Keep important content available without hover or animation and respect reduced motion.
5. For a single-file or offline deliverable, read [portable HTML](references/portable-html.md). Keep this as an output mode of the same interface workflow.

## Optional Openverse imagery

When a page benefits from photographs or illustrations, use the free anonymous [Openverse image API](https://api.openverse.org/v1/) through an available HTTP tool with permitted network access. Example:

```text
GET https://api.openverse.org/v1/images/?q=mountains&license=cc0,pdm,by&page_size=5&mature=false
```

Search public subject terms and inspect response warnings. Verify candidates' licenses, creators, and notices at their original source pages; [Openverse does not guarantee that metadata](https://docs.openverse.org/api/reference/made_with_ov.html). Keep the default license selection unless the intended use supports other restrictions.

Download suitable originals into the project's asset directory and optimize local copies for actual display sizes. Record title, creator, source URL, license/version/link, and modifications in the asset manifest and an appropriate user-accessible credit surface. Preserve notices in exported HTML too. Use descriptive alt text, or empty alt text for decorative images. Do not present stock images as the user's real team, products, or customer evidence.

Keep search calls out of page startup and runtime; bundle local assets for offline export. Respect source-host terms, rate limits, and retry guidance on 429 without catalog scraping. If access or verification fails, use supplied assets or local SVG/CSS and disclose any unmet requirement. No account, API secret, or paid provider is required.

## Review the result

Run the actual app or exported file. At desktop and narrow mobile widths, inspect clipping, contrast, fonts, missing images, and console errors. Exercise the primary flow, input validation, keyboard interaction, and relevant failure states. Use the project's tests or local browser automation when available; report any browser review that could not run.

Deliver the working source or requested HTML and explain material runtime requirements. Do not publish or create an account just to validate a local interface. If the project requires unavailable backend access, distinguish verified local behavior from that integration.

Example: “Build an offline loan-payment calculator as one HTML file.” Use local controls and calculations, show input errors, test representative results independently, and open the exported file with network disabled. No framework or financial API is necessary.
