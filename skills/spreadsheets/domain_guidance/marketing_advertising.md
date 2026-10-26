# Campaign and acquisition workbooks

Before calculating a marketing result, identify the observation unit: an impression, click, lead, attributed conversion, order, or account. Record the source platform, extraction date, timezone, reporting window, and attribution definition supplied with the data. Two platforms can use the same metric label for different events.

Preserve the imported extract. Put any deduplication, exclusion, or category mapping into a documented transformation, so a reviewer can reproduce the reported population. A deduplication key should come from the data contract; a repeated campaign name is not necessarily a duplicate record.

Compute rates from their components. For example, a combined click-through measure requires the summed clicks and eligible impressions for the same population and period. Do not average campaign percentages when the denominators differ. Keep costs, revenue, currencies, and conversion windows aligned before deriving a cost or return measure.

Compare like periods and definitions. If a platform changed its attribution window or an extract is incomplete, explain that discontinuity alongside the chart. Use source-supplied targets and their direction of improvement; do not invent success thresholds to populate status colours.

Tie stakeholder summaries to the calculation cells and retain the underlying detail. See [charts](../features/charts.md) for range and visual checks, and [local.md](../local.md) for formula verification. A read-only investigation uses [the inspection workflow](../references/read_only_qna.md).

New domain guidance built on the permitted data/calculation/presentation separation in Design Office Artifacts. See [SOURCES.md](../SOURCES.md).
