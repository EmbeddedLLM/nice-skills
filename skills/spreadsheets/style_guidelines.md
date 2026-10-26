# Style and formatting

Precedence: user instructions, then intentional templates/references, then domain guidance. Defaults apply only to new sheets or authorized restyling.

Render before editing. Unrelated content, layout, formatting, and native features stay as they are; a values-only edit changes no formatting.

## Tab structure defaults

- Follow [Workbook structure](SKILL.md#workbook-structure). Roles do not force separate tabs: simple workbooks stay basic, and mixed-use tabs get role styling by section.
- Primary outputs and the assumptions control panel stay easy to find: a dark brand-color tab for outputs, one level lighter for Assumptions, and light tan for standalone Finance Actuals tabs. Intentional user/reference colors are preserved.
- A complex workbook with several source/internal tabs trailing the working views gets a divider before that group; focused tasks get none. Pick a plain group name like `Data >>`, `Internal >>`, or `Inputs >>`. The divider takes a color and its children stay uncolored, overriding individual role colors. A `ReadMe` tab always gets a distinct muted color, divider group or not. Other tabs stay uncolored unless color aids navigation.

## Reader-facing sheets

New reader-facing sheets (or authorized restyles) open with a compact, presentation-style view: a concise unfilled title, modest whitespace, and the main results — a table, a chart, or both, whichever suits the task. Covers instead follow the simple front-page guidance in [Workbook structure](SKILL.md#workbook-structure).

A filled Cover starts from a bounded area such as `A1:Z100`, adjusted to the intended opening view; the background never covers the entire worksheet or whole rows/columns.

- Lead with one blank top row, then the concise unfilled left-aligned title, a thin rule, and compact spacing before the main content. Include essential context — a subtitle or takeaway is not mandatory. No large filled title banners. Raw source tables get no presentation blank rows, and a supplied layout is never overridden.
- Remove filler. Useful table commentary goes in ordinary `Notes` or `Comments` cells to the right — at least one blank spacer column away, outside the table header fill and borders, wrapping off. Widen or shorten notes without inflating table row heights; longer explanations get their own notes area on the same sheet. Notes stay readable and unclipped. No setup or footer blocks. Essential units and specific warnings sit beside the affected result. Sources and annotations follow [Citations](SKILL.md#citations). These are ordinary cells — not Excel Comments or Notes.
- Summary/KPI cards appear only when they clarify the requested decision; never duplicate a small table or build oversized cards.
- Cards, tables, and charts are chosen for the task; keep useful trends and comparisons rather than defaulting every summary to a table. An analytical Summary uses its width: a compact table beside a useful chart, monthly detail below, when the content fits that. Never stretch it into a tall page of prose or shrink fonts to force a layout.

## Visually clear layout

- Headers, inputs, calculations, and notes read as distinct, consistently. Default to dark body text and restrained fills — not a universal teal theme. Domain styling defaults (finance input/formula/source colors, dynamic statuses) are preserved.
- Wherever cases are used (Finance or elsewhere), every output and build tab shows `Case Selected:` with the linked case value (e.g. `Base`) prominently near the top — horizontally and vertically centered in a restrained dashed or dotted outline, close to the content. Keep one editable selector, and distinguish the active case from actuals and named comparison cases. On Assumptions, the selector (or its linked value) and only essential global inputs sit directly above the driver table; each driver's Active Selection row is emphasized over its case inputs. A short case-number key appears only for numeric selectors. No unused Owner columns or setup sections; meaningful existing owners are preserved.
- Purely technical helper rows (period keys, say) live above the model, italicized and grouped/collapsed where supported — inspectable, but out of business headers and chart labels. Useful business calculation steps are not hidden as helpers.
- Output tabs keep row heights consistent within each table and vertical padding modest. Excessive spacing tightens, and oversized heights after autofit come down, while tables must survive being copied into slides or printed to PDF. Rows fit the font and content: expand only rows whose wrapped table content needs it, never the whole table, and never shrink fonts to tighten spacing. Off-table commentary is excluded from table-row autofit. Input tabs may use smaller fitted rows; working builds stay compact. Mixed-use tabs get these distinctions by section. Only populated or intentionally reserved ranges are formatted.
- Working titles, headers, and input/calculation areas stay unmerged. Presentation merges require user or template intent; merges never overwrite content or combine distinct table columns. In reader-facing tables, column headers center horizontally and vertically. One heading spanning several otherwise-empty header cells uses Center Across Selection where supported — or the layout simplifies to one header cell; treat the span as a single header group with no internal borders or blank outlined header boxes, and never center across distinct headings or populated cells. Working builds may keep useful blank column headers and genuine spacer columns.
- Yellow/amber marks inputs needing updates. Editable-input cues stay distinct from calculated warnings, with a compact legend when needed. Documented exception styles cover overrides, special formulas, and one-offs.
- Dark column headers: white text with thin white separators between actual headings, dates included.
- Section bands: one continuous fill and a single outside outline, no internal borders, gutters excluded. Genuine spacer columns between separate tables or sections stay blank and unfilled, header cells included.
- If a sheet has a leading gutter, titles, sections, and tables align to the same content edge, and the gutter stays empty except specified navigation markers. Finance gutter defaults apply to financial models only; operational trackers are not forced into them.
- Structural borders stay thin and light, section breaks stronger, and there is no full body-cell grid — never border every filled cell.
- New sheets hide worksheet gridlines by default, inputs, builds, and outputs included. An intentional user/reference setting is preserved, and unrelated edits never touch gridlines. Gridline visibility is separate from selective structural borders.
- Needed context goes in separate cells or ordinary punctuation. Meaningful financial/mathematical labels and symbols, required source quotes, intentional reference conventions, and expressly specified plain `x` navigation markers are preserved.
- Status, risk, variance, and exception cues that must react to edits use bounded conditional formatting. Reuse the workbook's existing rules rather than inventing business logic for color. Emphasize affected missing/invalid inputs and failed checks — light-red fill with bold red text for critical errors, say — while valid check values stay neutral. Static error paint and decorative PASS fills are not substitutes.

## Freeze panes

- Tables that scroll vertically freeze their header rows. When horizontal scrolling would hide identifying columns, freeze those too. Use the smallest useful frozen area and leave room to read and work.
- Content is never moved and no tabs are added to accommodate freezing. Existing panes survive unrelated edits.
- Compact summary, dashboard, and cover sheets are not frozen unless scrolling genuinely requires the shared headers or row labels.

## Align and format by data type

- Text left-aligns, numbers right-align, column headers center horizontally. Populated and intentionally reserved ranges default to middle vertical alignment; wrapped descriptions may top-align where helpful.
- Numbers and dates stay typed, with explicit appropriate formats and clear units. Widths and heights adjust so the final formatted content fits — signs, parentheses, and units included; values are never stringified for appearance.
- Brief context/scope/unit notes are italicized — headers, controls, statuses, and warnings are not.

## Typography — intentional and conservative

- One font, verified in both the generating and target environments: Helvetica Neue → Helvetica → Arial → Aptos. One family across cells, charts, and theme fonts, with consistent body sizing throughout the workbook.
- Standard non-cover sheets default to two font sizes, three at most, kept consistent for matching elements. Dashboard and visual sheets may add sizes selectively and modestly.
- The largest size stays within 6 pt of the body size unless the user or reference specifies otherwise; hierarchy comes from spacing and restrained fills.
- Defaults: 10pt body/table headers, 14pt titles, 16pt ceiling.
- Table headers and content generally share the chosen body size.
- Bold and italics are spent sparingly — totals, or domain styling defaults.

## Live inputs and visuals

- Dependent values, charts, and status text all drive from editable cells. Use categorical validation where feasible plus the dynamic-state formatting above. Invalid or missing inputs never masquerade as plausible zeros or success states.
- Summaries are compact and formula-linked; required outputs are preserved without redundant tables or oversized KPI cards. Inline bars need an explicit request. Charts follow `features/charts.md`.
