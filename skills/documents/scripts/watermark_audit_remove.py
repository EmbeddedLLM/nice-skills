#!/usr/bin/env python3
"""Inspect stamp-like XML or remove pictures selected by VML text.

Usage: watermark_audit_remove.py marked.docx --mode report
       watermark_audit_remove.py marked.docx --mode remove --contains DRAFT --out clean.docx
Requires lxml. Reports are heuristics: text paths can be ordinary artwork.
Removal requires a nonempty, case-insensitive text filter and removes the whole
matching w:pict container. Unmatched drawings, paragraphs, and package members
survive. DrawingML stamps require separate inspection; report hits do not imply
that this remover supports the object. Output replacement is atomic.
"""
import argparse

from word_package import Package, tag

TEXTPATH = "{urn:schemas-microsoft-com:vml}textpath"


def report(docx):
    package = Package(docx)
    total = 0
    for name in sorted(package.stories()):
        root = package.xml(name)
        hits = [("vml_textpath", node.get("string").strip()) for node in root.iter(TEXTPATH)
                if node.get("string", "").strip()]
        for node in root.iter():
            value = next((value for value in node.attrib.values() if "watermark" in value.casefold()), None)
            if value is not None:
                hits.append(("attr_watermark", value))
        if hits:
            print(f"[{name}]")
            for category, label in hits[:50]:
                print(f"  - {category}: {label}")
        total += len(hits)
    print(f"[summary] watermark_like_hits={total}")
    return total


def remove(docx, out, contains):
    if not contains:
        raise ValueError("Removal requires a nonempty text filter")
    package = Package(docx)
    for name in package.stories():
        root = package.xml(name)
        selected = [picture for picture in root.iter(tag("pict"))
                    if any(contains.casefold() in node.get("string", "").casefold() for node in picture.iter(TEXTPATH))]
        for picture in selected:
            picture.getparent().remove(picture)
        if selected:
            package.put_xml(name, root)
    package.save(out)
    print(f"[OK] wrote {out}")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("in_docx")
    cli.add_argument("--mode", required=True, choices=("report", "remove"))
    cli.add_argument("--contains")
    cli.add_argument("--out")
    options = cli.parse_args()
    if options.mode == "report":
        report(options.in_docx)
    elif not options.contains or not options.out:
        cli.error("--contains and --out are required when --mode remove")
    else:
        remove(options.in_docx, options.out, options.contains)


if __name__ == "__main__":
    main()
