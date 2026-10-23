"""Detect body-text edits that were made without tracked changes.

Strategy: work out which <w:ins>/<w:del> elements are new relative to the
original document, undo exactly those, and compare the remaining body text
with the original.  Whatever still differs was edited without a tracked
change recording it.

Only word/document.xml is compared; headers, footers and notes live in
separate parts and are out of scope.
"""

from __future__ import annotations

import difflib
import tempfile
import zipfile
from pathlib import Path

import defusedxml.ElementTree as ET
from defusedxml.common import DefusedXmlException

from ..helpers import rendered_text, safe_extract

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE_ATTR = "{http://www.w3.org/XML/1998/namespace}space"


class RedliningValidator:
    """Compare an unpacked DOCX against its original for untracked edits."""

    def __init__(self, unpacked_dir, original_docx, verbose=False):
        self.unpacked_dir = Path(unpacked_dir)
        self.original_docx = Path(original_docx)
        self.verbose = bool(verbose)

    def repair(self) -> int:
        return 0  # untracked edits are reported, never auto-rewritten

    def validate(self) -> bool:
        edited_part = self.unpacked_dir / "word" / "document.xml"
        if not edited_part.is_file():
            print(f"FAILED - edited document.xml not found at {edited_part}")
            return False

        with tempfile.TemporaryDirectory() as staging:
            staging_dir = Path(staging)
            try:
                with zipfile.ZipFile(self.original_docx, "r") as archive:
                    safe_extract(archive, staging_dir)
            except (zipfile.BadZipFile, ValueError, OSError) as exc:
                print(f"FAILED - cannot unpack original document: {exc}")
                return False

            baseline_part = staging_dir / "word" / "document.xml"
            if not baseline_part.is_file():
                print(
                    "FAILED - the original package has no word/document.xml:"
                    f" {self.original_docx}"
                )
                return False

            try:
                edited_root = ET.parse(edited_part).getroot()
                baseline_root = ET.parse(baseline_part).getroot()
            except (ET.ParseError, DefusedXmlException) as exc:
                print(f"FAILED - cannot parse document XML: {exc}")
                return False

            fresh = self._fresh_revisions(baseline_root, edited_root)
            self._undo_revisions(edited_root, fresh)

            baseline_text = self._body_text(baseline_root)
            edited_text = self._body_text(edited_root)

        if edited_text == baseline_text:
            if self.verbose:
                print(
                    f"PASSED - all {len(fresh)} revision(s) against the original"
                    " are tracked"
                )
            return True

        print(self._failure_report(baseline_text, edited_text))
        return False

    # -------------------------------------------------------- revision sets

    @staticmethod
    def _revisions(root):
        return [
            element
            for element in root.iter()
            if element.tag in (f"{{{W}}}ins", f"{{{W}}}del")
        ]

    @staticmethod
    def _visible_text(element) -> str:
        pieces = []
        for node in element.iter():
            if node.tag in (f"{{{W}}}t", f"{{{W}}}delText"):
                pieces.append(
                    rendered_text(node.text or "", node.get(XML_SPACE_ATTR) == "preserve")
                )
        return "".join(pieces)

    def _revision_key(self, element):
        return (
            element.tag,
            element.get(f"{{{W}}}author"),
            element.get(f"{{{W}}}date"),
            self._visible_text(element),
        )

    def _fresh_revisions(self, baseline_root, edited_root) -> set:
        """Edited-side revisions that do not reproduce an original one."""
        baseline_revisions = self._revisions(baseline_root)
        edited_revisions = self._revisions(edited_root)

        # Exact matching first: a revision survives when its kind, author,
        # date and carried text are all reproduced.
        pool: dict = {}
        for element in baseline_revisions:
            pool.setdefault(self._revision_key(element), []).append(element)

        matched_originals = set()
        unmatched_edits = []
        for element in edited_revisions:
            bucket = pool.get(self._revision_key(element))
            if bucket:
                matched_originals.add(bucket.pop())
            else:
                unmatched_edits.append(element)

        # A revision may be split into pieces (for example to nest a partial
        # rejection): the pieces keep author/date and re-spell the same text.
        def group_key(element):
            return self._revision_key(element)[:3]

        def group_text(elements):
            return "".join(self._visible_text(element) for element in elements)

        leftover_originals: dict = {}
        for element in baseline_revisions:
            if element not in matched_originals:
                leftover_originals.setdefault(group_key(element), []).append(element)

        edited_groups: dict = {}
        for element in unmatched_edits:
            edited_groups.setdefault(group_key(element), []).append(element)

        fresh = set()
        for key, elements in edited_groups.items():
            rebuilt = group_text(elements)
            if rebuilt and rebuilt == group_text(leftover_originals.get(key, [])):
                continue
            fresh.update(elements)
        return fresh

    # ------------------------------------------------------------- undo

    @staticmethod
    def _undo_revisions(root, targets: set) -> None:
        ins_tag, del_tag = f"{{{W}}}ins", f"{{{W}}}del"
        removals = []       # (parent, w:ins) dropped outright
        unwraps = []        # (parent, index, w:del) spliced back in
        for parent in root.iter():
            for index, child in enumerate(list(parent)):
                if child not in targets:
                    continue
                if child.tag == ins_tag:
                    removals.append((parent, child))
                elif child.tag == del_tag:
                    unwraps.append((parent, index, child))
        for parent, child in removals:
            parent.remove(child)
        for parent, index, deletion in unwraps:
            for node in deletion.iter():
                if node.tag == f"{{{W}}}delText":
                    node.tag = f"{{{W}}}t"
            for offset, child in enumerate(list(deletion)):
                parent.insert(index + offset, child)
            parent.remove(deletion)

    # --------------------------------------------------------- comparison

    @staticmethod
    def _body_text(root) -> str:
        paragraphs = []
        for paragraph in root.iter(f"{{{W}}}p"):
            text = "".join(
                rendered_text(node.text or "", node.get(XML_SPACE_ATTR) == "preserve")
                for node in paragraph.iter(f"{{{W}}}t")
            )
            if text:
                paragraphs.append(text)
        return "\n".join(paragraphs)

    def _failure_report(self, baseline_text: str, edited_text: str) -> str:
        lines = [
            "FAILED - body text differs from the original even after the new",
            "tracked changes are discounted; something was edited untracked.",
            "",
            "Common causes:",
            "  1. text changed inside another author's <w:ins>/<w:del>",
            "  2. edits made without tracked changes at all",
            "  3. rejecting another's insertion without nesting <w:del> in it",
            "  4. rewriting an existing revision: one is recognised only when",
            "     author, date and text are reproduced exactly",
            "",
            "Working against pre-redlined documents:",
            "  - reject an insertion:  nest <w:del> inside the <w:ins>",
            "  - reject part of one: split the <w:ins> around the rejected",
            "    runs, keeping author/date so the pieces still read the same",
            "  - restore a deletion:   add a fresh <w:ins> after the <w:del>",
            "",
            "Word-level differences ([-removed-] {+added+}):",
            _word_level_diff(baseline_text, edited_text),
        ]
        return "\n".join(lines)


def _word_level_diff(before: str, after: str) -> str:
    before_words = before.split()
    after_words = after.split()
    chunks = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, before_words, after_words
    ).get_opcodes():
        if tag == "equal":
            chunks.append(" ".join(before_words[i1:i2]))
        elif tag == "delete":
            chunks.append("[-" + " ".join(before_words[i1:i2]) + "-]")
        elif tag == "insert":
            chunks.append("{+" + " ".join(after_words[j1:j2]) + "+}")
        else:
            chunks.append(
                "[-" + " ".join(before_words[i1:i2]) + "-]"
                "{+" + " ".join(after_words[j1:j2]) + "+}"
            )
    return " ".join(chunks)


if __name__ == "__main__":
    raise SystemExit("RedliningValidator is a library; run office/validate.py instead.")
