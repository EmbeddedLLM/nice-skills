# Financial model reasoning

Use this guide to establish what a model calculates. For presentation choices, see [the model layout guide](../templates/financial_models.md). The user's accounting definitions and supplied workbook determine the calculation contract.

## Write the contract before extending the forecast

Identify the output the user needs, the reporting currency, scale, fiscal calendar, and distinction between recorded periods and estimates. Inventory the source tables and existing reconciliation cells. Resolve conflicting definitions before combining extracts; record an unsupported assumption explicitly instead of treating it as an observed input.

Describe each schedule as a small equation with its timing rules. For example, a subscription forecast can derive revenue from billable accounts and a monthly price, but it also needs a rule for the first and last billing month. That rule cannot be recovered from an annual total alone. Keep quantities, rates, and timing assumptions independently adjustable where the task calls for scenarios.

## Model flows and balances deliberately

A period's activity and a balance at a particular date have different meanings. Specify opening balance, movements, and closing balance for cash, debt, assets, or customer counts. Reconcile the last balance to the next opening period. Calculate ratios from the appropriate numerator and denominator rather than averaging displayed percentages.

Use recorded transactions for historical periods. Put changes to future assumptions in the forecast portion, and keep one-time events distinguishable from continuing costs. Extending a timeline must update references, labels, chart ranges, and assumptions together; changing just the column headings relabels old results.

For a valuation or return calculation, state the timing convention and which cash flows belong to the chosen measure. Keep financing, tax, and operating assumptions visible. Do not select discount rates or investment conclusions merely to fill a template; use the task's supported assumptions and identify gaps.

## Challenge the result

Verify at least one representative period independently, then test boundary cases: a zero denominator, a deliberately zero input, a missing source record, and the first forecast period. Reconcile totals using independent source controls where available. A balancing adjustment needs an explanation and source; a formula that forces a difference to zero does not test the model.

When comparing cases, hold the period and calculation definition constant. Explain whether a positive variance is beneficial for the particular measure. Label the reason for an unavailable percentage rather than displaying a misleading zero.

Keep formulas in the delivered workbook and follow [local recalculation](../local.md#recalculate-and-verify). Report unsupported functions, stale caches, or incomplete source controls separately from a numerical failure.

This replacement guide uses the permitted workbook-preservation and calculation principles recorded in [SOURCES.md](../SOURCES.md). Domain examples and the organization above are new repository work.
