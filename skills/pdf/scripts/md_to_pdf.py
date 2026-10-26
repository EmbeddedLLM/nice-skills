#!/usr/bin/env python3
"""Markdown-to-PDF through Pandoc.

A productive document pipeline with citations, math, and templates.
LaTeX-heavy documents are often better written as LaTeX directly (see
latex_to_pdf.py).

Examples:
  python md_to_pdf.py report.md --output report.pdf
  python md_to_pdf.py report.md -o report.pdf --template template.tex
  python md_to_pdf.py report.md -o report.pdf --pdf_engine lualatex

Tip: `--resource_path` makes relative image paths resolve.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

CLI_SPEC = [
    (["input_md"], {}, "Markdown source file"),
    (["-o", "--output"], {"required": True}, "where the PDF is written"),
    (["--pdf_engine"], {"default": "xelatex"}, "Pandoc PDF engine"),
    (["--template"], {}, "Pandoc template file"),
    (["--resource_path"], {}, "search path for relative resources"),
    (["--extra"], {"action": "append", "default": []},
     "extra pandoc argument (repeatable)"),
]


def build_command(args, source: Path, destination: Path) -> list[str]:
    return [
        "pandoc",
        str(source),
        "-o",
        str(destination),
        "--pdf-engine",
        args.pdf_engine,
        "--resource-path",
        args.resource_path or str(source.parent),
        *(["--template", args.template] if args.template else []),
        *args.extra,
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for flags, options, help_text in CLI_SPEC:
        parser.add_argument(*flags, **options, help=help_text)
    args = parser.parse_args()

    if shutil.which("pandoc") is None:
        raise SystemExit(
            "pandoc not found. Install pandoc, or use another pipeline "
            "(ReportLab, HTML->PDF, ...)."
        )

    source = Path(args.input_md)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = build_command(args, source, destination)
    print(" ".join(command))
    subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
