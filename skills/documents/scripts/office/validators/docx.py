"""DOCX-specific checks on top of the shared package validator.

Covers the wordprocessingml pitfalls that corrupt or misrender documents:
unpreserved boundary whitespace, text markup misplaced inside tracked
insertions/deletions, out-of-range paragraph identifiers, and comment
markers that do not pair up with entries in the comments part.
"""

from __future__ import annotations

import random
import re
import tempfile
import zipfile
from pathlib import Path

import lxml.etree

from ..helpers import safe_extract
from .base import NS_XML, PackageValidator

NS_WORD = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
NS_W15 = "http://schemas.microsoft.com/office/word/2012/wordml"
NS_W16CID = "http://schemas.microsoft.com/office/word/2016/wordml/cid"
NS_W16CEX = "http://schemas.microsoft.com/office/word/2018/wordml/cex"

_EDGE_WHITESPACE = re.compile(r"^[ \t\n\r]|[ \t\n\r]$")
_PARA_ID_MAX = 0x80000000
_DURABLE_ID_MAX = 0x7FFFFFFF
_DURABLE_ID_ATTRS = (f"{{{NS_W16CID}}}durableId", f"{{{NS_W16CEX}}}durableId")


class DOCXSchemaValidator(PackageValidator):
    """Validate an unpacked DOCX package directory."""

    PART_SCHEMAS = {
        "[Content_Types].xml": "ecma376-opc/opc-contentTypes.xsd",
        ".rels": "ecma376-opc/opc-relationships.xsd",
        "app.xml": "ecma376-transitional/shared-documentPropertiesExtended.xsd",
        "custom.xml": "ecma376-transitional/shared-documentPropertiesCustom.xsd",
        "people.xml": "ms-open-specs/wml-2012.xsd",
        "commentsExtended.xml": "ms-open-specs/wml-2012.xsd",
        "commentsIds.xml": "ms-open-specs/wml-cid-2016.xsd",
        "commentsExtensible.xml": "ms-open-specs/wml-cex-2018.xsd",
        "chart": "ecma376-transitional/dml-chart.xsd",
        "theme": "ecma376-transitional/dml-main.xsd",
        "word": "ecma376-transitional/wml.xsd",
    }

    def validate(self) -> bool:
        if not self.check_well_formed():
            return False
        verdicts = [
            self.check_namespaces(),
            self.check_id_uniqueness(),
            self.check_part_references(),
            self.check_content_types(),
            self.check_xsd_delta(),
            self.check_whitespace_preservation(),
            self.check_deleted_markup(),
            self.check_inserted_markup(),
            self.check_relationship_id_refs(),
            self.check_revision_id_ranges(),
            self.check_comment_anchoring(),
        ]
        self.report_paragraph_delta()
        return all(verdicts)

    # ------------------------------------------------------------- checks

    def _document_parts(self, name="document.xml"):
        for part in self.xml_files:
            if part.name == name:
                yield part

    def check_whitespace_preservation(self) -> bool:
        problems = []
        for part in self._document_parts():
            root = lxml.etree.parse(str(part)).getroot()
            for element in root.iter(f"{{{NS_WORD}}}t"):
                text = element.text or ""
                if not _EDGE_WHITESPACE.search(text):
                    continue
                if element.get(f"{{{NS_XML}}}space") == "preserve":
                    continue
                preview = repr(text)[:50]
                problems.append(
                    f"  {self._relative(part)}: line {element.sourceline}:"
                    f" <w:t> loses boundary whitespace without"
                    f" xml:space='preserve': {preview}"
                )
        return self.report(
            "whitespace preservation", problems,
            "boundary whitespace is preserved everywhere",
        )

    def check_deleted_markup(self) -> bool:
        """<w:del> content must use delText/delInstrText, never w:t/w:instrText."""
        problems = []
        for part in self._document_parts():
            root = lxml.etree.parse(str(part)).getroot()
            scope = {"w": NS_WORD}
            for element in root.xpath(".//w:del//w:t", namespaces=scope):
                problems.append(
                    f"  {self._relative(part)}: line {element.sourceline}:"
                    f" <w:t> inside <w:del> (want <w:delText>):"
                    f" {repr(element.text or '')[:50]}"
                )
            for element in root.xpath(".//w:del//w:instrText", namespaces=scope):
                problems.append(
                    f"  {self._relative(part)}: line {element.sourceline}:"
                    f" <w:instrText> inside <w:del> (want <w:delInstrText>):"
                    f" {repr(element.text or '')[:50]}"
                )
        return self.report(
            "deletion markup", problems, "no live text elements inside deletions"
        )

    def check_inserted_markup(self) -> bool:
        """<w:ins> must not contain <w:delText> outside a nested <w:del>."""
        problems = []
        for part in self._document_parts():
            root = lxml.etree.parse(str(part)).getroot()
            scope = {"w": NS_WORD}
            misplaced = root.xpath(
                ".//w:ins//w:delText[not(ancestor::w:del)]", namespaces=scope
            )
            for element in misplaced:
                problems.append(
                    f"  {self._relative(part)}: line {element.sourceline}:"
                    f" <w:delText> inside <w:ins>: {repr(element.text or '')[:50]}"
                )
        return self.report(
            "insertion markup", problems, "no deleted-text elements inside insertions"
        )

    def check_revision_id_ranges(self) -> bool:
        problems = []
        para_attr = f"{{{NS_W14}}}paraId"
        durable_attr = f"{{{NS_W16CID}}}durableId"
        for part in self.xml_files:
            try:
                root = lxml.etree.parse(str(part)).getroot()
            except lxml.etree.XMLSyntaxError:
                continue
            in_numbering = part.name == "numbering.xml"
            for element in root.iter():
                value = element.get(para_attr)
                if value:
                    try:
                        if int(value, 16) >= _PARA_ID_MAX:
                            problems.append(
                                f"  {part.name}: line {element.sourceline}:"
                                f" paraId={value} exceeds 0x7FFFFFFF"
                            )
                    except ValueError:
                        problems.append(
                            f"  {part.name}: line {element.sourceline}:"
                            f" paraId={value} is not hexadecimal"
                        )
                value = element.get(durable_attr)
                if value:
                    radix = 10 if in_numbering else 16
                    try:
                        if int(value, radix) >= _DURABLE_ID_MAX:
                            problems.append(
                                f"  {part.name}: line {element.sourceline}:"
                                f" durableId={value} exceeds the allowed range"
                            )
                    except ValueError:
                        kind = "decimal" if in_numbering else "hexadecimal"
                        problems.append(
                            f"  {part.name}: line {element.sourceline}:"
                            f" durableId={value} is not {kind}"
                        )
        return self.report(
            "revision id ranges", problems,
            "paraId/durableId values are within range",
        )

    def check_comment_anchoring(self) -> bool:
        document_part = next(
            (p for p in self.xml_files if p.name == "document.xml" and "word" in p.parts),
            None,
        )
        comments_part = next(
            (p for p in self.xml_files if p.name == "comments.xml"), None
        )
        if document_part is None:
            if self.verbose:
                print("PASSED - comment anchoring: no document.xml, nothing to check")
            return True

        problems = []
        try:
            document = lxml.etree.parse(str(document_part)).getroot()
            scope = {"w": NS_WORD}
            starts = self._marker_ids(document, scope, "commentRangeStart")
            ends = self._marker_ids(document, scope, "commentRangeEnd")
            refs = self._marker_ids(document, scope, "commentReference")

            for cid in sorted(ends - starts, key=_numeric):
                problems.append(
                    f'  document.xml: commentRangeEnd id="{cid}" has no matching start'
                )
            for cid in sorted(starts - ends, key=_numeric):
                problems.append(
                    f'  document.xml: commentRangeStart id="{cid}" has no matching end'
                )

            if comments_part is not None:
                comments = lxml.etree.parse(str(comments_part)).getroot()
                known = {
                    element.get(f"{{{NS_WORD}}}id")
                    for element in comments.iter(f"{{{NS_WORD}}}comment")
                }
                anchored = self._anchored_comment_ids(comments_part)
                for cid in sorted(known - refs - anchored, key=_numeric):
                    problems.append(
                        f"  comments.xml: comment {cid} is never referenced"
                        " from the body"
                    )
                for cid in sorted((starts | ends | refs) - known, key=_numeric):
                    if cid:
                        problems.append(
                            f'  document.xml: marker id="{cid}" names a comment'
                            " that does not exist"
                        )
            elif starts or ends or refs:
                problems.append(
                    "  document.xml carries comment markers but the package has"
                    " no comments.xml"
                )
        except lxml.etree.XMLSyntaxError as exc:
            problems.append(f"  comment check aborted: {exc}")
        return self.report(
            "comment anchoring", problems, "comment markers and entries are paired"
        )

    @staticmethod
    def _marker_ids(root, scope, name) -> set:
        return {
            element.get(f"{{{NS_WORD}}}id")
            for element in root.xpath(f".//w:{name}", namespaces=scope)
        }

    def _anchored_comment_ids(self, comments_part: Path) -> set:
        """Ids of reply comments, which inherit their parent's anchor."""
        extended_part = self.unpacked_dir / "word" / "commentsExtended.xml"
        if not extended_part.is_file():
            return set()
        extended = lxml.etree.parse(str(extended_part)).getroot()
        reply_paras = {
            element.get(f"{{{NS_W15}}}paraId")
            for element in extended
            if element.get(f"{{{NS_W15}}}paraIdParent")
        }
        if not reply_paras:
            return set()
        comments = lxml.etree.parse(str(comments_part)).getroot()
        anchored = set()
        for comment in comments.iter(f"{{{NS_WORD}}}comment"):
            for para in comment.iter(f"{{{NS_WORD}}}p"):
                if para.get(f"{{{NS_W14}}}paraId") in reply_paras:
                    anchored.add(comment.get(f"{{{NS_WORD}}}id"))
                    break
        return anchored

    def report_paragraph_delta(self) -> None:
        current = self._paragraph_count(self.unpacked_dir)
        if self.original_file is None:
            print(f"\nParagraphs: {current}")
            return
        baseline = self._paragraph_count_in_original()
        delta = current - baseline
        sign = f"+{delta}" if delta > 0 else str(delta)
        print(f"\nParagraphs: {baseline} -> {current} ({sign})")

    def _paragraph_count(self, directory: Path) -> int:
        document_part = Path(directory) / "word" / "document.xml"
        if not document_part.is_file():
            return 0
        try:
            root = lxml.etree.parse(str(document_part)).getroot()
        except (lxml.etree.XMLSyntaxError, OSError) as exc:
            print(f"Could not count paragraphs in {document_part}: {exc}")
            return 0
        return len(root.findall(f".//{{{NS_WORD}}}p"))

    def _paragraph_count_in_original(self) -> int:
        if self.original_file is None:
            return 0
        try:
            with tempfile.TemporaryDirectory() as staging:
                with zipfile.ZipFile(self.original_file, "r") as archive:
                    safe_extract(archive, Path(staging))
                return self._paragraph_count(Path(staging))
        except (zipfile.BadZipFile, ValueError, OSError) as exc:
            print(f"Could not count paragraphs in {self.original_file}: {exc}")
            return 0

    # ------------------------------------------------------------ repairs

    def repair(self) -> int:
        return super().repair() + self.repair_durable_ids()

    def repair_durable_ids(self) -> int:
        """Renumber out-of-range or malformed durableId attributes.

        The same broken value maps to the same replacement across the whole
        package, while duplicates inside one part each get a fresh id.
        """
        fixed = 0
        renames: dict = {}
        for part in self.xml_files:
            try:
                tree = lxml.etree.parse(str(part))
            except (lxml.etree.XMLSyntaxError, OSError):
                continue
            in_numbering = part.name == "numbering.xml"
            radix = 10 if in_numbering else 16
            seen_here: set = set()
            touched = False
            for element in tree.getroot().iter():
                for attr in _DURABLE_ID_ATTRS:
                    old = element.get(attr)
                    if old is None:
                        continue
                    try:
                        key = int(old, radix)
                        broken = key >= _DURABLE_ID_MAX
                    except ValueError:
                        key = old
                        broken = True
                    if not broken:
                        continue
                    if key in seen_here:
                        new_value = random.randint(1, _DURABLE_ID_MAX - 1)
                    else:
                        seen_here.add(key)
                        new_value = renames.setdefault(
                            key, random.randint(1, _DURABLE_ID_MAX - 1)
                        )
                    rendered = str(new_value) if in_numbering else f"{new_value:08X}"
                    element.set(attr, rendered)
                    print(
                        f"  Repaired: {part.name}: durableId {old} -> {rendered}"
                    )
                    fixed += 1
                    touched = True
            if touched:
                tree.write(
                    str(part), xml_declaration=True, encoding="UTF-8",
                    standalone=True,
                )
        return fixed


def _numeric(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    raise SystemExit("DOCXSchemaValidator is a library; run office/validate.py instead.")
