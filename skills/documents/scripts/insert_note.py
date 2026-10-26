#!/usr/bin/env python3
"""Create a footnote/endnote and its document reference using lxml.

Usage: insert_note.py report.docx --kind footnote --text 'Source note' --out noted.docx
The first marker occurrence in one text node becomes a native note reference.
If absent, adds a paragraph before the final section properties. Split-run
markers are not matched. Existing notes remain intact; new IDs exceed existing
positive IDs. Required relationships and content-type declarations are added.
"""
import argparse

from word_package import DOCUMENT, Package, W, X, element, tag, text_run


def insert_note(in_docx, out_docx, kind_label, marker, text):
    if kind_label not in ("footnote", "endnote"):
        raise ValueError("kind must be footnote or endnote")
    if not marker:
        raise ValueError("marker must not be empty")
    package = Package(in_docx)
    document = package.xml(DOCUMENT)
    body = document.find(tag("body"))
    if body is None:
        raise ValueError("No w:body in document.xml")
    name = package.document_part(kind_label + "s", f"word/{kind_label}s.xml")
    if name in package.parts:
        notes = package.xml(name)
    else:
        notes = X.Element(tag(kind_label + "s"), nsmap={"w": W})
        for identifier, separator in ((-1, "separator"), (0, "continuationSeparator")):
            entry = element(kind_label, id=identifier, type=separator)
            paragraph = element("p")
            run = element("r")
            run.append(element(separator))
            paragraph.append(run)
            entry.append(paragraph)
            notes.append(entry)
    ids = [int(n.get(tag("id"))) for n in notes if n.get(tag("id"), "").lstrip("-").isdigit()]
    identifier = max([0, *ids]) + 1
    note = element(kind_label, id=identifier)
    paragraph = element("p")
    run = element("r")
    run.append(element(kind_label + "Ref"))
    paragraph.extend([run, text_run(" " + text)])
    note.append(paragraph)
    notes.append(note)
    reference = element(kind_label + "Reference", id=identifier)
    selected = next((n for n in body.iter(tag("t")) if marker in (n.text or "")), None)
    if selected is None:
        paragraph = element("p")
        run = element("r")
        run.append(reference)
        paragraph.append(run)
        index = len(body) - int(bool(len(body)) and body[-1].tag == tag("sectPr"))
        body.insert(index, paragraph)
    else:
        # Split only the selected text node, preserving siblings in the same run.
        run = selected.getparent()
        if run.tag != tag("r"):
            raise ValueError("Marker is not inside a Word run")
        prefix, suffix = selected.text.split(marker, 1)
        position = run.index(selected)
        run.remove(selected)
        replacements = [text_run(prefix)[0], reference, text_run(suffix)[0]]
        for offset, node in enumerate(replacements):
            run.insert(position + offset, node)
    package.put_xml(DOCUMENT, document)
    package.put_xml(name, notes)
    package.register(name, kind_label + "s")
    package.save(out_docx)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("in_docx")
    cli.add_argument("--kind", required=True, choices=("footnote", "endnote"))
    cli.add_argument("--text", required=True)
    cli.add_argument("--marker", default="[[NOTE]]")
    cli.add_argument("--out", required=True)
    options = cli.parse_args()
    insert_note(options.in_docx, options.out, options.kind, options.marker, options.text)
    print(f"[OK] inserted {options.kind} and wrote {options.out}")


if __name__ == "__main__":
    main()
