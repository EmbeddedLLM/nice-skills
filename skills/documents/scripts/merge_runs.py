"""Coalesce neighbouring runs that share identical formatting in a DOCX.

Word fragments paragraph text across many <w:r> elements (revision-save ids,
spell-check markers, editing history), which makes find-and-replace over
word/document.xml unreliable: the string you want is split across runs.
This tool joins adjacent runs whose properties (<w:rPr>) match, removes
rsid attributes and proofErr markers, and folds the text elements -
<w:t>, plus <w:delText> inside tracked deletions - into one.

Rendering is unchanged.  Merging follows the text a reader sees: without
xml:space="preserve", boundary whitespace is trimmed before display, so
<w:t>Hello </w:t> + <w:t>world</w:t> reads and merges as "Hello world".

Runs living in different <w:ins>/<w:del> wrappers are never joined: that
would rewrite tracked-change structure, collapsing distinct revisions.

Only word/document.xml is processed (not headers, footers, or notes).

Usage:
    python merge_runs.py unpacked/                     # directory, in place
    python merge_runs.py document.docx -o merged.docx  # packed, input kept
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

from office.helpers import XML_SPACE, rendered_text, rezip, safe_extract

WML = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
RUN = f"{{{WML}}}r"
RUN_PROPS = f"{{{WML}}}rPr"
PROOF_MARKER = f"{{{WML}}}proofErr"
TEXT_TAGS = (f"{{{WML}}}t", f"{{{WML}}}delText")
SPACE_ATTR = "{http://www.w3.org/XML/1998/namespace}space"
_PERMITTED_RUN_CHILDREN = frozenset({RUN_PROPS, *TEXT_TAGS})


def merge_runs(input_dir) -> tuple[int, str]:
    """Merge runs under ``input_dir`` in place; return (count, message)."""
    document_xml = Path(input_dir) / "word" / "document.xml"
    if not document_xml.is_file():
        return 0, f"Error: {document_xml} not found"
    try:
        count = _coalesce_document(document_xml)
    except Exception as exc:  # surfaced as a message so the CLI stays quiet
        return 0, f"Error: {exc}"
    return count, f"Merged {count} runs"


def _coalesce_document(document_xml: Path) -> int:
    tree = etree.parse(str(document_xml), etree.XMLParser(remove_blank_text=False))
    root = tree.getroot()

    for marker in [node for node in root.iter(PROOF_MARKER)]:
        marker.getparent().remove(marker)

    runs = [node for node in root.iter(RUN)]
    for run in runs:
        for attr in list(run.attrib):
            if "rsid" in attr.rsplit("}", 1)[-1].lower():
                del run.attrib[attr]

    containers: list = []
    seen: set[int] = set()
    for run in runs:
        parent = run.getparent()
        if parent is not None and id(parent) not in seen:
            seen.add(id(parent))
            containers.append(parent)

    merged = sum(_coalesce_siblings(container) for container in containers)
    tree.write(
        str(document_xml), xml_declaration=True, encoding="UTF-8", standalone=True
    )
    return merged


def _coalesce_siblings(container) -> int:
    merged = 0
    run = next((child for child in container if child.tag == RUN), None)
    while run is not None:
        following = _next_run(run)
        while following is not None and _mergeable(run, following):
            _absorb(run, following)
            container.remove(following)
            merged += 1
            following = _next_run(run)
        _fold_text_children(run)
        run = following
    return merged


def _next_run(node):
    """Next sibling element if it is a run, else None."""
    sibling = node.getnext()
    return sibling if sibling is not None and sibling.tag == RUN else None


def _mergeable(first, second) -> bool:
    if dict(first.attrib) != dict(second.attrib):
        return False
    for run in (first, second):
        for child in run:
            if child.tag not in _PERMITTED_RUN_CHILDREN:
                return False
    props_first = first.find(RUN_PROPS)
    props_second = second.find(RUN_PROPS)
    if (props_first is None) != (props_second is None):
        return False
    if props_first is None:
        return True
    return etree.tostring(props_first) == etree.tostring(props_second)


def _absorb(target, source) -> None:
    for child in list(source):
        if child.tag != RUN_PROPS:
            target.append(child)


def _fold_text_children(run) -> None:
    for tag in TEXT_TAGS:
        holders = [child for child in run if child.tag == tag]
        for current, previous in zip(
            reversed(holders[1:]), reversed(holders[:-1])
        ):
            if previous.getnext() is not current:
                continue
            if (previous.tail or "").strip(XML_SPACE):
                continue
            if len(previous) or len(current):
                continue  # unexpected nested markup: leave the pair alone
            combined = _holder_text(previous) + _holder_text(current)
            keep_space = (
                combined != combined.strip(XML_SPACE)
                or previous.get(SPACE_ATTR) == "preserve"
                or current.get(SPACE_ATTR) == "preserve"
            )
            previous.text = combined
            if keep_space:
                previous.set(SPACE_ATTR, "preserve")
            else:
                previous.attrib.pop(SPACE_ATTR, None)
            run.remove(current)


def _holder_text(element) -> str:
    return rendered_text(element.text or "", element.get(SPACE_ATTR) == "preserve")


def _merge_tree_or_die(root: Path) -> str:
    _, message = merge_runs(root)
    if message.startswith("Error"):
        print(message, file=sys.stderr)
        sys.exit(1)
    return message


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coalesce adjacent identically formatted runs in a DOCX"
        " (unpacked directory or packed .docx/.dotx)."
    )
    parser.add_argument("input", help="Unpacked DOCX directory OR a .docx/.dotx file")
    parser.add_argument(
        "-o", "--output",
        help="Output .docx path (packed input only; a fresh path is required)",
    )
    args = parser.parse_args()

    src = Path(args.input)
    try:
        if src.is_dir():
            if args.output:
                parser.error(
                    "--output applies to packed input; directories are edited in place"
                )
            print(_merge_tree_or_die(src))
        elif src.is_file() and src.suffix.lower() in (".docx", ".dotx"):
            if not args.output:
                parser.error("Packed input requires --output with a new path")
            out = Path(args.output)
            if out.exists() or out.is_symlink():
                parser.error("Choose a new output path")
            with tempfile.TemporaryDirectory() as staging:
                staging_dir = Path(staging)
                with zipfile.ZipFile(src) as archive:
                    safe_extract(archive, staging_dir)
                message = _merge_tree_or_die(staging_dir)
                rezip(staging_dir, out)
            print(f"{message}; wrote {out}")
        else:
            print(
                f"Error: {src} is neither a directory nor a .docx/.dotx file",
                file=sys.stderr,
            )
            sys.exit(1)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
