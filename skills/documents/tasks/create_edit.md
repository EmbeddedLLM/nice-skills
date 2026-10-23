# Task: create or edit a DOCX

## Default tool

Reach for `python-docx` first. It covers paragraphs and runs, the built-in styles (`Title`, `Heading 1`, `Heading 2`, …), tables including cell text and basic formatting, and straightforward headers, footers, and margins.

## Gotchas worth knowing before you hit them

### Tables in headers and footers need an explicit width

`add_table` will not infer one there:

```python
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches

footer = doc.sections[0].footer
grid = footer.add_table(rows=1, cols=3, width=Inches(6.5))
grid.rows[0].cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
```

### Setting a font may take two places

Some Word builds and renderers ignore `run.font.name` on its own. Write the `w:rFonts` attributes as well:

```python
from docx.oxml.ns import qn

run.font.name = "Gill Sans"
rfonts = run._element.rPr.rFonts
rfonts.set(qn("w:ascii"), "Gill Sans")
rfonts.set(qn("w:hAnsi"), "Gill Sans")
```

### There is no `clear()` on a header paragraph

To replace existing header content, remove its runs or swap the paragraph element. Do not assume a convenience method exists.

### Tracked changes and comments are outside the library

Neither is first-class in `python-docx`. If the user asks for genuine redlines or genuine Word comments, budget for OOXML patching — see `ooxml/`.

## Render after every batch of edits

Do not accumulate a long editing session and check at the end. Run the loop in `tasks/verify_render.md` (DOCX → PNG) after each meaningful batch; that is how layout defects get caught while they are still cheap to fix. The renderer goes through a PDF step internally, and `--emit_pdf` keeps it if you want it.

## Keeping the workspace tidy

`work` is for deliverables. Leave render output and scratch files out of it unless the user asked for those artifacts.
