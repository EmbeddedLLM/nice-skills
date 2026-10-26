# Task: insert and maintain a table of contents

## Goal

A TOC that populates, and stays correct after the document is edited.

## The thing that surprises everyone

A TOC is a **field**. Word does not recompute it when your script writes the file, and neither does LibreOffice during a headless export. Until fields are refreshed, the contents page shows whatever was cached when the file was last saved in an editor.

## Headless alternative: a static TOC

For a fully automated flow where no field refresh is available, generate a static contents section with internal links instead:

```bash
python scripts/internal_nav.py work/report.docx --out work/with_static_toc.docx
```

That builds the contents list plus TOC → heading and heading → Back to TOC links without depending on Word. Details in `tasks/navigation_internal_links.md`.

## Requirements for a field-based TOC

1. Headings use `Heading 1/2/3` styles. Bold, larger Normal text is invisible to the TOC.
2. Heading text lives in the paragraph itself — avoid leading numbers typed as plain text.
3. Fields are updated after edits and before final export.

## Inserting at a placeholder

**1.** Add one paragraph containing the token:

```
[[TOC]]
```

**2.** Run the inserter:

```bash
python scripts/insert_toc.py work/report.docx --out work/with_toc.docx
```

It covers Heading 1–3 by default; `--levels "1-2"` narrows that, and `--placeholder` changes the token. Omitting `--out` edits in place.

**3.** Open the result in Word and update fields: `Ctrl+A`, then `F9`, then save.

**4.** Render and read it:

```bash
python render_docx.py work/with_toc.docx --output_dir work/out
```

## TOC review checklist

- the contents section is not blank;
- indentation follows heading level;
- the page numbers match where the headings actually are;
- every heading that should be listed is listed, and nothing else is;
- no authoring placeholders survive, such as "TOC will populate…".

## Why TOCs go wrong

| Symptom                        | Cause                                  |
| ------------------------------ | -------------------------------------- |
| Empty contents                 | headings are not styled as headings    |
| Levels or indentation drift    | manual numbering and direct formatting |
| Stale entries and page numbers | fields never updated after editing     |

When heading styles are the suspect, run `scripts/heading_audit.py`.
