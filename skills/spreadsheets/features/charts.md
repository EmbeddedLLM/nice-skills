# Data-backed workbook charts

Design a chart around the question and the reader's next comparison. Use native charts linked to cells when future data edits are required. A static export can be useful for a report, but it must not replace a requested editable chart.

## Choose a visual encoding

| Reader's question                    | Useful starting point            | Check before delivery                      |
| ------------------------------------ | -------------------------------- | ------------------------------------------ |
| Which category is larger?            | Bars or dots                     | Comparable units and a meaningful baseline |
| How does a measure change over time? | A line with an ordered date axis | Missing periods and irregular sampling     |
| Are two measurements associated?     | Scatterplot                      | Observation pairing and axis scale         |
| What is the distribution?            | Histogram or a summary table     | Bin definitions and excluded observations  |
| What exact numbers should I use?     | A compact table                  | Precision, units, and rounding             |

These are choices, not quotas. Use fewer visuals when a table answers the question better.

## Keep the evidence attached

Select the source range deliberately. Verify that category labels and each series cover the same observations. Give derived chart inputs traceable formulas or documented transformations. State the reporting window, units, aggregation, and treatment of missing or filtered rows. Missing measurements must not become zero-valued observations merely to produce an unbroken line.

When adding periods or rows, check the chart's range after saving. A chart that looked correct before expansion may still point at the old table. Verify series names, totals, and plotted boundary values against the worksheet.

## Make the saved chart readable

Keep series meanings and colours consistent between related charts, pairing colour with labels where necessary. Place titles, units, and explanatory notes where they remain legible at the final size. Use axis limits that support an honest comparison; disclose any deliberate truncation. Avoid decorative depth and unnecessary axes that obscure magnitude.

Leave room for long labels and legends. Inspect the workbook in the target viewer or a compatible renderer, including print output when requested. Native chart structure establishes editability only to the extent tested; it does not guarantee identical appearance across spreadsheet applications.

Adapted from Design Office Artifacts' chart and workbook guidance; see [SOURCES.md](../SOURCES.md) for the selected permissive sources and retained notices.
