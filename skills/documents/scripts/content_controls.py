#!/usr/bin/env python3
"""List, create, or fill plain-text Word content controls (lxml required).

Examples:
  content_controls.py form.docx wrap_placeholders --output controls.docx
  content_controls.py controls.docx fill --set CLIENT=Example --output filled.docx
  content_controls.py filled.docx list --json

Wraps {{TAG}} across adjacent text nodes in a run. Split-run tokens stay intact.
Existing controls are not nested. Nontext run children and formatting survive.
Filling replaces a selected control's content; rich controls require other tools.
Default scope includes numbered headers/footers; --no_headers_footers limits it.
Invalid assignments fail before writing. Changes are saved atomically.
"""
import argparse
from copy import deepcopy
import json
from itertools import groupby
import re

from word_package import Package, element, tag, text_of, text_run

TOKEN = re.compile(r"\{\{([A-Za-z0-9_-]+)\}\}")


def wrap(root):
    count = 0
    for run in list(root.iter(tag("r"))):
        if any(parent.tag == tag("sdt") for parent in run.iterancestors()):
            continue
        contents = []
        for is_text, siblings in groupby(run, key=lambda node: node.tag == tag("t")):
            siblings = list(siblings)
            if is_text:
                combined = element("t")
                combined.text = "".join(node.text or "" for node in siblings)
                contents.append(combined)
            else:
                contents.extend(siblings)
        if not any(node.tag == tag("t") and TOKEN.search(node.text or "") for node in contents):
            continue
        properties = run.find(tag("rPr"))
        fragments = []
        for child in contents:
            if child.tag == tag("rPr"):
                continue
            if child.tag != tag("t"):
                fragment = element("r")
                if properties is not None:
                    fragment.append(deepcopy(properties))
                fragment.append(deepcopy(child))
                fragments.append(fragment)
                continue
            text = child.text or ""
            cursor = 0
            for match in TOKEN.finditer(text):
                if match.start() > cursor:
                    fragments.append(text_run(text[cursor:match.start()], properties))
                control = element("sdt")
                settings = element("sdtPr")
                settings.extend([element("tag", val=match[1]), element("alias", val=match[1]), element("text")])
                content = element("sdtContent")
                content.append(text_run(match[0], properties))
                control.extend([settings, content])
                fragments.append(control)
                cursor = match.end()
            if cursor < len(text):
                fragments.append(text_run(text[cursor:], properties))
        parent = run.getparent()
        position = parent.index(run)
        parent.remove(run)
        for offset, fragment in enumerate(fragments):
            parent.insert(position + offset, fragment)
        count += 1
    return count


def property_value(control, name):
    node = control.find(tag("sdtPr") + "/" + tag(name))
    return node.get(tag("val"), "") if node is not None else ""


def fill(root, values):
    count = 0
    for control in root.iter(tag("sdt")):
        key = property_value(control, "tag")
        content = control.find(tag("sdtContent"))
        if key not in values or content is None:
            continue
        # Refuse to flatten nested structures that the plain-text contract cannot preserve.
        if content.find(".//" + tag("tbl")) is not None or content.find(".//" + tag("sdt")) is not None:
            raise ValueError(f"Control {key!r} is structured; plain-text fill would discard its structure")
        formatting = content.find(".//" + tag("rPr"))
        paragraphs = content.findall(tag("p"))
        paragraph_settings = paragraphs[0].find(tag("pPr")) if paragraphs else None
        new_run = text_run(values[key], formatting)
        for child in list(content):
            content.remove(child)
        if paragraphs:
            paragraph = element("p")
            if paragraph_settings is not None:
                paragraph.append(deepcopy(paragraph_settings))
            paragraph.append(new_run)
            content.append(paragraph)
        else:
            content.append(new_run)
        count += 1
    return count


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("docx")
    actions = cli.add_subparsers(dest="action", required=True)
    for action in ("list", "wrap_placeholders", "fill"):
        parser = actions.add_parser(action)
        parser.add_argument("--no_headers_footers", action="store_true")
        if action == "list":
            parser.add_argument("--json", action="store_true")
        else:
            parser.add_argument("--output", required=True)
        if action == "fill":
            parser.add_argument("--set", action="append", default=[])
    options = cli.parse_args()
    assignments = {}
    if options.action == "fill":
        if not options.set:
            cli.error("fill requires at least one --set TAG=VALUE")
        for assignment in options.set:
            key, separator, value = assignment.partition("=")
            if not separator or not key.strip():
                cli.error(f"Invalid --set {assignment!r} (expected TAG=VALUE with nonempty TAG)")
            assignments[key.strip()] = value
    package = Package(options.docx)
    rows = []
    total = 0
    for part in package.stories(not options.no_headers_footers):
        root = package.xml(part)
        if options.action == "list":
            for control in root.iter(tag("sdt")):
                rows.append({"part": part, "tag": property_value(control, "tag"),
                             "alias": property_value(control, "alias"), "text": text_of(control)})
        else:
            changed = wrap(root) if options.action == "wrap_placeholders" else fill(root, assignments)
            total += changed
            if changed:
                package.put_xml(part, root)
    if options.action == "list":
        if options.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        elif not rows:
            print("[content_controls] no SDTs found")
        else:
            for row in rows:
                print(f"- {row['part']}: tag={row['tag'] or '(no-tag)'} alias={row['alias']} text={row['text']}")
        return
    package.save(options.output)
    message = f"wrapped placeholders in {total} run(s)" if options.action == "wrap_placeholders" else f"filled {total} SDT(s)"
    print(f"[content_controls] {message}; wrote {options.output}")


if __name__ == "__main__":
    main()
