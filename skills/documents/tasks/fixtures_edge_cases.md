# Task: repro fixtures for edge cases

## Goal

Small, deterministic `.docx` files that exercise the OOXML patterns which are awkward to produce by hand, so helper scripts can be tested without anyone editing XML in a text editor.

## Why bother

Tracked changes and watermarks cause a disproportionate share of "this looks wrong" reports, and building either by hand is slow and easy to get subtly wrong. A standard fixture turns a smoke test into two commands and gives future debugging a known starting point.

## Generating them

`scripts/make_fixtures.py` writes into `--outdir`: both fixtures by default, or one of them via `--only tracked` / `--only watermark`.

```bash
python scripts/make_fixtures.py --outdir fixtures
```

| Fixture                        | Contains                                                        |
| ------------------------------ | --------------------------------------------------------------- |
| `tracked_changes_fixture.docx` | body text with `w:ins` / `w:del` revisions and tracking enabled |
| `watermark_fixture.docx`       | a header carrying watermark-like VML whose text reads `DRAFT`   |

## Exercising the tracked-changes fixture

Report first, so there is a revision count to compare against, then accept into a new file and render it.

```bash
python scripts/accept_tracked_changes.py fixtures/tracked_changes_fixture.docx --mode report
python scripts/accept_tracked_changes.py fixtures/tracked_changes_fixture.docx --mode accept --out accepted.docx
python render_docx.py accepted.docx --output_dir out_accepted
```

Passing means: the report counted revisions in the fixture, a second report against `accepted.docx` counts none, and the rendered pages show no redline markup.

## Exercising the watermark fixture

Report, remove by matching the watermark's own text, then diff the two renders to see precisely what disappeared.

```bash
python scripts/watermark_audit_remove.py fixtures/watermark_fixture.docx --mode report
python scripts/watermark_audit_remove.py fixtures/watermark_fixture.docx --mode remove --contains DRAFT --out no_watermark.docx
python scripts/render_and_diff.py fixtures/watermark_fixture.docx no_watermark.docx --outdir diff_watermark
```

Passing means: the first report finds the VML shape, a report against `no_watermark.docx` finds nothing, and the rest of the header — logos, rules, text — is untouched in the diff.

## Keeping fixtures useful

Regenerate rather than edit them. A fixture that someone patched by hand stops being deterministic, and the point of the pair is that the next person can trust it.
