#!/usr/bin/env python3
"""Append body XML to a base DOCX; retain the base package and final section.

Usage: merge_docx_append.py base.docx appendix.docx --out combined.docx
Requires lxml. This is a limited splice, not a dependency-aware Word merger.
Appendix styles, numbering, relationships, headers and media are not imported.
Drawings fail by default. --allow_drawings permits unresolved drawing references
only for callers who have separately made the packages compatible.
"""
import argparse
from copy import deepcopy

from word_package import DOCUMENT, Package, tag


def merge(base_docx, append_docx, out_docx, allow_drawings=False):
    result = Package(base_docx)
    document = result.xml(DOCUMENT)
    original = document.find(tag("body"))
    addition = Package(append_docx).xml(DOCUMENT).find(tag("body"))
    if original is None or addition is None:
        raise RuntimeError("Missing w:body in one of the documents")
    if not allow_drawings and any(node.tag in (tag("drawing"), tag("pict")) for node in addition.iter()):
        raise SystemExit("append.docx contains drawings/images. Use --allow_drawings only after resolving their package dependencies.")
    children = list(addition)
    if children and children[-1].tag == tag("sectPr"):
        children.pop()
    position = len(original) - int(bool(len(original)) and original[-1].tag == tag("sectPr"))
    for offset, child in enumerate(children):
        original.insert(position + offset, deepcopy(child))
    result.put_xml(DOCUMENT, document)
    result.save(out_docx)
    return {"body_children_appended": len(children)}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("base_docx")
    cli.add_argument("append_docx")
    cli.add_argument("--out", required=True)
    cli.add_argument("--allow_drawings", action="store_true")
    options = cli.parse_args()
    stats = merge(options.base_docx, options.append_docx, options.out, options.allow_drawings)
    print(f"[OK] wrote {options.out} | {stats}")


if __name__ == "__main__":
    main()
