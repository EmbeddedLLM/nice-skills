#!/usr/bin/env python3
"""Add a diagonal VML text stamp to the lowest-numbered DOCX header.

Usage: watermark_add.py draft.docx --text DRAFT --out marked.docx
Requires lxml. If no header exists, creates a default header for the first
section and registers it without round-tripping the document through an editor.
This does not stamp every section/first/even-page variant. Rendering differs
between Word and LibreOffice; inspect the final pages before relying on it.
"""
import argparse
import re

from word_package import DOCUMENT, Package, R, W, X, element, tag

VML = "urn:schemas-microsoft-com:vml"


def add_watermark(in_docx, out_docx, text):
    package = Package(in_docx)
    headers = [(int(m[1]), name) for name in package.parts if (m := re.fullmatch(r"word/header(\d+)\.xml", name))]
    if headers:
        name = min(headers)[1]
        header = package.xml(name)
    else:
        name = "word/header1.xml"
        header = X.Element(tag("hdr"), nsmap={"w": W, "v": VML})
        document = package.xml(DOCUMENT)
        section = document.find(".//" + tag("sectPr"))
        if section is None:
            body = document.find(tag("body"))
            if body is None:
                raise ValueError("Document has no body")
            section = element("sectPr")
            body.append(section)
        if any(node.get(tag("type")) == "default" for node in section.findall(tag("headerReference"))):
            raise ValueError("Section already references a nonstandard default header; edit it in a compatible editor")
        reference = element("headerReference", type="default")
        reference.set("{" + R + "}id", package.register(name, "header"))
        section.insert(0, reference)
        package.put_xml(DOCUMENT, document)
    paragraph = element("p")
    run = element("r")
    picture = element("pict")
    # Distinct shape IDs permit repeated stamps without introducing duplicate IDs.
    used = {node.get("id") for node in header.iter()}
    serial = 1
    while f"Watermark{serial}" in used:
        serial += 1
    shape = X.SubElement(picture, "{" + VML + "}shape", {
        "id": f"Watermark{serial}", "type": "#_x0000_t136", "fillcolor": "#C0C0C0", "stroked": "f",
        "style": "position:absolute;width:468pt;height:468pt;rotation:315;z-index:-251654144;mso-position-horizontal:center;mso-position-vertical:center",
    })
    for local, attributes in (("fill", {"opacity": "0.15"}),
                              ("path", {"textpathok": "t"}),
                              ("textpath", {"on": "t", "string": text, "style": 'font-family:"Calibri";font-size:1pt'})):
        X.SubElement(shape, "{" + VML + "}" + local, attributes)
    run.append(picture)
    paragraph.append(run)
    header.append(paragraph)
    package.put_xml(name, header)
    package.save(out_docx)
    print(f"[OK] wrote {out_docx} (patched {name})")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("in_docx")
    cli.add_argument("--out", required=True)
    cli.add_argument("--text", required=True)
    options = cli.parse_args()
    add_watermark(options.in_docx, options.out, options.text)


if __name__ == "__main__":
    main()
