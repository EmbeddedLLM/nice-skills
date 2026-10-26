#!/usr/bin/env python3
"""Multi-purpose PDF content extractor.

Subcommands:
  info         - quick summary (delegates to the sibling pdf_inspect script)
  text         - plain text
  words        - word bounding boxes
  chars        - per-character boxes (fine-grained layout)
  tables       - tables as CSV / JSON / XLSX
  images       - embedded images
  attachments  - embedded file attachments
  annotations  - annotation listing
  forms        - form field listing

Examples:
  python pdf_extract.py text input.pdf --method pdfplumber --out work/text.txt
  python pdf_extract.py words input.pdf --out words.csv
  python pdf_extract.py tables input.pdf --out_dir work/tables --format xlsx
  python pdf_extract.py images input.pdf --out_dir work/images

Coordinate note: pdfplumber and PyMuPDF both report boxes with a top-left
origin and y growing downward.
"""

from __future__ import annotations

import argparse
import sys
import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable


# ------------------------------------------------------------ page selection

def page_ranges(spec: str | None) -> list[tuple[int, int]] | None:
    """Parse "1-3,5" into 1-based inclusive ranges; None selects everything."""
    if not spec or not spec.strip():
        return None
    ranges: list[tuple[int, int]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            first, last = (int(x) for x in part.split("-", 1))
            if first <= 0 or last <= 0:
                raise ValueError("Page numbers must be >= 1")
            ranges.append((min(first, last), max(first, last)))
        else:
            page = int(part)
            if page <= 0:
                raise ValueError("Page numbers must be >= 1")
            ranges.append((page, page))
    return ranges


def selected_pages(page_count: int, ranges: list[tuple[int, int]] | None) -> Iterable[int]:
    if not ranges:
        return range(1, page_count + 1)
    return (
        page
        for first, last in ranges
        for page in range(max(1, first), min(page_count, last) + 1)
    )


# ------------------------------------------------------------------- output

def emit_rows(rows: list[dict], out: str | None) -> None:
    """Rows go to JSON when the destination ends in .json, CSV otherwise."""
    if not out:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    destination = Path(out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.suffix.lower() == ".json":
        destination.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        return
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({key for row in rows for key in row}))
        writer.writeheader()
        writer.writerows(rows)


def emit_document(document: Any, out: str | None) -> None:
    text = json.dumps(document, indent=2, ensure_ascii=False)
    if out:
        Path(out).write_text(text, encoding="utf-8")
    else:
        print(text)


# ------------------------------------------------------------- subcommands

def run_info(args) -> int:
    command = [sys.executable, str(Path(__file__).with_name("pdf_inspect.py")), args.input_pdf]
    if args.password:
        command += ["--password", args.password]
    if args.json:
        command += ["--json"]
    return subprocess.call(command)


def run_text(args) -> int:
    ranges = page_ranges(args.pages)
    parts: list[str] = []

    if args.method == "pdftotext":
        # Disjoint page ranges are not supported here; the whole document is
        # dumped.  For page control use the pdfplumber/pymupdf/pypdf methods.
        proc = subprocess.run(
            ["pdftotext", args.input_pdf, "-"],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode("utf-8", "ignore").strip() or "pdftotext failed")
        parts.append(proc.stdout.decode("utf-8", "ignore"))
    elif args.method == "pypdf":
        from pypdf import PdfReader

        reader = PdfReader(args.input_pdf)
        for page_no in selected_pages(len(reader.pages), ranges):
            parts.append(reader.pages[page_no - 1].extract_text() or "")
    elif args.method == "pdfplumber":
        import pdfplumber

        with pdfplumber.open(args.input_pdf) as pdf:
            for page_no in selected_pages(len(pdf.pages), ranges):
                parts.append(pdf.pages[page_no - 1].extract_text() or "")
    elif args.method == "pymupdf":
        import fitz

        with fitz.open(args.input_pdf) as doc:
            for page_no in selected_pages(doc.page_count, ranges):
                parts.append(doc.load_page(page_no - 1).get_text("text") or "")
    else:
        raise ValueError(f"Unknown method: {args.method}")

    text = "\n\n".join(parts)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


def run_words(args) -> int:
    ranges = page_ranges(args.pages)
    rows: list[dict] = []
    if args.method == "pdfplumber":
        import pdfplumber

        with pdfplumber.open(args.input_pdf) as pdf:
            for page_no in selected_pages(len(pdf.pages), ranges):
                for word in pdf.pages[page_no - 1].extract_words():
                    rows.append({
                        "page": page_no,
                        "text": word.get("text", ""),
                        "x0": word.get("x0"),
                        "x1": word.get("x1"),
                        "top": word.get("top"),
                        "bottom": word.get("bottom"),
                        "doctop": word.get("doctop"),
                    })
    elif args.method == "pymupdf":
        import fitz

        with fitz.open(args.input_pdf) as doc:
            for page_no in selected_pages(doc.page_count, ranges):
                for x0, y0, x1, y1, word, block_no, line_no, word_no in (
                    doc.load_page(page_no - 1).get_text("words")
                ):
                    rows.append({
                        "page": page_no,
                        "text": word,
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                        "block": block_no,
                        "line": line_no,
                        "word_no": word_no,
                    })
    else:
        raise ValueError("--method must be pdfplumber or pymupdf")
    emit_rows(rows, args.out)
    return 0


def run_chars(args) -> int:
    """Per-character boxes via pdfplumber (the reliable char metrics)."""
    import pdfplumber

    ranges = page_ranges(args.pages)
    rows = []
    with pdfplumber.open(args.input_pdf) as pdf:
        for page_no in selected_pages(len(pdf.pages), ranges):
            for ch in pdf.pages[page_no - 1].chars or []:
                rows.append({
                    "page": page_no,
                    "text": ch.get("text", ""),
                    "x0": ch.get("x0"),
                    "x1": ch.get("x1"),
                    "top": ch.get("top"),
                    "bottom": ch.get("bottom"),
                    "doctop": ch.get("doctop"),
                    "fontname": ch.get("fontname"),
                    "size": ch.get("size"),
                })
    emit_rows(rows, args.out)
    return 0


def run_tables(args) -> int:
    import pdfplumber

    ranges = page_ranges(args.pages)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    collected: list[tuple[str, list[list]]] = []

    with pdfplumber.open(args.input_pdf) as pdf:
        for page_no in selected_pages(len(pdf.pages), ranges):
            for table_no, table in enumerate(
                pdf.pages[page_no - 1].extract_tables(), start=1,
            ):
                normalized = [
                    [None if cell is None else str(cell) for cell in row]
                    for row in table
                    if row is not None
                ]
                stem = f"page{page_no:03d}_table{table_no:02d}"
                if args.format == "csv":
                    with (out_dir / f"{stem}.csv").open("w", newline="", encoding="utf-8") as fh:
                        csv.writer(fh).writerows(normalized)
                elif args.format == "json":
                    (out_dir / f"{stem}.json").write_text(
                        json.dumps(normalized, indent=2, ensure_ascii=False), encoding="utf-8")
                elif args.format == "xlsx":
                    collected.append((stem, normalized))
                else:
                    raise ValueError("--format must be csv|json|xlsx")

    if args.format == "xlsx":
        try:
            from openpyxl import Workbook
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("openpyxl is required for xlsx output") from exc
        book = Workbook()
        book.remove(book.active)
        for stem, table in collected:
            sheet = book.create_sheet(title=stem[:31])
            for row_no, row in enumerate(table, start=1):
                for col_no, cell in enumerate(row, start=1):
                    sheet.cell(row=row_no, column=col_no, value=cell)
        book.save(out_dir / "tables.xlsx")

    print(f"Wrote tables to: {out_dir}")
    return 0


def run_images(args) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ranges = page_ranges(args.pages)

    if args.method == "pdfimages":
        proc = subprocess.run(
            ["pdfimages", "-all", args.input_pdf, str(out_dir / "img")],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "pdfimages failed")
        print(f"Extracted images to: {out_dir}")
        return 0
    if args.method != "pymupdf":
        raise ValueError("--method must be pymupdf or pdfimages")

    import fitz

    count = 0
    with fitz.open(args.input_pdf) as doc:
        for page_no in selected_pages(doc.page_count, ranges):
            for image_no, image in enumerate(
                doc.load_page(page_no - 1).get_images(full=True), start=1,
            ):
                pixmap = fitz.Pixmap(doc, image[0])
                if pixmap.n - pixmap.alpha > 3:
                    pixmap = fitz.Pixmap(fitz.csRGB, pixmap)
                pixmap.save(out_dir / f"page{page_no:03d}_img{image_no:03d}.png")
                count += 1
    print(f"Extracted {count} images to: {out_dir}")
    return 0


def run_attachments(args) -> int:
    from pypdf import PdfReader

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for name, payload in (getattr(PdfReader(args.input_pdf), "attachments", {}) or {}).items():
        # One name may map to a single payload or a list of them.
        items = payload if isinstance(payload, list) else [payload]
        for index, data in enumerate(items, start=1):
            safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name) or "attachment"
            if len(items) > 1:
                safe = f"{safe}.{index}"
            (out_dir / safe).write_bytes(data)
            written += 1
    print(f"Wrote {written} attachments to: {out_dir}")
    return 0


def run_annotations(args) -> int:
    from pypdf import PdfReader

    reader = PdfReader(args.input_pdf)
    found: list[dict] = []
    for page_no in selected_pages(len(reader.pages), page_ranges(args.pages)):
        for annot_ref in reader.pages[page_no - 1].get("/Annots") or []:
            try:
                annot = annot_ref.get_object()
            except Exception:
                continue
            found.append({
                "page": page_no,
                "subtype": str(annot.get("/Subtype")),
                "rect": [float(x) for x in (annot.get("/Rect") or [])],
                "contents": (
                    str(annot.get("/Contents")) if annot.get("/Contents") is not None else None),
                "name": str(annot.get("/NM")) if annot.get("/NM") is not None else None,
            })
    emit_document(found, args.out)
    return 0


# ------------------------------------------------------------------- forms

def _resolve(ref: Any) -> Any:
    try:
        return ref.get_object()
    except Exception:
        return ref


def _qualified_name(field: Any) -> str:
    """Best-effort hierarchical field name: /T parts joined with '.' up the
    /Parent chain (viewers vary; good enough for debugging)."""
    parts: list[str] = []
    seen = set()
    current = field
    while current is not None:
        current = _resolve(current)
        marker = id(current)
        if marker in seen:
            break
        seen.add(marker)
        title = current.get("/T") if hasattr(current, "get") else None
        if title is not None:
            parts.append(str(title))
        current = current.get("/Parent") if hasattr(current, "get") else None
    return ".".join(reversed(parts))


def _field_kind(field_type: Any, flags: int) -> str:
    if field_type == "/Btn":
        if flags & (1 << 16):
            return "button"
        if flags & (1 << 15):
            return "radio"
        return "checkbox"
    return {"/Tx": "text", "/Ch": "choice", "/Sig": "signature"}.get(field_type, "unknown")


def _appearance_states(annot: Any):
    """Named appearance states of a widget (checkboxes/radios), when present.

    /AP /N is either a normal-appearance stream or a dictionary of named
    appearances (e.g. /Off, /Yes); pypdf exposes both as dict-like, so the
    stream case must be ruled out explicitly.
    """
    from pypdf.generic import DictionaryObject, StreamObject

    try:
        appearance = _resolve(annot.get("/AP"))
        normal = _resolve(appearance.get("/N")) if appearance else None
        if isinstance(normal, DictionaryObject) and not isinstance(normal, StreamObject):
            return [str(key) for key in normal.keys()]
    except Exception:
        pass
    return None


def run_forms(args) -> int:
    from pypdf import PdfReader

    reader = PdfReader(args.input_pdf)
    result: dict[str, Any] = {}
    for name, field in (reader.get_fields() or {}).items():
        field = _resolve(field)
        get = field.get if hasattr(field, "get") else lambda *_: None
        entry: dict[str, Any] = {
            "type": str(get("/FT")) if get("/FT") is not None else None,
            "value": str(get("/V")) if get("/V") is not None else None,
            "default": str(get("/DV")) if get("/DV") is not None else None,
            "alt_name": str(get("/TU")) if get("/TU") is not None else None,
            "flags": int(get("/Ff")) if get("/Ff") is not None else None,
        }
        # Choice fields carry /Opt as ["A","B"] or [["export","display"], ...]
        if get("/Opt") is not None:
            try:
                entry["options"] = [
                    list(option) if isinstance(option, (list, tuple)) else str(option)
                    for option in get("/Opt")
                ]
            except Exception:
                entry["options"] = None
        entry["field_kind"] = _field_kind(entry["type"], entry["flags"] or 0)
        result[name] = entry

    if args.include_widgets:
        # Widget annotations carry page + rect, which is what alignment
        # debugging needs.
        for page_no, page in enumerate(reader.pages, start=1):
            for annot_ref in page.get("/Annots") or []:
                annot = _resolve(annot_ref)
                if not hasattr(annot, "get") or str(annot.get("/Subtype")) != "/Widget":
                    continue
                parent = annot.get("/Parent")
                field_obj = _resolve(parent) if parent is not None else annot
                name = _qualified_name(annot) or _qualified_name(field_obj)
                if not name and annot.get("/T") is not None:
                    name = str(annot.get("/T"))
                if name and name not in result:
                    # Match pypdf's get_fields keys by unique ending component.
                    matches = [key for key in result
                               if key == name or key.endswith("." + name)]
                    if len(matches) == 1:
                        name = matches[0]
                rect = annot.get("/Rect") or []
                widget = {
                    "page": page_no,
                    "rect": [float(x) for x in rect] if rect else None,
                    "appearance_states": _appearance_states(annot),
                }
                if name:
                    result.setdefault(name, {}).setdefault("widgets", []).append(widget)
                else:
                    result.setdefault("__unmatched_widgets__", []).append(widget)

    emit_document(result, args.out)
    return 0


# ---------------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="cmd", required=True)

    info = commands.add_parser("info", help="inspect pdf")
    info.add_argument("input_pdf")
    info.add_argument("--json", action="store_true")
    info.add_argument("--password", default=None)

    text = commands.add_parser("text", help="extract plain text")
    text.add_argument("input_pdf")
    text.add_argument("--method",
                      choices=["pdfplumber", "pymupdf", "pypdf", "pdftotext"],
                      default="pdfplumber")
    text.add_argument("--pages", default=None, help="e.g. 1-3,5")
    text.add_argument("--out", "--output", dest="out", default=None)

    words = commands.add_parser("words", help="extract word boxes")
    words.add_argument("input_pdf")
    words.add_argument("--method", choices=["pdfplumber", "pymupdf"], default="pdfplumber")
    words.add_argument("--pages", default=None)
    words.add_argument("--out", "--output", dest="out", default=None,
                       help=".csv or .json; if omitted prints JSON")

    chars = commands.add_parser("chars", help="extract character boxes")
    chars.add_argument("input_pdf")
    chars.add_argument("--pages", default=None)
    chars.add_argument("--out", "--output", dest="out", default=None,
                       help=".csv or .json; if omitted prints JSON")

    tables = commands.add_parser("tables", help="extract tables")
    tables.add_argument("input_pdf")
    tables.add_argument("--pages", default=None)
    tables.add_argument("--out_dir", required=True)
    tables.add_argument("--format", choices=["csv", "json", "xlsx"], default="csv")

    images = commands.add_parser("images", help="extract images")
    images.add_argument("input_pdf")
    images.add_argument("--pages", default=None)
    images.add_argument("--out_dir", required=True)
    images.add_argument("--method", choices=["pymupdf", "pdfimages"], default="pymupdf")

    attachments = commands.add_parser("attachments", help="extract embedded attachments")
    attachments.add_argument("input_pdf")
    attachments.add_argument("--out_dir", required=True)

    annotations = commands.add_parser("annotations", help="list annotations")
    annotations.add_argument("input_pdf")
    annotations.add_argument("--pages", default=None)
    annotations.add_argument("--out", "--output", dest="out", default=None)

    forms = commands.add_parser("forms", help="list form fields")
    forms.add_argument("input_pdf")
    forms.add_argument("--out", "--output", dest="out", default=None)
    forms.add_argument("--include_widgets", "--include-widgets",
                       dest="include_widgets", action="store_true")
    return parser


HANDLERS = {
    "info": run_info,
    "text": run_text,
    "words": run_words,
    "chars": run_chars,
    "tables": run_tables,
    "images": run_images,
    "attachments": run_attachments,
    "annotations": run_annotations,
    "forms": run_forms,
}


def main() -> int:
    args = build_parser().parse_args()
    handler = HANDLERS.get(args.cmd)
    if handler is None:
        raise AssertionError(f"Unhandled cmd: {args.cmd}")
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
