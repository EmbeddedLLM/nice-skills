# Explain a workbook without changing it

Treat a question about an existing workbook as an inspection task. Open read-only views when supported, retain formula expressions alongside available cached results, and leave the file unchanged. Do not refresh connections or run a save/recalculation cycle simply to answer a question.

Locate the requested figure by its labels and reporting period. Trace its formula through intermediate cells to the actual inputs, noting missing external workbooks or unsupported calculations. Cite sheet names and cell ranges so the user can check the explanation. An output's displayed rounding may differ from the value used in a calculation.

For “why did this change?”, compare the relevant input and formula versions. Separate a data change from a changed formula or reporting definition. If only one version is supplied, explain what can be established without inventing a history.

If caches are absent or their freshness is unknown, distinguish the formula's intended calculation from a verified current result. Offer the findings that can be supported and identify the missing evidence. Only disclose the data needed for the authorized question.

This workflow follows the preservation boundary in the approved Design Office Artifacts reference; provenance is in [SOURCES.md](../SOURCES.md).
