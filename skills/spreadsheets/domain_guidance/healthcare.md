# Clinical and administrative data workbooks

Determine whether the task is record handling, operational reporting, or a clinical calculation. A workbook's healthcare setting does not establish the meaning of its fields or authorize a change to care protocols. Obtain the supplied data dictionary and applicable calculation specification when the requested output depends on them.

Keep record identifiers, encounter identifiers, dates, codes, and units intact. Identify whether the reporting unit is a person, visit, admission, or service; otherwise a count can silently double-count the intended population. Preserve unknown, not collected, and zero as distinct states.

Apply corrections through the authorized workflow with a record of the prior value and reason. Use synthetic records for testing. Expose only the fields and level of detail required for the authorized deliverable; a summary does not ordinarily need individual identifiers.

Implement only supplied, applicable clinical definitions and thresholds. Label the version and context of a rule and verify its boundary cases. Do not infer a universal reference range or let a formatting preset determine a clinical flag. Report unavailable qualified or authoritative validation when a calculation could inform care.

For operational summaries, document the eligible population and time window next to the result. Check aggregate numerators and denominators against source controls. Make status meaning readable without relying on colour alone, and inspect any printed views used in the workflow.

Use [the local workbook workflow](../local.md) for preservation, recalculation, and cache limitations. This guide governs handling of the workbook; it is not a clinical protocol.

Original domain guidance informed by Design Office Artifacts' preservation and accessible presentation principles. Attribution is recorded in [SOURCES.md](../SOURCES.md).
