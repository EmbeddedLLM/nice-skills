# Task: compare two DOCX files

## What you get

One command produces a QA bundle that answers "did this edit change anything I did not intend?" — page images of both files, a visual diff for every page that moved, and a text-level unified diff:

```bash
python scripts/render_and_diff.py before.docx after.docx --outdir work/diff
```

The output directory holds:

| Path                         | Contents                                         |
| ---------------------------- | ------------------------------------------------ |
| `a_render/page-*.png`        | rendered pages of the first file                 |
| `b_render/page-*.png`        | rendered pages of the second                     |
| `diff_pages/diff-page-*.png` | one image per changed page                       |
| `text_a.txt`, `text_b.txt`   | extracted `w:t` text of each file                |
| `text_diff.txt`              | unified diff of those two extractions            |
| `summary.json`               | page counts and the list of changed page numbers |

Pages present in one file but not the other count as changed. `--render_py` points at a different renderer if you ever need one; the default is the `render_docx.py` beside this package.

## Reading the bundle

1. Compare `pages_a` and `pages_b` in `summary.json` against what you expected.
2. Open each page listed in `changed_pages` side by side at 100% zoom.
3. Confirm the highlighted regions are the edits you meant to make and nothing else.
4. If the change touched layout — tables, images, section breaks — also look at a few pages the tool reported as unchanged.

## Things that trip people up

- The comparison is between two _LibreOffice_ renders, which is not Word. It catches regressions in the pipeline you actually ship through, and that is the point; it is not a Word-fidelity oracle.
- A pagination shift marks every later page as changed. Read `text_diff.txt` to separate real content edits from reflow.
- Differences that are only anti-aliasing noise: render at a higher DPI and run the comparison again.
