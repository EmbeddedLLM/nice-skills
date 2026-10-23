# Finalizing a document under review

Accepting and rejecting revisions produce different documents. Establish which decision the user has authorized and whether it applies to every revision or only selected passages. Preserve the original redline and reviewer metadata. Do not treat removal of visible markup as permission to resolve comments or accept contractual language.

## Inventory and route selection

Run the local report before changing anything:

```sh
python scripts/accept_tracked_changes.py review.docx --mode report
```

The helper requires Python and `lxml`. Inspect its supported revision constructs against the actual package, including headers, footers, notes, tables, moves, and property changes. A zero count for supported wrappers does not establish that every kind of Word revision has disappeared. For complex review histories, prefer a compatible editor's native accept/reject operation and save a separate result.

For a supported whole-document decision:

```sh
python scripts/accept_tracked_changes.py review.docx --mode accept --out final.docx
python scripts/accept_tracked_changes.py review.docx --mode reject --out baseline.docx
```

Choose one command according to the authorized outcome. The output argument is mandatory. Unless `--keep_tracking_on` is supplied, the helper disables future revision recording. That setting is distinct from resolving the revisions already present. See [tracked-change XML notes](../ooxml/tracked_changes.md) for the underlying structure.

## Verification

Compare the resulting text with the intended accepted or rejected reading, including spaces at edit boundaries, moved passages, lists, tables, and footnotes. Repeat the revision report against the output and inspect any unsupported constructs. Comments have a separate lifecycle; retain them unless their removal is requested.

Render the saved document using [the verification workflow](verify_render.md). Review page flow, running headers, and every changed passage. Preserve the difference between structural checks, text comparisons, and visual evidence, as emphasized in [Sources and notices](../SOURCES.md). If the target editor or renderer is unavailable, identify what remains unverified rather than claiming a clean final document solely from the XML count.
