#!/usr/bin/env python3
"""Report selected DOCX accessibility risks; optionally apply mechanical edits.

Usage: a11y_audit.py report.docx --out_json findings.json
       a11y_audit.py report.docx --fix_table_headers first_row --out headers.docx
Requires lxml. Body/header/footer checks cover heading jumps, missing image
labels, unmarked first table rows, and vague or raw-URL link text. Exit 1 means
high findings remain; it is not a conformance result. Filename-derived labels
(--fix_image_alt from_filename) are placeholders requiring human review, and a
first row should be marked only after confirming that it contains headings.
"""
import argparse
import json
import posixpath
import re
from pathlib import Path

from word_package import Package, R, element, tag, text_of

WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/main"


def inspect_story(root, part):
    findings = []
    def add(severity, kind, message, **context):
        findings.append(dict(severity=severity, kind=kind, message=message, context={"part": part, **context}))
    previous = None
    for paragraph in root.iter(tag("p")):
        style = paragraph.find(tag("pPr") + "/" + tag("pStyle"))
        match = re.fullmatch(r"Heading\s*(\d+)", style.get(tag("val"), "")) if style is not None else None
        if match:
            level = int(match[1])
            if previous is not None and level > previous + 1:
                add("medium", "heading_skip", f"Heading level jumped from {previous} to {level}", text=text_of(paragraph)[:120])
            previous = level
    for properties in root.iter("{" + WP + "}docPr"):
        if not any(properties.get(key, "").strip() for key in ("descr", "title")):
            add("high", "image_missing_alt", "Image missing alt text (descr/title empty)", id=properties.get("id"), name=properties.get("name"))
    for table in root.iter(tag("tbl")):
        row = table.find(tag("tr"))
        if row is not None:
            flag = row.find(tag("trPr") + "/" + tag("tblHeader"))
            if flag is None or flag.get(tag("val"), "true") in ("0", "false", "off"):
                add("medium", "table_no_header_row", "Table first row is not marked as header (w:tblHeader missing)")
    for link in root.iter(tag("hyperlink")):
        label = text_of(link).strip()
        if label.casefold() in {"here", "click here", "link", "this link"}:
            add("medium", "hyperlink_nondescriptive", f"Non-descriptive hyperlink text: '{label}'")
        if re.fullmatch(r"https?://\S+", label, re.IGNORECASE):
            add("low", "hyperlink_raw_url", "Hyperlink display text is a raw URL (often less accessible)", text=label[:120])
    return findings


def audit_docx(path):
    package = Package(path)
    findings = [finding for part in package.stories() for finding in inspect_story(package.xml(part), part)]
    return {"file": str(path), "counts": {level: sum(f["severity"] == level for f in findings) for level in ("high", "medium", "low")}, "findings": findings}


def apply_fixes(in_docx, out_docx, fix_image_alt, fix_table_headers):
    package = Package(in_docx)
    stats = {"image_alt_filled": 0, "table_headers_set": 0}
    for part in package.stories():
        root = package.xml(part)
        before = sum(stats.values())
        if fix_image_alt == "from_filename":
            folder, name = posixpath.split(part)
            relpath = posixpath.join(folder, "_rels", name + ".rels")
            targets = {node.get("Id"): node.get("Target", "") for node in package.xml(relpath)} if relpath in package.parts else {}
            for drawing in root.iter(tag("drawing")):
                properties = drawing.find(".//{" + WP + "}docPr")
                if properties is None or any(properties.get(key, "").strip() for key in ("descr", "title")):
                    continue
                blip = drawing.find(".//{" + DRAWING + "}blip")
                target = targets.get(blip.get("{" + R + "}embed"), "") if blip is not None else ""
                properties.set("descr", "Image: " + posixpath.basename(target) if target else "Image")
                stats["image_alt_filled"] += 1
        if fix_table_headers == "first_row":
            for table in root.iter(tag("tbl")):
                row = table.find(tag("tr"))
                if row is None:
                    continue
                properties = row.find(tag("trPr"))
                if properties is None:
                    properties = element("trPr")
                    row.insert(0, properties)
                flag = properties.find(tag("tblHeader"))
                if flag is None:
                    flag = element("tblHeader")
                    properties.append(flag)
                    stats["table_headers_set"] += 1
                elif flag.get(tag("val"), "true") in ("0", "false", "off"):
                    flag.set(tag("val"), "true")
                    stats["table_headers_set"] += 1
        if sum(stats.values()) != before:
            package.put_xml(part, root)
    package.save(out_docx)
    return stats


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("in_docx")
    cli.add_argument("--out_json")
    cli.add_argument("--out")
    cli.add_argument("--fix_image_alt", choices=("from_filename",))
    cli.add_argument("--fix_table_headers", choices=("first_row",))
    options = cli.parse_args()
    source = options.in_docx
    if options.fix_image_alt or options.fix_table_headers:
        if not options.out:
            raise SystemExit("--out is required when applying fixes")
        stats = apply_fixes(source, options.out, options.fix_image_alt, options.fix_table_headers)
        print(f"[OK] wrote {options.out} | {stats}")
        source = options.out
    report = audit_docx(source)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if options.out_json:
        Path(options.out_json).write_text(encoded + "\n", encoding="utf-8")
        print(f"[a11y] wrote report -> {options.out_json} | " + " ".join(f"{key}={value}" for key, value in report["counts"].items()))
    else:
        print(encoded)
    raise SystemExit(int(report["counts"]["high"] > 0))


if __name__ == "__main__":
    main()
