#!/usr/bin/env python3
"""Add deterministic internal navigation to a DOCX.

Word's table of contents is a field, and fields need a GUI editor to refresh —
awkward in an automated pipeline. This builds a *static* contents section out of
internal hyperlinks (`<w:hyperlink w:anchor="…">`, no relationship, no field)
plus the bookmarks they target:

* `Top`, `Bottom`, and `TOC` bookmarks;
* a bookmark on each heading (`sec001`, `sec002`, …), recognised by
  `Heading1/2/3` style *or* by `w:outlineLvl`, so documents that never adopted
  heading styles still work;
* a contents section listing every heading, indented by level;
* a "Back to TOC" link appended to each heading;
* an optional quick-links bar with Top / Bottom / TOC and any `tblN` / `figN`
  caption bookmarks that already exist.

Only `word/document.xml` is touched.

    python scripts/internal_nav.py in.docx --out out.docx
    python scripts/internal_nav.py in.docx --out out.docx --levels 1 2
    python scripts/internal_nav.py in.docx --out out.docx --no_quicklinks
"""

from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path

from lxml import etree

try:
    from docx_ooxml_patch import unzip_docx, zip_docx
except Exception:
    # Standalone fallback so a lone copy of this script still runs.
    import os
    import shutil
    import zipfile

    def unzip_docx(docx_path: Path, out_dir: Path) -> None:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(docx_path, "r") as archive:
            archive.extractall(out_dir)

    def zip_docx(in_dir: Path, out_docx_path: Path) -> None:
        if out_docx_path.exists():
            out_docx_path.unlink()
        with zipfile.ZipFile(out_docx_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for root, _dirs, files in os.walk(in_dir):
                for name in files:
                    absolute = Path(root) / name
                    archive.write(absolute, absolute.relative_to(in_dir).as_posix())


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS, "r": R_NS}

DOCUMENT_PART = "word/document.xml"
HYPERLINK_STYLE = "Hyperlink"
TOC_HEADING_STYLE = "Heading1"
INDENT_STEP = "  "
SEPARATOR = " | "
HEADING_STYLE_SPACED = re.compile(r"Heading\s*(\d+)")
HEADING_STYLE_JOINED = re.compile(r"Heading(\d+)")
FIGURE_BOOKMARK = re.compile(r"fig\d+")
TABLE_BOOKMARK = re.compile(r"tbl\d+")


def qn(local: str) -> str:
    return f"{{{W_NS}}}{local}"


def preserve_spaces(text_node: etree._Element) -> None:
    text = text_node.text or ""
    if text and (text.startswith(" ") or text.endswith(" ")):
        text_node.set(f"{{{XML_NS}}}space", "preserve")


def read_part(path: Path) -> etree._ElementTree:
    return etree.parse(str(path), etree.XMLParser(remove_blank_text=False))


def write_part(tree: etree._ElementTree, path: Path) -> None:
    tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone="yes")


def paragraph_text(paragraph: etree._Element) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()


def paragraph_style(paragraph: etree._Element) -> str | None:
    style = paragraph.find("w:pPr/w:pStyle", namespaces=NS)
    return None if style is None else style.get(qn("val"))


def outline_level(paragraph: etree._Element) -> int | None:
    """Word's 0-based outline level, when the paragraph declares one."""
    element = paragraph.find("w:pPr/w:outlineLvl", namespaces=NS)
    if element is None:
        return None
    value = element.get(qn("val"))
    return int(value) if value is not None and value.isdigit() else None


def heading_level(paragraph: etree._Element) -> int | None:
    """Outline level wins; otherwise read the Heading style id."""
    declared = outline_level(paragraph)
    if declared is not None:
        return declared + 1

    style = paragraph_style(paragraph) or ""
    for pattern in (HEADING_STYLE_SPACED, HEADING_STYLE_JOINED):
        match = pattern.fullmatch(style)
        if match:
            return int(match.group(1))
    return None


def highest_bookmark_id(root: etree._Element) -> int:
    highest = 0
    for tag in ("bookmarkStart", "bookmarkEnd"):
        for bookmark in root.findall(f".//w:{tag}", namespaces=NS):
            value = bookmark.get(qn("id"))
            if value and value.isdigit():
                highest = max(highest, int(value))
    return highest


def bookmark_names(root: etree._Element) -> set[str]:
    return {
        name
        for bookmark in root.findall(".//w:bookmarkStart", namespaces=NS)
        if (name := bookmark.get(qn("name")))
    }


def caption_bookmarks(root: etree._Element) -> tuple[list[str], list[str]]:
    """(figure names, table names) already present, sorted."""
    names = sorted(bookmark_names(root))
    return ([n for n in names if FIGURE_BOOKMARK.fullmatch(n)],
            [n for n in names if TABLE_BOOKMARK.fullmatch(n)])


def text_run(text: str) -> etree._Element:
    run = etree.Element(qn("r"))
    node = etree.SubElement(run, qn("t"))
    node.text = text
    preserve_spaces(node)
    return run


def styled_paragraph(text: str, style: str | None = None) -> etree._Element:
    paragraph = etree.Element(qn("p"))
    if style is not None:
        etree.SubElement(etree.SubElement(paragraph, qn("pPr")), qn("pStyle")).set(qn("val"), style)
    paragraph.append(text_run(text))
    return paragraph


def internal_link(anchor: str, label: str) -> etree._Element:
    """A hyperlink to a bookmark in this document, styled as a link."""
    hyperlink = etree.Element(qn("hyperlink"))
    hyperlink.set(qn("anchor"), anchor)

    run = etree.SubElement(hyperlink, qn("r"))
    etree.SubElement(etree.SubElement(run, qn("rPr")), qn("rStyle")).set(qn("val"), HYPERLINK_STYLE)

    node = etree.SubElement(run, qn("t"))
    node.text = label
    preserve_spaces(node)
    return hyperlink


def bookmark_paragraph(paragraph: etree._Element, name: str, bookmark_id: int) -> None:
    """Wrap a paragraph in a bookmark, unless that name is already there."""
    for existing in paragraph.findall(".//w:bookmarkStart", namespaces=NS):
        if existing.get(qn("name")) == name:
            return

    start = etree.Element(qn("bookmarkStart"))
    start.set(qn("id"), str(bookmark_id))
    start.set(qn("name"), name)
    end = etree.Element(qn("bookmarkEnd"))
    end.set(qn("id"), str(bookmark_id))

    paragraph.insert(0, start)
    paragraph.append(end)


class NavigationBuilder:
    """Allocates bookmark ids and assembles the navigation blocks."""

    def __init__(self, root: etree._Element, levels: list[int], toc_title: str,
                 add_quicklinks: bool, add_back_links: bool, add_top_bottom: bool) -> None:
        self.root = root
        self.body = root.find("w:body", namespaces=NS)
        self.levels = levels
        self.toc_title = toc_title
        self.add_quicklinks = add_quicklinks
        self.add_back_links_enabled = add_back_links
        self.add_top_bottom = add_top_bottom
        self.headings: list[tuple[int, str, str, etree._Element]] = []

        if self.body is None:
            raise RuntimeError("word/document.xml missing w:body")

        self.paragraphs = self.body.findall("w:p", namespaces=NS)
        if not self.paragraphs:
            raise RuntimeError("No paragraphs found in document body")

        self.next_bookmark_id = highest_bookmark_id(root) + 1

    def take_bookmark_id(self) -> int:
        allocated = self.next_bookmark_id
        self.next_bookmark_id += 1
        return allocated

    def add_edge_bookmarks(self) -> None:
        if not self.add_top_bottom:
            return
        bookmark_paragraph(self.paragraphs[0], "Top", self.take_bookmark_id())
        bookmark_paragraph(self.paragraphs[-1], "Bottom", self.take_bookmark_id())

    def collect_headings(self) -> None:
        for paragraph in self.paragraphs:
            level = heading_level(paragraph)
            if level is None or level not in self.levels:
                continue
            title = paragraph_text(paragraph)
            if not title:
                continue
            name = f"sec{len(self.headings) + 1:03d}"
            bookmark_paragraph(paragraph, name, self.take_bookmark_id())
            self.headings.append((level, title, name, paragraph))

    def contents_heading(self) -> etree._Element:
        heading = styled_paragraph(self.toc_title, style=TOC_HEADING_STYLE)
        bookmark_paragraph(heading, "TOC", self.take_bookmark_id())
        return heading

    def contents_entry(self, level: int, title: str, name: str) -> etree._Element:
        entry = etree.Element(qn("p"))
        indent = INDENT_STEP * (max(1, level) - 1)
        if indent:
            entry.append(text_run(indent))
        entry.append(internal_link(name, title))
        return entry

    def quick_links_bar(self) -> etree._Element:
        figures, tables = caption_bookmarks(self.root)
        bar = etree.Element(qn("p"))

        bar.append(internal_link("Top", "Top"))
        for anchor, label in (("Bottom", "Bottom"), ("TOC", "TOC")):
            bar.append(text_run(SEPARATOR))
            bar.append(internal_link(anchor, label))

        for name in tables:
            bar.append(text_run(SEPARATOR))
            bar.append(internal_link(name, f"Table {name.replace('tbl', '')}"))
        for name in figures:
            bar.append(text_run(SEPARATOR))
            bar.append(internal_link(name, f"Figure {name.replace('fig', '')}"))

        return bar

    def add_back_links(self) -> None:
        """Append a space and a "Back to TOC" link to every heading."""
        for _level, _title, _name, paragraph in self.headings:
            paragraph.append(text_run(" "))
            paragraph.append(internal_link("TOC", "Back to TOC"))

    def build(self) -> None:
        self.add_edge_bookmarks()
        self.collect_headings()

        blocks = [self.contents_heading()]
        blocks += [self.contents_entry(level, title, name)
                   for level, title, name, _paragraph in self.headings]
        blocks.append(styled_paragraph(""))

        if self.add_quicklinks:
            blocks.append(self.quick_links_bar())
            blocks.append(styled_paragraph(""))

        for offset, block in enumerate(blocks):
            self.body.insert(offset, block)

        if self.add_back_links_enabled:
            self.add_back_links()


def patch_document(docx_in: Path, docx_out: Path, levels: list[int], toc_title: str,
                   add_quicklinks: bool, add_back_to_toc: bool, add_top_bottom: bool) -> None:
    with tempfile.TemporaryDirectory(prefix="docx_nav_") as staging:
        unzipped = Path(staging) / "unz"
        unzip_docx(docx_in, unzipped)

        document_part = unzipped / DOCUMENT_PART
        tree = read_part(document_part)

        NavigationBuilder(
            tree.getroot(),
            levels=levels,
            toc_title=toc_title,
            add_quicklinks=add_quicklinks,
            add_back_links=add_back_to_toc,
            add_top_bottom=add_top_bottom,
        ).build()

        write_part(tree, document_part)
        zip_docx(unzipped, docx_out)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Add internal navigation links/bookmarks and a static TOC"
    )
    ap.add_argument("input_docx")
    ap.add_argument("--out", required=True)
    ap.add_argument("--toc_title", default="Table of Contents")
    ap.add_argument("--levels", nargs="+", type=int, default=[1, 2, 3],
                    help="Heading levels to include")
    ap.add_argument("--no_quicklinks", action="store_true", help="Disable quick links bar")
    ap.add_argument("--no_back_to_toc", action="store_true",
                    help="Do not add back-to-TOC links on headings")
    ap.add_argument("--no_top_bottom", action="store_true",
                    help="Do not add Top/Bottom bookmarks")
    args = ap.parse_args()

    patch_document(
        docx_in=Path(args.input_docx),
        docx_out=Path(args.out),
        levels=list(args.levels),
        toc_title=args.toc_title,
        add_quicklinks=not args.no_quicklinks,
        add_back_to_toc=not args.no_back_to_toc,
        add_top_bottom=not args.no_top_bottom,
    )
    print(f"[OK] wrote {args.out}")


if __name__ == "__main__":
    main()
