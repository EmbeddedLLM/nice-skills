# Export an authored document as PDF

Choose the converter according to the source format and the user's delivery requirements. Retain native source files when editing, formulas or comments matter; conversion creates a separate reading artifact. Check tools locally before running a route—none of the optional applications is assumed installed.

| Source | Local route | Additional prerequisites |
| --- | --- | --- |
| Office/OpenDocument | `python scripts/lo_convert_to_pdf.py report.docx --out_dir delivery` | LibreOffice and the source fonts |
| Browser document | `python scripts/html_to_pdf.py report.html -o delivery/report.pdf --format letter` | Playwright and Chromium; `requirements-browser.txt` |
| Markdown | `python scripts/md_to_pdf.py report.md -o delivery/report.pdf --pdf_engine xelatex` | Pandoc plus the requested PDF engine |
| TeX | `python scripts/latex_to_pdf.py report.tex -o delivery/report.pdf` | latexmk/TeX packages |

Commands run from this skill directory; source-relative assets must remain available. HTML may reference remote fonts/images and conversion can fetch them; use authorized local assets when network access is unavailable or inappropriate. A missing executable or unsupported source must be reported explicitly.

Before export, set page dimensions, margins and print behavior. Long tables need repeating headers and sensible row breaks; charts need readable labels at the final size. Export a representative dense page early to detect substitutions before producing the entire document.

After export, check that the PDF opens, has the expected page count and contains the requested content. Render all pages, then inspect headings, table boundaries, figures, links and non-Latin text. A successful converter exit is not evidence of layout fidelity. Describe differences from the native source and any untested target-viewer behavior.
