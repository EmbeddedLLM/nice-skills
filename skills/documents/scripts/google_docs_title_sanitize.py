#!/usr/bin/env python3
"""Audit/remove title borders that can become unwanted rules on DOCX import.

Usage: google_docs_title_sanitize.py draft.docx --check
       google_docs_title_sanitize.py draft.docx --out clean.docx
Requires lxml. Removes borders from Title styles/paragraphs and a bounded
leading paragraph block in each story. Only Title styles/paragraphs lose
underlines. The leading block stops at headings, table cells, or the configured
nonempty-paragraph limit. --check reads only; --in-place replaces atomically.
"""
import argparse
from pathlib import Path

from word_package import Package, tag, text_of

MESSAGES = {
    "style_borders_removed": "Title paragraph style contains paragraph border residue",
    "paragraph_borders_removed": "Title/leading title-block paragraph contains paragraph border residue",
    "title_underlines_removed": "Title style/paragraph contains underline residue",
}


def edit(package, limit):
    counts = dict.fromkeys(MESSAGES, 0)
    names = (["word/styles.xml"] if "word/styles.xml" in package.parts else []) + package.stories()
    for name in names:
        root = package.xml(name)
        removals = []
        if name == "word/styles.xml":
            for style in root.iter(tag("style")):
                label = style.find(tag("name"))
                nameset = {style.get(tag("styleId"), "").casefold(), label.get(tag("val"), "").casefold() if label is not None else ""}
                if style.get(tag("type")) == "paragraph" and "title" in nameset:
                    removals.extend((n, "style_borders_removed") for n in style.findall(tag("pPr") + "/" + tag("pBdr")))
                    removals.extend((n, "title_underlines_removed") for n in style.iter(tag("u")))
        else:
            remaining = limit
            leading = True
            for paragraph in root.iter(tag("p")):
                style = paragraph.find(tag("pPr") + "/" + tag("pStyle"))
                identity = style.get(tag("val"), "").casefold() if style is not None else ""
                if identity.startswith(("heading", "h1", "h2")) or any(p.tag == tag("tc") for p in paragraph.iterancestors()):
                    leading = False
                if leading and text_of(paragraph).strip():
                    remaining -= 1
                leading = leading and remaining >= 0
                if leading or identity == "title":
                    removals.extend((n, "paragraph_borders_removed") for n in paragraph.findall(tag("pPr") + "/" + tag("pBdr")))
                if identity == "title":
                    removals.extend((n, "title_underlines_removed") for n in paragraph.iter(tag("u")))
        for node, category in removals:
            node.getparent().remove(node)
            counts[category] += 1
        if removals:
            package.put_xml(name, root)
    return counts


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("input_docx", type=Path)
    cli.add_argument("--out", type=Path)
    cli.add_argument("--in-place", action="store_true")
    cli.add_argument("--check", action="store_true")
    cli.add_argument("--leading-nonempty-paragraphs", type=int, default=3)
    options = cli.parse_args()
    if options.leading_nonempty_paragraphs < 1:
        cli.error("--leading-nonempty-paragraphs must be >= 1")
    if not options.check:
        if options.in_place == bool(options.out):
            cli.error("Provide exactly one of --out or --in-place, or use --check")
        if options.out and options.out.resolve() == options.input_docx.resolve():
            cli.error("--out must not overwrite the input DOCX; use --in-place instead")
    package = Package(options.input_docx)
    counts = edit(package, options.leading_nonempty_paragraphs)
    if options.check:
        for category, number in counts.items():
            if number:
                print("[FAIL] " + MESSAGES[category])
        if any(counts.values()):
            raise SystemExit(1)
        print("[OK] no Google Docs title border/rule residue detected")
    else:
        destination = options.input_docx if options.in_place else options.out
        package.save(destination)
        print(f"[OK] wrote {destination} | " + " ".join(f"{key}={number}" for key, number in counts.items()))


if __name__ == "__main__":
    main()
