#!/usr/bin/env python3
"""Copy a template's styles, numbering, fonts, and theme into a target DOCX.

Usage: apply_template_styles.py --template brand.dotx --target draft.docx --out styled.docx
Requires lxml. Whole selected parts replace their target counterparts; shared
style/numbering IDs therefore take template definitions. Body and section XML
stay intact. Relationship-backed assets (embedded fonts, picture bullets) need a
full package merger: this tool refuses them before publishing an output.
"""
import argparse
import posixpath

from word_package import Package


def apply(template_path, target_path, out_path):
    template = Package(template_path)
    target = Package(target_path)
    selection = {"word/styles.xml": "styles", "word/numbering.xml": "numbering",
                 "word/fontTable.xml": "fontTable", "word/theme/theme1.xml": "theme"}
    for name, kind in selection.items():
        source_name = template.document_part(kind, name)
        destination_name = target.document_part(kind, name)
        if source_name not in template.parts:
            continue
        parent, filename = posixpath.split(source_name)
        dependencies = posixpath.join(parent, "_rels", filename + ".rels")
        if dependencies in template.parts and len(template.xml(dependencies)):
            raise ValueError(f"Template part {source_name} has relationships; use a full package merger")
        target.parts[destination_name] = template.parts[source_name]
        target.register(destination_name, kind)
    target.save(out_path)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for flag in ("template", "target", "out"):
        cli.add_argument("--" + flag, required=True)
    options = cli.parse_args()
    apply(options.template, options.target, options.out)
    print(f"[OK] wrote {options.out}")


if __name__ == "__main__":
    main()
