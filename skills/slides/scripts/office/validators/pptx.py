"""PPTX-specific checks on top of the shared package validator.

Besides the generic package checks, presentations get: uuid-shaped id
hygiene, slide/layout/master relationship wiring, notes-slide exclusivity,
master/theme part sharing, chart consistency, and the slide-XML defects
PowerPoint is known to hard-reject.
"""

from __future__ import annotations

import re
import tempfile
import zipfile
from pathlib import Path

import lxml.etree

from ..helpers import opc_target, rels_source_part, safe_extract
from .base import NS_OFFICE_RELS, NS_PACKAGE_RELS, PackageValidator

NS_PRESENTATION = "http://schemas.openxmlformats.org/presentationml/2006/main"

_UUID_SHAPE = re.compile(
    r"^[{(]?[0-9A-Fa-f]{8}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{4}"
    r"-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{12}[)}]?$"
)

#: Id-list elements and the relationship type they must resolve to.
_REL_TYPES = {
    "sldid": "slide",
    "sldmasterid": "slidemaster",
    "notesmasterid": "notesmaster",
    "sldlayoutid": "slidelayout",
    "themeid": "theme",
    "tablestyleid": "tablestyles",
}


class PPTXSchemaValidator(PackageValidator):
    """Validate an unpacked PPTX package directory."""

    PART_SCHEMAS = {
        "[Content_Types].xml": "ecma376-opc/opc-contentTypes.xsd",
        ".rels": "ecma376-opc/opc-relationships.xsd",
        "app.xml": "ecma376-transitional/shared-documentPropertiesExtended.xsd",
        "custom.xml": "ecma376-transitional/shared-documentPropertiesCustom.xsd",
        "theme": "ecma376-transitional/dml-main.xsd",
        "ppt": "ecma376-transitional/pml.xsd",
    }

    REL_TYPE_BY_ELEMENT = _REL_TYPES

    def validate(self) -> bool:
        if not self.check_well_formed():
            return False
        verdicts = [
            self.check_namespaces(),
            self.check_id_uniqueness(),
            self.check_uuid_shaped_ids(),
            self.check_part_references(),
            self.check_layout_id_refs(),
            self.check_content_types(),
            self.check_xsd_delta(),
            self.check_notes_slide_sharing(),
            self.check_relationship_id_refs(),
            self.check_single_layout_per_slide(),
            self.check_master_theme_sharing(),
            self.check_charts(),
            self.check_slide_schema_verdicts(),
        ]
        return all(verdicts)

    # ----------------------------------------------------------- plumbing

    def content_schema_for(self, part: Path):
        if part.parent.name in (
            "ppt", "slides", "slideLayouts", "slideMasters",
            "notesSlides", "notesMasters", "handoutMasters",
        ):
            return self.PART_SCHEMAS["ppt"]
        return None

    def schema_for(self, part: Path):
        # Chart parts are covered by targeted chart checks instead of XSD.
        if part.parent.name == "charts" and part.name.startswith("chart"):
            return None
        return super().schema_for(part)

    def adapt_for_schema(self, tree, rel_part: Path):
        """Tolerate notesMasterIdLst after sldIdLst in presentation.xml.

        PowerPoint accepts that ordering; the strict schema does not, so the
        comparison copy is reordered rather than reported.
        """
        if rel_part.as_posix() != "ppt/presentation.xml":
            return tree
        root = tree.getroot()
        notes = root.find(f"{{{NS_PRESENTATION}}}notesMasterIdLst")
        slides = root.find(f"{{{NS_PRESENTATION}}}sldIdLst")
        if notes is None or slides is None:
            return tree
        children = list(root)
        if children.index(notes) < children.index(slides):
            return tree
        root.remove(notes)
        root.insert(list(root).index(slides), notes)
        return tree

    def _package_snapshot(self) -> dict:
        """Bytes of the parts the master/theme and chart checks inspect."""
        wanted = [self.unpacked_dir / "[Content_Types].xml"]
        wanted += sorted(self.unpacked_dir.glob("ppt/presentation.xml"))
        wanted += sorted(self.unpacked_dir.glob("ppt/theme/*.xml"))
        wanted += sorted(self.unpacked_dir.glob("ppt/theme/_rels/*.rels"))
        wanted += sorted(self.unpacked_dir.glob("ppt/charts/chart*.xml"))
        for group in ("slideMasters", "notesMasters", "handoutMasters"):
            wanted += sorted(self.unpacked_dir.glob(f"ppt/{group}/*.xml"))
            wanted += sorted(self.unpacked_dir.glob(f"ppt/{group}/_rels/*.rels"))
        return {
            part.relative_to(self.unpacked_dir).as_posix(): part.read_bytes()
            for part in wanted
            if part.is_file()
        }

    # ------------------------------------------------------------- checks

    def check_uuid_shaped_ids(self) -> bool:
        problems = []
        for part in self.xml_files:
            try:
                root = lxml.etree.parse(str(part)).getroot()
            except lxml.etree.XMLSyntaxError:
                continue
            for element in root.iter():
                if not isinstance(element.tag, str):
                    continue
                for attr, value in element.attrib.items():
                    if not attr.rsplit("}", 1)[-1].lower().endswith("id"):
                        continue
                    stripped = value.strip("{}()").replace("-", "")
                    looks_uuidish = len(stripped) == 32 and stripped.isalnum()
                    if looks_uuidish and not _UUID_SHAPE.match(value):
                        problems.append(
                            f"  {self._relative(part)}: line {element.sourceline}:"
                            f" id '{value}' looks like a UUID but has non-hex digits"
                        )
        return self.report(
            "uuid-shaped ids", problems, "uuid-shaped ids are well-formed"
        )

    def check_layout_id_refs(self) -> bool:
        """Every sldLayoutId in a master must reference a layout the master's
        own .rels actually points at."""
        problems = []
        masters = sorted(self.unpacked_dir.glob("ppt/slideMasters/*.xml"))
        if not masters:
            if self.verbose:
                print("PASSED - layout id refs: no slide masters present")
            return True
        for master in masters:
            master_rel = self._relative(master)
            rels_part = master.parent / "_rels" / f"{master.name}.rels"
            if not rels_part.is_file():
                problems.append(
                    f"  {master_rel}: missing sidecar {self._relative(rels_part)}"
                )
                continue
            try:
                master_root = lxml.etree.parse(str(master)).getroot()
                rels_root = lxml.etree.parse(str(rels_part)).getroot()
            except lxml.etree.XMLSyntaxError as exc:
                problems.append(f"  {master_rel}: unreadable: {exc}")
                continue
            layout_rids = {
                rel.get("Id")
                for rel in rels_root.iter(f"{{{NS_PACKAGE_RELS}}}Relationship")
                if "slideLayout" in rel.get("Type", "")
            }
            for entry in master_root.iter(f"{{{NS_PRESENTATION}}}sldLayoutId"):
                rid = entry.get(f"{{{NS_OFFICE_RELS}}}id")
                if rid and rid not in layout_rids:
                    problems.append(
                        f"  {master_rel}: line {entry.sourceline}: sldLayoutId"
                        f" id='{entry.get('id')}' points at r:id='{rid}', which is"
                        " not a slide-layout relationship of this master"
                    )
        ok = self.report(
            "layout id refs", problems,
            "every sldLayoutId resolves to a layout relationship",
        )
        if not ok:
            print("Drop the stale entries or add the missing layout relationships.")
        return ok

    def check_single_layout_per_slide(self) -> bool:
        problems = []
        for rels_part in sorted(self.unpacked_dir.glob("ppt/slides/_rels/*.xml.rels")):
            try:
                root = lxml.etree.parse(str(rels_part)).getroot()
            except lxml.etree.XMLSyntaxError as exc:
                problems.append(f"  {self._relative(rels_part)}: unreadable: {exc}")
                continue
            layouts = [
                rel
                for rel in root.iter(f"{{{NS_PACKAGE_RELS}}}Relationship")
                if "slideLayout" in rel.get("Type", "")
            ]
            if len(layouts) > 1:
                problems.append(
                    f"  {self._relative(rels_part)}: {len(layouts)} slideLayout"
                    " relationships on one slide"
                )
        return self.report(
            "one layout per slide", problems,
            "each slide references exactly one layout",
        )

    def check_notes_slide_sharing(self) -> bool:
        problems = []
        claims: dict[str, list[str]] = {}
        for rels_part in sorted(self.unpacked_dir.glob("ppt/slides/_rels/*.xml.rels")):
            try:
                root = lxml.etree.parse(str(rels_part)).getroot()
            except lxml.etree.XMLSyntaxError as exc:
                problems.append(f"  {self._relative(rels_part)}: unreadable: {exc}")
                continue
            for rel in root.iter(f"{{{NS_PACKAGE_RELS}}}Relationship"):
                if "notesSlide" not in rel.get("Type", ""):
                    continue
                part = opc_target(
                    rel.get("Target", ""),
                    rels_source_part(rels_part, self.unpacked_dir),
                    rel.get("TargetMode", ""),
                )
                if part:
                    slide_name = rels_part.name[: -len(".xml.rels")]
                    claims.setdefault(part, []).append(slide_name)
        for part, slide_names in sorted(claims.items()):
            if len(slide_names) > 1:
                problems.append(
                    f"  notes part '{part}' is claimed by several slides:"
                    f" {', '.join(slide_names)}"
                )
        return self.report(
            "notes slide exclusivity", problems,
            "each notes part belongs to a single slide",
        )

    def check_master_theme_sharing(self) -> bool:
        from ..helpers.pptx_theme import _NOTES_MASTERS, live_shared_master_themes

        shared = live_shared_master_themes(self._package_snapshot())
        problems = [f"  {message}" for message in shared]
        ok = self.report(
            "master/theme separation", problems,
            "no master shares a theme part in a way PowerPoint refuses",
        )
        if not ok:
            if any(message.startswith(_NOTES_MASTERS) for message in shared):
                print(
                    "  Remedy: move <p:notesMasterIdLst> in ppt/presentation.xml"
                    " back to directly after <p:sldIdLst>."
                )
            else:
                print("  Remedy: give each master its own theme part.")
        return ok

    def check_charts(self) -> bool:
        from ..helpers.pptx_chart import find_chart_problems

        found = find_chart_problems(self._package_snapshot())
        return self.report(
            "chart consistency", [f"  {p}" for p in found],
            "charts satisfy the constraints PowerPoint enforces",
        )

    def check_slide_schema_verdicts(self) -> bool:
        from ..helpers.pptx_slide import (
            SLIDE_PART_RE,
            fatal_slide_errors,
            is_schema_verdict,
        )

        schema = self.schemas_dir / self.PART_SCHEMAS["ppt"]
        inherited = self._original_slide_verdicts(schema)
        unreadable = []
        fatal = []
        for part in self.xml_files:
            rel = self._relative(part)
            if not SLIDE_PART_RE.fullmatch(rel):
                continue
            outcome, errors = self._xsd_errors(part, self.unpacked_dir,
                                               schema_path=schema)
            if outcome is None or not errors:
                continue
            foreign = [e for e in errors if not is_schema_verdict(e)]
            if foreign:
                unreadable.extend(f"{rel}: {e}" for e in foreign)
                continue
            if outcome:
                continue
            for message in fatal_slide_errors(errors):
                if message not in inherited:
                    fatal.append(f"{rel}: {message}")

        ok = True
        if unreadable:
            ok = self.report(
                "slide readability",
                [f"  {m[:240]}" for m in sorted(unreadable)], "",
            )
        if fatal:
            ok = self.report(
                "slide defects PowerPoint rejects",
                [f"  {m[:240]}" for m in sorted(fatal)], "",
            ) and ok
        if ok and self.verbose:
            print("PASSED - slide XML carries no defect PowerPoint refuses")
        return ok

    def _original_slide_verdicts(self, schema: Path) -> set:
        """Fatal slide errors the original deck already had (if any)."""
        from ..helpers.pptx_slide import SLIDE_PART_RE, fatal_slide_errors

        if self.original_file is None:
            return set()
        found: set = set()
        with tempfile.TemporaryDirectory() as staging:
            staging_dir = Path(staging)
            try:
                with zipfile.ZipFile(self.original_file, "r") as archive:
                    safe_extract(archive, staging_dir)
            except (zipfile.BadZipFile, ValueError, OSError):
                return set()
            for part in sorted(staging_dir.rglob("*.xml")):
                rel = part.relative_to(staging_dir).as_posix()
                if not SLIDE_PART_RE.fullmatch(rel):
                    continue
                outcome, errors = self._xsd_errors(part, staging_dir,
                                                   schema_path=schema)
                if outcome is None or outcome or not errors:
                    continue
                found.update(fatal_slide_errors(errors))
        return found


if __name__ == "__main__":
    raise SystemExit("PPTXSchemaValidator is a library; run office/validate.py instead.")
