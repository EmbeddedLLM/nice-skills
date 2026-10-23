# Page geometry and section boundaries

Use a section when page size, orientation, margins, columns, or running furniture must change. First inspect the existing boundaries: a wide exhibit may already have the section needed. Preserve the approved template's geometry and header/footer relationships unless the requested edit requires changing them. The document design guidance behind this approach is recorded in [Sources and notices](../SOURCES.md).

```sh
python scripts/section_audit.py report.docx
```

The audit requires the skill's Python dependencies. Record section order, page dimensions, break type, margins, and header/footer linkage before editing. The final `w:sectPr` belongs at the end of the body; earlier section properties commonly belong to the terminating paragraph of that section. Moving or deleting that paragraph can change the layout of preceding content.

## A new wide exhibit

For a new document where `python-docx` preserves all needed features, create a new-page section and set both orientation and actual dimensions. For example:

```python
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.shared import Mm

report = Document()
report.add_paragraph("Introduction")
exhibit = report.add_section(WD_SECTION.NEW_PAGE)
exhibit.orientation = WD_ORIENT.LANDSCAPE
exhibit.page_width = Mm(297)
exhibit.page_height = Mm(210)
report.add_paragraph("Wide exhibit")
report.save("exhibit.docx")
```

Add a subsequent portrait section if ordinary pages follow the exhibit. Set dimensions deliberately from the template or regional requirement; the example uses A4 and is not a universal default. A direction flag alone does not set the page's physical width and height.

## Running furniture and review

Headers and footers may inherit from a previous section. Break the relevant `is_linked_to_previous` relationship before giving a section independent content. Inspect first-page and odd/even variants separately; a normal header can look correct while the first page remains wrong. Confirm page-number continuation or restart explicitly.

Render all section transitions and inspect blank pages, margin changes, heading placement, wide tables, and numbering. Native editor pagination can differ from the local renderer. For mixed dimensions, pass an explicit `--dpi` to `render_docx.py` when consistent resolution matters; its automatic resolution uses the first section. Record the renderer and any unverified target-editor behavior.
