#!/usr/bin/env python3
"""Compile LaTeX to PDF with latexmk (multi-pass as needed).

Examples:
  python latex_to_pdf.py main.tex --out_dir work/out
  python latex_to_pdf.py main.tex --out_dir work/out --engine xelatex
  python latex_to_pdf.py main.tex -o work/out.pdf --engine xelatex

For a one-shot compile, call pdflatex directly instead.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

ENGINES = ("pdflatex", "xelatex", "lualatex")


def compile_tex(tex: Path, build_dir: Path, engine: str) -> Path:
    command = [
        "latexmk",
        "-pdf",
        f"-pdflatex={engine} %O %S",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-outdir={build_dir}",
        str(tex),
    ]
    proc = subprocess.run(command, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
    built = build_dir / f"{tex.stem}.pdf"
    if not built.exists():
        raise SystemExit(f"Expected output not found: {built}")
    return built


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tex", help="Path to a .tex file")
    # --out_dir drops <stem>.pdf in that directory; -o/--output is an exact
    # path (compiled in a temp build dir, then copied over).
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out_dir", help="Output directory (writes <stem>.pdf)")
    target.add_argument("-o", "--output", help="Exact output PDF path")
    parser.add_argument("--engine", default="pdflatex", choices=list(ENGINES),
                        help="LaTeX engine")
    parser.add_argument("--clean", action="store_true",
                        help="Clean auxiliary files after build")
    parser.add_argument("--keep_build", action="store_true",
                        help="Keep intermediate build directory when using -o/--output")
    args = parser.parse_args()

    if shutil.which("latexmk") is None:
        raise SystemExit("latexmk not found. Install texlive/latexmk or use another PDF pipeline.")

    tex_path = Path(args.tex)
    temp_build: Path | None = None
    final_path: Path | None = None
    if args.out_dir:
        build_dir = Path(args.out_dir)
        build_dir.mkdir(parents=True, exist_ok=True)
    else:
        final_path = Path(args.output)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        # Default: build artifacts stay out of the destination folder.
        build_dir = Path(tempfile.mkdtemp(prefix="latex_build_", dir=str(final_path.parent)))
        temp_build = build_dir

    built = compile_tex(tex_path, build_dir, args.engine)

    delivered = built
    if final_path is not None:
        shutil.copyfile(built, final_path)
        delivered = final_path

    if args.clean:
        subprocess.run(["latexmk", "-c", f"-outdir={build_dir}", str(tex_path)], check=False)
    if temp_build is not None and not args.keep_build:
        shutil.rmtree(temp_build, ignore_errors=True)

    print(str(delivered))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
