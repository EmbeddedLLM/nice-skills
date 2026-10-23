#!/usr/bin/env python3
"""Edit classic comments by ID using a JSON {"ops": [...]} patch.

Usage: comments_apply_patch.py review.docx edits.json --out revised.docx
Each operation accepts id and replace, append, and/or boolean resolved. Text is
split into nonempty trimmed paragraphs. When both are given, replacement runs
before append. Unknown IDs warn; missing comments.xml fails before writing.
Only classic w:done metadata is changed; modern thread state needs its own tool.
Dependencies: lxml and bundled word_package. Output replacement is atomic.
"""
import argparse
import datetime
import json
from pathlib import Path

from word_package import Package, element, tag, text_run


def apply_patch(in_docx, patch_path, out_docx):
    operations = json.loads(Path(patch_path).read_text(encoding="utf-8")).get("ops") or []
    if not isinstance(operations, list) or any(not isinstance(op, dict) for op in operations):
        raise ValueError("ops must be a list of objects")
    package = Package(in_docx)
    name = "word/comments.xml"
    if name not in package.parts:
        raise SystemExit("[comments_apply_patch] word/comments.xml not found")
    root = package.xml(name)
    index = {node.get(tag("id")): node for node in root.iter(tag("comment"))}
    touched = set()
    count = 0
    for operation in operations:
        if operation.get("id") is None:
            continue
        identifier = str(operation["id"])
        if identifier not in index:
            print(f"[warn] comment id {identifier} not found")
            continue
        comment = index[identifier]
        changed = False
        for action in ("replace", "append"):
            if operation.get(action) is None:
                continue
            if action == "replace":
                for paragraph in comment.findall(tag("p")):
                    comment.remove(paragraph)
            lines = [line.strip() for line in str(operation[action]).split("\n") if line.strip()]
            for line in lines or ([""] if action == "replace" else []):
                paragraph = element("p")
                paragraph.append(text_run(line))
                comment.append(paragraph)
            changed = True
        state = operation.get("resolved")
        if state is True or (state is False and tag("done") in comment.attrib):
            if state:
                comment.set(tag("done"), "1")
            else:
                del comment.attrib[tag("done")]
            comment.set(tag("date"), datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
            changed = True
        if changed:
            count += 1
            touched.add(identifier)
    if count:
        package.put_xml(name, root)
    package.save(out_docx)
    print(f"[OK] wrote {out_docx} (comments_touched={len(touched)} ops_applied={count})")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("in_docx")
    cli.add_argument("patch_json")
    cli.add_argument("--out", required=True)
    options = cli.parse_args()
    apply_patch(options.in_docx, options.patch_json, options.out)


if __name__ == "__main__":
    main()
