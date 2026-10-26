#!/usr/bin/env python3
"""Replace one whole body paragraph token with an unevaluated Word TOC field.

Usage: insert_toc.py report.docx --out contents.docx --levels 1-3
Requires lxml. Without --out, atomically updates the input. Unrelated parts and
paragraph properties survive. Missing tokens or invalid levels fail before any
output is published. A compatible editor must refresh fields and pagination.
"""
import argparse
import os
import re
import sys

from word_package import DOCUMENT, Package, W, X, element, tag, text_of


def insert(docx, output, placeholder, levels):
    if not re.fullmatch(r"[1-9]-[1-9]", levels) or levels[0] > levels[-1]:
        raise ValueError("levels must be an ascending heading range, such as 1-3")
    package = Package(docx)
    document = package.xml(DOCUMENT)
    body = document.find(tag("body"))
    target = next((p for p in body.findall(tag("p")) if text_of(p).strip() == placeholder), None)
    if target is None:
        raise ValueError(f"Could not find a paragraph whose text == placeholder {placeholder!r}")
    anchors = {tag(name) for name in ("bookmarkStart", "bookmarkEnd", "commentRangeStart",
                                      "commentRangeEnd", "proofErr", "permStart", "permEnd")}
    token_runs = []
    for child in target:
        if child.tag in anchors or child.tag == tag("pPr"):
            continue
        if child.tag != tag("r"):
            raise ValueError("TOC placeholder must use direct plain-text runs")
        if child.findall(tag("t")):
            if any(node.tag not in (tag("rPr"), tag("t")) for node in child):
                raise ValueError("TOC placeholder run contains nontext content")
            token_runs.append(child)
        elif any(node.tag not in (tag("rPr"), tag("commentReference")) for node in child):
            raise ValueError("TOC placeholder paragraph contains unsupported run content")
    if not token_runs:
        raise ValueError("TOC placeholder contains no direct text runs")
    start, end = target.index(token_runs[0]), target.index(token_runs[-1])
    if any(child.tag in anchors for child in list(target)[start:end + 1]):
        raise ValueError("TOC placeholder crosses an anchor boundary; edit it in a compatible editor")
    for run in token_runs:
        target.remove(run)
    # Each field component is in its own run, so a reader can update the cache.
    for kind, value in (("fldChar", "begin"), ("instrText", f' TOC \\o "{levels}" \\h \\z \\u '),
                        ("fldChar", "separate"), ("t", "(TOC will populate after updating fields)"),
                        ("fldChar", "end")):
        run = element("r")
        node = element(kind)
        if kind == "fldChar":
            node.set(tag("fldCharType"), value)
        else:
            node.text = value
            node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        run.append(node)
        target.insert(start, run)
        start += 1
    package.put_xml(DOCUMENT, document)
    settings_path = package.document_part("settings", "word/settings.xml")
    settings = package.xml(settings_path) if settings_path in package.parts else X.Element(tag("settings"), nsmap={"w": W})
    update = settings.find(tag("updateFields"))
    if update is None:
        update = element("updateFields")
        # CT_Settings is a sequence. These successors come from the bundled
        # ecma376-transitional/wml.xsd, including the imported math/schema slots.
        successors = set("hdrShapeDefaults footnotePr endnotePr compat docVars rsids mathPr "
                         "attachedSchema themeFontLang clrSchemeMapping doNotIncludeSubdocsInStats "
                         "doNotAutoCompressPictures forceUpgrade captions readModeInkLockDown "
                         "smartTagType schemaLibrary shapeDefaults doNotEmbedSmartTags "
                         "decimalSymbol listSeparator".split())
        position = next((index for index, child in enumerate(settings)
                         if isinstance(child.tag, str) and X.QName(child).localname in successors), len(settings))
        settings.insert(position, update)
    update.set(tag("val"), "true")
    package.put_xml(settings_path, settings)
    package.register(settings_path, "settings")
    package.save(output)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("docx")
    cli.add_argument("--out")
    cli.add_argument("--placeholder", default="[[TOC]]")
    cli.add_argument("--levels", default="1-3")
    options = cli.parse_args()
    output = options.out or options.docx
    insert(options.docx, output, options.placeholder, options.levels)
    print(f"[OK] Inserted TOC field at placeholder {options.placeholder!r} → {output}")
    print("Refresh the entire TOC in the target editor, save, and inspect pagination.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        if os.environ.get("DOCS_DEBUG") == "1":
            raise
        print(f"[ERROR] {error}", file=sys.stderr)
        sys.exit(2)
