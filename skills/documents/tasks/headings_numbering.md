# Task: heading hierarchy and multilevel numbering

## Goal

Documents whose outline is real: consistent, readable, and usable as the basis of a table of contents.

## Principles

1. **Style the paragraph, do not format the run.** `p.style = doc.styles["Heading 1"]` gives you an outline entry. Making text 16pt bold inside a Normal paragraph gives you something that looks like a heading and behaves like nothing.
2. **Do not skip levels.** Heading 1 straight to Heading 3 is only correct when the document genuinely has no level between them.
3. **Numbered headings are not bullet lists.** Word's multilevel numbering comes from numbering definitions in the template. Start from a DOTX that already has them; generating numbering from scratch is brittle and rarely round-trips.

## python-docx patterns

Applying heading styles:

```python
from docx import Document

doc = Document()
doc.add_paragraph("Executive Summary", style="Heading 1")
doc.add_paragraph("Background", style="Heading 2")
doc.add_paragraph("Prior Work", style="Heading 3")
doc.save("out.docx")
```

When typography has to change, change the style definition in the template rather than touching each paragraph — one edit instead of two hundred, and future paragraphs inherit it.

## Checking the structure

```bash
python scripts/heading_audit.py work/report.docx
```

`--max_findings` caps how many are printed (default 20).

## What to look for in the rendered pages

- heading sizes and weights consistent throughout;
- spacing above and below headings consistent;
- indentation consistent, especially on numbered headings;
- no "fake headings" — large bold Normal text standing in for a section;
- the TOC, if there is one, mirrors the actual hierarchy.

## Common pitfalls

- Manual numbers typed into the text ("1. ") mixed with generated numbering.
- Normal paragraphs dressed up with bold and size instead of Heading styles.
- Two documents in the same set disagreeing about what Heading 1 looks like — solve that with a shared template, not with per-file edits.
