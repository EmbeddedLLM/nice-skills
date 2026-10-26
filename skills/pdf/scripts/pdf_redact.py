#!/usr/bin/env python3
"""Redact PDF content for real — not black boxes painted over live text.

Painting a rectangle leaves the underlying content extractable; PyMuPDF's
redact annotations plus apply_redactions() actually remove it.

Golden paths:
  python pdf_redact.py text in.pdf out.pdf --text "TOP SECRET"
  python pdf_redact.py text in.pdf out.pdf --text "secret" --ignore_case
  python pdf_redact.py boxes in.pdf out.pdf --boxes_json boxes.json

Always verify afterwards: render the output and spot-check, and confirm the
sensitive string no longer extracts (pdftotext / pdfplumber).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF


# ------------------------------------------------------------ page ranges

def select_pages(spec: str | None, page_count: int) -> list[int]:
    """'1-3,5,7-' (1-indexed) -> sorted-order-preserving 0-indexed pages."""
    if not spec:
        return list(range(page_count))
    pages: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            first_s, last_s = (piece.strip() for piece in part.split("-", 1))
            first = int(first_s) if first_s else 1
            last = int(last_s) if last_s else page_count
            pages.extend(range(max(1, first) - 1, min(page_count, last)))
        else:
            page = int(part)
            if 1 <= page <= page_count:
                pages.append(page - 1)
    return list(dict.fromkeys(pages))


# ------------------------------------------------------------- text search

def load_needles(args) -> list[str]:
    needles = list(args.text or [])
    if args.text_file:
        for line in Path(args.text_file).read_text(
                encoding="utf-8", errors="ignore").splitlines():
            needles.append(line.strip("\n\r"))
    return [needle for needle in (n.strip() for n in needles) if needle]


def reading_order_words(page: fitz.Page) -> list[tuple[fitz.Rect, str]]:
    """Word boxes in stable reading-ish order (block, line, word, y, x)."""
    words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,word_no
    words.sort(key=lambda w: (w[5], w[6], w[7], w[1], w[0]))
    return [(fitz.Rect(w[0], w[1], w[2], w[3]), str(w[4])) for w in words]


def window_matches(window, needle_tokens, *, ignore_case: bool, whole_word: bool) -> bool:
    if len(window) != len(needle_tokens):
        return False
    for actual, wanted in zip(window, needle_tokens):
        if ignore_case:
            actual, wanted = actual.casefold(), wanted.casefold()
        if whole_word:
            # Punctuation glued to a token should not defeat a word match.
            actual = re.sub(r"^\W+|\W+$", "", actual)
            wanted = re.sub(r"^\W+|\W+$", "", wanted)
        if actual != wanted:
            return False
    return True


def find_by_words(page, needle: str, *, ignore_case: bool, whole_word: bool):
    """Best-effort phrase search over word boxes (case/whole-word aware)."""
    tokens = [token for token in needle.split() if token]
    if not tokens:
        return []
    words = reading_order_words(page)
    texts = [text for _, text in words]
    hits = []
    size = len(tokens)
    for start in range(0, max(0, len(texts) - size + 1)):
        if window_matches(texts[start:start + size], tokens,
                          ignore_case=ignore_case, whole_word=whole_word):
            union = None
            for rect, _text in words[start:start + size]:
                union = rect if union is None else union | rect
            if union is not None:
                hits.append(union)
    return hits


# ------------------------------------------------------------------- boxes

def load_box_specs(path: Path) -> list[tuple[int, list[float]]]:
    """Parse the two boxes JSON shapes:

    1. {"items": [{"page": 1, "rect": [...]}, ...]}
    2. {"pages": {"1": {"boxes": [{"rect": [...]} , ...]}}}
    """
    document = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    if isinstance(document, dict) and isinstance(document.get("items"), list):
        return [
            (int(item["page"]), [float(v) for v in item["rect"]])
            for item in document["items"]
            if isinstance(item, dict) and "page" in item and "rect" in item
        ]
    if isinstance(document, dict) and isinstance(document.get("pages"), dict):
        specs = []
        for key, value in document["pages"].items():
            try:
                page_no = int(key)
            except Exception:
                continue
            if not isinstance(value, dict):
                continue
            for box in value.get("boxes", []) or []:
                if isinstance(box, dict) and "rect" in box:
                    specs.append((page_no, [float(v) for v in box["rect"]]))
        return specs
    raise ValueError("Unsupported boxes JSON format")


# ------------------------------------------------------------------ colors

def parse_fill(fill: str) -> tuple[float, float, float]:
    text = fill.strip().lower()
    if text in ("black", "#000", "#000000"):
        return (0.0, 0.0, 0.0)
    if text in ("white", "#fff", "#ffffff"):
        return (1.0, 1.0, 1.0)
    match = re.fullmatch(r"#?([0-9a-f]{6})", text)
    if match:
        value = match.group(1)
        return (
            int(value[0:2], 16) / 255.0,
            int(value[2:4], 16) / 255.0,
            int(value[4:6], 16) / 255.0,
        )
    raise ValueError("fill must be black|white|#RRGGBB")


IMAGE_MODES = {
    "remove": fitz.PDF_REDACT_IMAGE_REMOVE,   # safest default
    "pixels": fitz.PDF_REDACT_IMAGE_PIXELS,
    "none": fitz.PDF_REDACT_IMAGE_NONE,
}


def apply_and_save(doc: fitz.Document, output: Path, image_mode: str) -> None:
    mode = IMAGE_MODES[image_mode]
    for page_no in range(doc.page_count):
        # text=PDF_REDACT_TEXT_REMOVE removes the text under the redaction.
        doc.load_page(page_no).apply_redactions(
            images=mode, graphics=1, text=fitz.PDF_REDACT_TEXT_REMOVE)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output), garbage=4, clean=1, deflate=1, incremental=0)


def open_document(path: Path, password: str | None) -> fitz.Document:
    doc = fitz.open(str(path))
    if doc.is_encrypted and password:
        doc.authenticate(password)
    return doc


# ------------------------------------------------------------------- runs

def run_text(args) -> int:
    needles = load_needles(args)
    if not needles:
        print("ERROR: provide --text and/or --text_file", file=sys.stderr)
        return 2
    fill = parse_fill(args.fill)
    doc = open_document(args.input_pdf, args.password)
    pages = select_pages(args.pages, doc.page_count)

    applied = 0
    for page_no in pages:
        page = doc.load_page(page_no)
        for needle in needles:
            if args.ignore_case or args.whole_word:
                rects = find_by_words(page, needle,
                                      ignore_case=args.ignore_case,
                                      whole_word=args.whole_word)
            else:
                # Fast path: MuPDF's own search (case-sensitive).
                rects = page.search_for(needle)
            for rect in rects:
                # Content behind the annotation is removed when
                # apply_redactions() runs.
                page.add_redact_annot(rect, fill=fill)
                applied += 1
    if applied == 0:
        print("WARNING: no matches found")
    apply_and_save(doc, args.output_pdf, args.image_mode)
    print(f"Applied {applied} redaction(s) -> {args.output_pdf}")
    return 0


def run_boxes(args) -> int:
    fill = parse_fill(args.fill)
    boxes = load_box_specs(Path(args.boxes_json))
    doc = open_document(args.input_pdf, args.password)
    allowed = set(select_pages(args.pages, doc.page_count))

    applied = 0
    for page_1based, rect in boxes:
        if page_1based - 1 not in allowed:
            continue
        page = doc.load_page(page_1based - 1)
        x0, y0, x1, y1 = rect
        page.add_redact_annot(fitz.Rect(float(x0), float(y0), float(x1), float(y1)), fill=fill)
        applied += 1
    if applied == 0:
        print("WARNING: no boxes applied (check pages filter)")
    apply_and_save(doc, args.output_pdf, args.image_mode)
    print(f"Applied {applied} redaction(s) -> {args.output_pdf}")
    return 0


# ---------------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="cmd", required=True)

    text = commands.add_parser("text", help="redact by searching for text")
    text.add_argument("input_pdf", type=Path)
    text.add_argument("output_pdf", type=Path)
    text.add_argument("--text", action="append", default=[],
                      help="Text / phrase to redact (repeatable)")
    text.add_argument("--text_file", default=None, help="File with one phrase per line")
    text.add_argument("--pages", default=None, help='Page range like "1-3,5" (1-indexed)')
    text.add_argument("--ignore_case", action="store_true",
                      help="Best-effort case-insensitive match using word boxes")
    text.add_argument("--whole_word", action="store_true",
                      help="Best-effort whole-word match (strips punctuation)")
    text.add_argument("--fill", default="black",
                      help="Fill color for redaction box: black|white|#RRGGBB")
    text.add_argument("--image_mode", choices=list(IMAGE_MODES), default="remove")
    text.add_argument("--password", default=None)

    boxes = commands.add_parser(
        "boxes", help="redact by rectangle(s) in a JSON file (PDF points)")
    boxes.add_argument("input_pdf", type=Path)
    boxes.add_argument("output_pdf", type=Path)
    boxes.add_argument("--boxes_json", required=True,
                       help="JSON file with page+rect entries")
    boxes.add_argument("--pages", default=None, help='Optional page filter like "1-3,5"')
    boxes.add_argument("--fill", default="black")
    boxes.add_argument("--image_mode", choices=list(IMAGE_MODES), default="remove")
    boxes.add_argument("--password", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.cmd == "text":
        return run_text(args)
    if args.cmd == "boxes":
        return run_boxes(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
