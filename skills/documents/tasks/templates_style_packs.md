# Task: templates and style packs (DOTX)

## Goal

Apply a `.dotx` — or a template `.docx` — onto an existing report so the typography comes from a designed style pack instead of ad-hoc choices.

## What a template actually contributes

| Part                                       | Contents                                           |
| ------------------------------------------ | -------------------------------------------------- |
| `word/styles.xml`                          | style definitions                                  |
| `word/theme/theme1.xml`                    | colour scheme and font scheme                      |
| `word/fontTable.xml`, `word/numbering.xml` | optional: font declarations, numbering definitions |

Direct formatting on runs — manual bold, sizes, colours — sits _above_ all of that and will beat a style pack wherever it exists. That is the main reason a template application looks patchy.

## Steps

**1. Apply the template parts**

```bash
python scripts/apply_template_styles.py --template template.dotx --target report.docx --out report_styled.docx
```

All three arguments are required and the target is never modified in place.

**2. Render and review**

```bash
python render_docx.py report_styled.docx --output_dir out_styled
```

## Review checklist

- headings and body text are typographically consistent;
- spacing and margins are still acceptable;
- tables have not reflowed into something hard to read;
- any change in page count is acceptable to the reader.

## Pitfalls

- Restyling changes pagination. Expect it and say so.
- A report heavy in direct formatting should be normalized first — re-apply the paragraph styles (`Normal`, `Heading 1/2/3`) with `scripts/style_normalize.py`, then apply the template.
- Style ids that the target document defines itself can be overwritten by the template's versions. Check custom styles survive if the document depends on them.
