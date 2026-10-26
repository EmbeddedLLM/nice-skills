#!/usr/bin/env python3
"""Exercise local AcroForm filling, flattening and raster comparison.

Prepare the js/ dependencies before running; this smoke test never installs
packages. Generated PDFs, values.json and diff/summary.json stay in --workdir.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

SCRIPTS = Path(__file__).resolve().parent
JS_DIR = SCRIPTS.parent / "js"


def write_form_pdf(path):
    drawing = Canvas(str(path), pagesize=(612, 792))
    drawing.drawString(54, 740, "Synthetic registration")
    drawing.acroForm.textfield(name="name", x=72, y=650, width=240, height=20)
    drawing.acroForm.checkbox(name="agree", x=72, y=610, size=16)
    drawing.showPage()
    drawing.save()


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--workdir", type=Path, default=Path("work/_pdf_forms_smoke"))
    cli.add_argument("--dpi", type=int, default=200)
    options = cli.parse_args()
    options.workdir.mkdir(parents=True, exist_ok=True)
    source, target, mapping = (options.workdir / name for name in
                              ("form_in.pdf", "form_filled.pdf", "values.json"))
    write_form_pdf(source)
    mapping.write_text(json.dumps({"name": "Casey Example", "agree": True}), encoding="utf-8")
    subprocess.run(["node", str(JS_DIR / "fill_form.mjs"), str(source), str(mapping),
                    str(target), "--flatten"], check=True)
    filled = PdfReader(target)
    if filled.get_fields() or "Casey Example" not in filled.pages[0].extract_text():
        raise RuntimeError("Expected flattened field text and no remaining form fields")
    directory = options.workdir / "diff"
    subprocess.run([sys.executable, str(SCRIPTS / "compare_renders.py"), str(source),
                    str(target), "--out_dir", str(directory), "--dpi", str(options.dpi)], check=True)
    report = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    changed = report["changed_pages"]
    if changed != 1:
        raise RuntimeError("Expected the completed form to change one rendered page")
    print(f"[OK] forms smoke test passed. changed_pages={changed}")
    print(options.workdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
