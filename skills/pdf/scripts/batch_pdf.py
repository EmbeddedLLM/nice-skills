#!/usr/bin/env python3
"""Batch driver: run one PDF operation over a glob of inputs.

Intentionally thin — it glues the sibling scripts together with sane
output-directory conventions.

Examples:
  python batch_pdf.py render    --in_glob "work/in/**/*.pdf" \
      --out_root work/out_renders --dpi 200
  python batch_pdf.py inspect   --in_glob "work/in/**/*.pdf" \
      --out_root work/out_inspect
  python batch_pdf.py normalize --in_glob "work/in/**/*.pdf" \
      --out_root work/out_norm
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def matched_inputs(pattern: str) -> list[Path]:
    """Expand an absolute or relative glob (with ** support)."""
    root = Path("/") if pattern.startswith("/") else Path(".")
    relative = pattern.lstrip("/") if pattern.startswith("/") else pattern
    return sorted(p for p in root.glob(relative) if p.is_file())


def output_name(pdf: Path) -> str:
    """Stable, filesystem-safe output name for one input."""
    return pdf.name.replace(" ", "_")


def each_input(args) -> tuple[list[Path], Path]:
    inputs = matched_inputs(args.in_glob)
    if not inputs:
        print("No inputs matched", file=sys.stderr)
        raise SystemExit(2)
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    return inputs, out_root


def op_render(args) -> int:
    inputs, out_root = each_input(args)
    for pdf in inputs:
        target = out_root / output_name(pdf)
        target.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(
            [sys.executable, str(SCRIPT_DIR / "render_pdf.py"), str(pdf)]
            + ["--out_dir", str(target), "--dpi", str(args.dpi), "--engine", args.engine]
        )
    print(f"Rendered {len(inputs)} PDF(s) -> {out_root}")
    return 0


def op_inspect(args) -> int:
    inputs, out_root = each_input(args)
    for pdf in inputs:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "pdf_inspect.py"), str(pdf), "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        target = out_root / f"{output_name(pdf)}.json"
        if proc.returncode == 0:
            target.write_text(proc.stdout, encoding="utf-8")
        else:
            target.write_text(
                json.dumps({"path": str(pdf), "error": proc.stderr or proc.stdout}, indent=2),
                encoding="utf-8",
            )
    print(f"Inspected {len(inputs)} PDF(s) -> {out_root}")
    return 0


def op_normalize(args) -> int:
    inputs, out_root = each_input(args)
    for pdf in inputs:
        target = out_root / output_name(pdf)
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(
            [sys.executable, str(SCRIPT_DIR / "pdf_edit.py"), "optimize", str(pdf), "-o", str(target)]
            + ["--recover", "--optimize_streams", "--compress_streams"]
        )
    print(f"Normalized {len(inputs)} PDF(s) -> {out_root}")
    return 0


SUBCOMMANDS = {
    "render": (
        op_render,
        "render each PDF to PNGs",
        [
            (["--in_glob"], {"required": True}),
            (["--out_root"], {"required": True}),
            (["--dpi"], {"type": int, "default": 200}),
            (["--engine"], {"choices": ["pdftoppm", "pdfium"], "default": "pdftoppm"}),
        ],
    ),
    "inspect": (
        op_inspect,
        "write inspection JSON per PDF",
        [(["--in_glob"], {"required": True}), (["--out_root"], {"required": True})],
    ),
    "normalize": (
        op_normalize,
        "rewrite PDFs via pdf_edit.py optimize",
        [(["--in_glob"], {"required": True}), (["--out_root"], {"required": True})],
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, (_, help_text, arguments) in SUBCOMMANDS.items():
        sub_parser = sub.add_parser(name, help=help_text)
        for flags, options in arguments:
            sub_parser.add_argument(*flags, **options)
    args = parser.parse_args()
    handler = SUBCOMMANDS[args.cmd][0]
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
