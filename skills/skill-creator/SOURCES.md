# Sources and notices

This package reimplements the entry-point workflow from the user-supplied repository snapshots `skill-creator`. Supporting tools and selected references were retained where useful; their provenance is the supplied snapshot, not a new upstream retrieval. The installed package is self-contained and does not read the original snapshots.

Preserved notices: [LICENSE.anthropic.txt](LICENSE.anthropic.txt), [LICENSE.openai.txt](LICENSE.openai.txt). Adapted third-party material retains those terms; new repository contributions follow the repository MIT license.

## Retained licensed helpers

Issue 6 separately identified `scripts/init_skill.py` and `scripts/quick_validate.py` as licensed carry-over. These remain under the retained Apache-2.0 terms rather than being relabeled MIT. Both files now carry prominent modification notices: the initializer uses the portable repository scaffold and omits provider-specific UI output; the validator checks repository metadata, directory names, and unfinished placeholders. The supplied license texts and their attribution are unchanged. No additional upstream NOTICE file was present in the supplied skill-creator snapshot.

These two helpers are intentionally outside the 62-file replacement gate. A similarity match for retained, attributed source is expected and is not evidence that it should be rewritten.
