"""Structural integrity checks shared by the OOXML family validators.

A validator inspects an *unpacked* package directory.  Each ``check_*``
method returns a list of human-readable problems (empty when the package is
clean); :meth:`PackageValidator.report` renders them and produces the
boolean the CLI ultimately maps to an exit status.

XSD validation is differential: a part only fails when it carries schema
errors that the original document did not already have, so quirks inherited
from a template are not reported as fresh damage.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from functools import cache
from pathlib import Path

import lxml.etree

from ..helpers import XML_SPACE, opc_target, rels_source_part, safe_extract

NS_MARKUP_COMPAT = "http://schemas.openxmlformats.org/markup-compatibility/2006"
NS_XML = "http://www.w3.org/XML/1998/namespace"
NS_PACKAGE_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_OFFICE_RELS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"

#: Element local-name -> (id attribute local-name, "part" or "package" scope).
_ID_RULES = {
    "comment": ("id", "part"),
    "commentrangestart": ("id", "part"),
    "commentrangeend": ("id", "part"),
    "bookmarkstart": ("id", "part"),
    "bookmarkend": ("id", "part"),
    "sldid": ("id", "part"),
    "sldmasterid": ("id", "package"),
    "sldlayoutid": ("id", "package"),
    "cm": ("authorid", "part"),
    "sheet": ("sheetid", "part"),
    "definedname": ("id", "part"),
    "cxnsp": ("id", "part"),
    "sp": ("id", "part"),
    "pic": ("id", "part"),
    "grpsp": ("id", "part"),
}

#: Ancestor local-names inside which id rules do not apply.
_ID_RULE_EXEMPTIONS = frozenset({"sectionlst", "alternatecontent"})

#: Schema messages matching any of these fragments are known false alarms.
_IGNORED_SCHEMA_MESSAGES = ("hyphenationZone",)

_MAIN_CONTENT_FOLDERS = frozenset({"word", "ppt", "xl"})

_OOXML_NAMESPACE_SET = frozenset({
    "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "http://schemas.openxmlformats.org/schemaLibrary/2006/main",
    "http://schemas.openxmlformats.org/drawingml/2006/main",
    "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "http://schemas.openxmlformats.org/drawingml/2006/chartDrawing",
    "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
    "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "http://schemas.openxmlformats.org/presentationml/2006/main",
    "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "http://schemas.openxmlformats.org/officeDocument/2006/sharedTypes",
    NS_XML,
})

#: Root local-names that must appear as Overrides in [Content_Types].xml.
_DECLARABLE_ROOTS = frozenset({
    "sld", "sldLayout", "sldMaster", "presentation",
    "document", "workbook", "worksheet", "theme",
})

#: Extension -> content type for media a package is expected to declare.
_MEDIA_CONTENT_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
    "wmf": "image/x-wmf",
    "emf": "image/x-emf",
}

#: Elements whose character data word processors may trim unless preserved.
_TEXT_HOLDERS = frozenset({"t", "delText", "instrText", "delInstrText"})

#: Jinja-style placeholders sometimes left in template text.
_TEMPLATE_TOKEN = re.compile(r"\{\{[^}]*\}\}")

XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema"

#: Relationship attributes (in the office-relationships namespace) that must
#: resolve to an entry in the part's own .rels file.
_RID_ATTRIBUTES = ("id", "embed", "link")


def _schema_verdict(message: str) -> bool:
    """True when *message* is an XSD verdict rather than an I/O failure."""
    return message.startswith("Element ")


def _xml_parser() -> lxml.etree.XMLParser:
    return lxml.etree.XMLParser(resolve_entities=False, no_network=True)


@cache
def _schema_work_tree(schemas_dir: str) -> str:
    """Mirror *schemas_dir* into a scratch tree with one accommodation.

    A few published schemas import the XML namespace without a
    schemaLocation, which lxml cannot resolve.  The vendored schema files
    must stay byte-identical to their published sources (ECMA-376 / W3C /
    Microsoft Open Specifications), so the location is filled in only in a
    throwaway copy, pointing at the vendored W3C xml.xsd.
    """
    source = Path(schemas_dir)
    mirror = Path(tempfile.mkdtemp(prefix="ooxml-schemas-"))
    xml_schema = mirror / "w3c" / "xml.xsd"
    for path in sorted(source.rglob("*.xsd")):
        target = mirror / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        document = lxml.etree.parse(str(path))
        touched = False
        for node in document.getroot().iter(f"{{{XSD_NAMESPACE}}}import"):
            if node.get("namespace") == NS_XML and not node.get("schemaLocation"):
                node.set(
                    "schemaLocation",
                    os.path.relpath(xml_schema, target.parent),
                )
                touched = True
        if touched:
            document.write(str(target), xml_declaration=True, encoding="utf-8")
        else:
            shutil.copyfile(path, target)
    return str(mirror)


@cache
def _compiled_schema(schema_path: str) -> lxml.etree.XMLSchema:
    path = Path(schema_path).resolve()
    root = path.parent
    while root.name != "schemas" and root != root.parent:
        root = root.parent
    if root.name != "schemas":
        root = path.parent
    entry = Path(_schema_work_tree(str(root))) / path.relative_to(root)
    with open(entry, "rb") as handle:
        document = lxml.etree.parse(handle, base_url=str(entry))
    return lxml.etree.XMLSchema(document)


class PackageValidator:
    """Family-independent checks over an unpacked OOXML package directory."""

    #: Part name (or content folder) -> schema file under ``schemas_dir``.
    PART_SCHEMAS: dict[str, str] = {}

    #: Element local-name -> expected relationship type fragment, used by the
    #: relationship-id check.  Families with typed id lists override this.
    REL_TYPE_BY_ELEMENT: dict[str, str] = {}

    def __init__(self, unpacked_dir, original_file=None, verbose=False):
        self.unpacked_dir = Path(unpacked_dir).resolve()
        self.original_file = Path(original_file) if original_file else None
        self.verbose = bool(verbose)
        self.schemas_dir = Path(__file__).resolve().parent.parent / "schemas"
        self.xml_files = sorted(
            {
                *self.unpacked_dir.rglob("*.xml"),
                *self.unpacked_dir.rglob("*.rels"),
            }
        )
        if not self.xml_files:
            print(f"Warning: no XML parts found under {self.unpacked_dir}")

    # ------------------------------------------------------------------ API

    def validate(self) -> bool:
        raise NotImplementedError("family validators implement validate()")

    def repair(self) -> int:
        """Fix cheap, unambiguous problems in place; return how many."""
        return self.repair_whitespace_preservation()

    def report(self, title: str, problems, pass_note: str) -> bool:
        """Render *problems* for *title* and return True when there are none."""
        problems = list(problems)
        if problems:
            print(f"FAILED - {title}: {len(problems)} problem(s):")
            for problem in problems:
                print(problem)
            return False
        if self.verbose:
            print(f"PASSED - {pass_note}")
        return True

    def _relative(self, part: Path) -> str:
        return part.relative_to(self.unpacked_dir).as_posix()

    # ------------------------------------------------------- basic checks

    def check_well_formed(self) -> bool:
        problems = []
        for part in self.xml_files:
            try:
                document = lxml.etree.parse(str(part), parser=_xml_parser())
            except lxml.etree.XMLSyntaxError as exc:
                problems.append(f"  {self._relative(part)}: line {exc.lineno}: {exc.msg}")
                continue
            except OSError as exc:
                problems.append(f"  {self._relative(part)}: unreadable: {exc}")
                continue
            if document.docinfo.doctype:
                problems.append(
                    f"  {self._relative(part)}: DOCTYPE/DTD is not permitted in OOXML parts"
                )
        return self.report("XML syntax", problems, "every XML part is well-formed")

    def check_namespaces(self) -> bool:
        problems = []
        for part in self.xml_files:
            try:
                root = lxml.etree.parse(str(part), parser=_xml_parser()).getroot()
            except lxml.etree.XMLSyntaxError:
                continue
            declared = {prefix for prefix in root.nsmap if prefix}
            for attr, value in root.attrib.items():
                if not attr.endswith("Ignorable"):
                    continue
                for prefix in value.split():
                    if prefix not in declared:
                        problems.append(
                            f"  {self._relative(part)}: mc:Ignorable lists undeclared"
                            f" prefix '{prefix}'"
                        )
        return self.report(
            "namespace declarations", problems,
            "every mc:Ignorable prefix is declared",
        )

    def check_id_uniqueness(self) -> bool:
        problems = []
        package_scope: dict[str, tuple[str, int]] = {}
        for part in self.xml_files:
            try:
                root = lxml.etree.parse(str(part), parser=_xml_parser()).getroot()
            except lxml.etree.XMLSyntaxError:
                continue
            part_scope: dict[tuple[str, str, str], int] = {}
            for element in root.iter():
                if not isinstance(element.tag, str):
                    continue
                local = element.tag.rsplit("}", 1)[-1].lower()
                rule = _ID_RULES.get(local)
                if rule is None:
                    continue
                if any(
                    isinstance(ancestor.tag, str)
                    and ancestor.tag.rsplit("}", 1)[-1].lower() in _ID_RULE_EXEMPTIONS
                    for ancestor in element.iterancestors()
                ):
                    continue
                attr_local, scope = rule
                value = next(
                    (
                        v
                        for k, v in element.attrib.items()
                        if k.rsplit("}", 1)[-1].lower() == attr_local
                    ),
                    None,
                )
                if value is None:
                    continue
                location = f"{self._relative(part)}: line {element.sourceline}"
                if scope == "package":
                    prior = package_scope.get(value)
                    if prior is not None:
                        problems.append(
                            f"  {location}: package-wide id '{value}' of <{local}>"
                            f" already used at {prior[0]}: line {prior[1]}"
                        )
                    else:
                        package_scope[value] = (self._relative(part), element.sourceline)
                else:
                    key = (local, attr_local, value)
                    prior_line = part_scope.get(key)
                    if prior_line is not None:
                        problems.append(
                            f"  {location}: duplicate {attr_local}='{value}' on"
                            f" <{local}> (first occurrence at line {prior_line})"
                        )
                    else:
                        part_scope[key] = element.sourceline
        return self.report("id uniqueness", problems, "all required ids are unique")

    def check_part_references(self) -> bool:
        rels_parts = [p for p in self.xml_files if p.name.endswith(".rels")]
        payload = {
            p.resolve()
            for p in self.unpacked_dir.rglob("*")
            if p.is_file()
            and p.name != "[Content_Types].xml"
            and not p.name.endswith(".rels")
        }
        referenced: set[Path] = set()
        problems = []
        for rels_part in rels_parts:
            rels_rel = self._relative(rels_part)
            try:
                root = lxml.etree.parse(str(rels_part), parser=_xml_parser()).getroot()
            except lxml.etree.XMLSyntaxError as exc:
                problems.append(f"  {rels_rel}: unreadable: {exc}")
                continue
            owner = rels_source_part(rels_part, self.unpacked_dir)
            for rel in root.iter(f"{{{NS_PACKAGE_RELS}}}Relationship"):
                target = rel.get("Target", "")
                try:
                    part_name = opc_target(target, owner, rel.get("TargetMode", ""))
                except ValueError:
                    part_name = None
                    if target:
                        problems.append(
                            f"  {rels_rel}: line {rel.sourceline}: illegal target {target!r}"
                        )
                if part_name is None:
                    continue
                resolved = (self.unpacked_dir / part_name).resolve()
                if resolved.is_relative_to(self.unpacked_dir) and resolved.is_file():
                    referenced.add(resolved)
                else:
                    problems.append(
                        f"  {rels_rel}: line {rel.sourceline}: target '{target}'"
                        " does not exist in the package"
                    )
        for orphan in sorted(payload - referenced):
            problems.append(
                f"  Orphaned part: {orphan.relative_to(self.unpacked_dir).as_posix()}"
                " is never referenced"
            )
        ok = self.report(
            "relationship targets", problems,
            "every relationship target exists and every part is reachable",
        )
        if not ok:
            print("Fix dangling targets or orphan parts before delivering the file.")
        return ok

    def check_relationship_id_refs(self) -> bool:
        problems = []
        for part in self.xml_files:
            if part.name.endswith(".rels"):
                continue
            rels_part = part.parent / "_rels" / f"{part.name}.rels"
            if not rels_part.is_file():
                continue
            part_rel = self._relative(part)
            rels_rel = self._relative(rels_part)
            try:
                rels_root = lxml.etree.parse(str(rels_part), parser=_xml_parser()).getroot()
                part_root = lxml.etree.parse(str(part), parser=_xml_parser()).getroot()
            except lxml.etree.XMLSyntaxError as exc:
                problems.append(f"  {part_rel}: unreadable: {exc}")
                continue
            rid_types: dict[str, str] = {}
            for rel in rels_root.iter(f"{{{NS_PACKAGE_RELS}}}Relationship"):
                rid = rel.get("Id")
                if not rid:
                    continue
                if rid in rid_types:
                    problems.append(
                        f"  {rels_rel}: line {rel.sourceline}: relationship id"
                        f" '{rid}' is defined twice"
                    )
                rid_types.setdefault(rid, rel.get("Type", "").rsplit("/", 1)[-1])
            for element in part_root.iter():
                if not isinstance(element.tag, str):
                    continue
                local = element.tag.rsplit("}", 1)[-1]
                for attr_name in _RID_ATTRIBUTES:
                    rid = element.get(f"{{{NS_OFFICE_RELS}}}{attr_name}")
                    if not rid:
                        continue
                    location = f"{part_rel}: line {element.sourceline}"
                    if rid not in rid_types:
                        known = ", ".join(sorted(rid_types)[:5])
                        problems.append(
                            f"  {location}: <{local}> r:{attr_name}='{rid}' has no"
                            f" matching relationship (known ids: {known}"
                            f"{'...' if len(rid_types) > 5 else ''})"
                        )
                        continue
                    if attr_name != "id" or not self.REL_TYPE_BY_ELEMENT:
                        continue
                    expected = self.expected_relationship_type(local.lower())
                    if expected and expected not in rid_types[rid].lower():
                        problems.append(
                            f"  {location}: <{local}> points at '{rid}' of type"
                            f" '{rid_types[rid]}', expected a '{expected}' relationship"
                        )
        ok = self.report(
            "relationship id references", problems,
            "every r:id/r:embed/r:link resolves",
        )
        if not ok:
            print("Mismatched relationship ids surface as a corrupt document.")
        return ok

    def expected_relationship_type(self, local_name: str):
        """Expected relationship-type fragment for an id-carrying element."""
        if local_name in self.REL_TYPE_BY_ELEMENT:
            return self.REL_TYPE_BY_ELEMENT[local_name]
        if local_name.endswith("id") and len(local_name) > 2:
            stem = local_name[:-2]
            if stem == "sld":
                return "slide"
            return stem
        if local_name.endswith("reference") and len(local_name) > 9:
            return local_name[:-9]
        return None

    def check_content_types(self) -> bool:
        manifest = self.unpacked_dir / "[Content_Types].xml"
        if not manifest.is_file():
            print("FAILED - content types: [Content_Types].xml is missing")
            return False
        problems = []
        try:
            root = lxml.etree.parse(str(manifest), parser=_xml_parser()).getroot()
        except lxml.etree.XMLSyntaxError as exc:
            print(f"FAILED - content types: [Content_Types].xml is unreadable: {exc}")
            return False
        overrides = {
            node.get("PartName", "").lstrip("/")
            for node in root.iter(f"{{{NS_CONTENT_TYPES}}}Override")
        }
        defaults = {
            node.get("Extension", "").lower()
            for node in root.iter(f"{{{NS_CONTENT_TYPES}}}Default")
        }
        for part in self.xml_files:
            rel = self._relative(part)
            if part.name.endswith(".rels") or part.name == "[Content_Types].xml":
                continue
            if rel.startswith(("docProps/", "_rels/")):
                continue
            try:
                part_root = lxml.etree.parse(str(part), parser=_xml_parser()).getroot()
            except lxml.etree.XMLSyntaxError:
                continue
            local = part_root.tag.rsplit("}", 1)[-1]
            if local in _DECLARABLE_ROOTS and rel not in overrides:
                problems.append(
                    f"  {rel}: <{local}> part is not declared in [Content_Types].xml"
                )
        for part in sorted(self.unpacked_dir.rglob("*")):
            if not part.is_file() or part.name.endswith((".xml", ".rels")):
                continue
            if part.name == "[Content_Types].xml":
                continue
            if "_rels" in part.parts or "docProps" in part.parts:
                continue
            extension = part.suffix.lstrip(".").lower()
            if extension and extension not in defaults:
                content_type = _MEDIA_CONTENT_TYPES.get(extension)
                if content_type:
                    problems.append(
                        f"  {self._relative(part)}: extension '{extension}' is not"
                        f' declared - add <Default Extension="{extension}"'
                        f' ContentType="{content_type}"/>'
                    )
        return self.report(
            "content type coverage", problems,
            "all parts are declared in [Content_Types].xml",
        )

    # ------------------------------------------------------- XSD machinery

    def content_schema_for(self, part: Path):
        """Schema key for parts under a main content folder, else ``None``."""
        if part.parent.name in _MAIN_CONTENT_FOLDERS:
            return self.PART_SCHEMAS.get(part.parent.name)
        return None

    def schema_for(self, part: Path):
        """XSD path that governs *part*, or ``None`` when unchecked."""
        if part.name in self.PART_SCHEMAS:
            return self.schemas_dir / self.PART_SCHEMAS[part.name]
        if part.name.endswith(".rels") and ".rels" in self.PART_SCHEMAS:
            return self.schemas_dir / self.PART_SCHEMAS[".rels"]
        if part.parent.name == "charts" and part.name.startswith("chart"):
            key = self.PART_SCHEMAS.get("chart")
            return self.schemas_dir / key if key else None
        if part.parent.name == "theme" and part.name.startswith("theme"):
            key = self.PART_SCHEMAS.get("theme")
            return self.schemas_dir / key if key else None
        key = self.content_schema_for(part)
        return self.schemas_dir / key if key else None

    def prepare_for_schema(self, tree, rel_part: Path):
        """Return a copy of *tree* normalised for schema comparison.

        Template placeholders are stripped from character data (but never
        from text-holder elements, where they may be deliberate content),
        the root's mc:Ignorable hint is dropped, and - for main content
        parts - elements and attributes from unknown namespaces are pruned,
        mirroring what a markup-compatibility consumer would skip.
        """
        snapshot = lxml.etree.fromstring(lxml.etree.tostring(tree))
        for element in snapshot.iter():
            if not isinstance(element.tag, str):
                continue
            if element.tag.rsplit("}", 1)[-1] == "t":
                continue
            if element.text:
                element.text = _TEMPLATE_TOKEN.sub("", element.text)
            if element.tail:
                element.tail = _TEMPLATE_TOKEN.sub("", element.tail)
        snapshot.attrib.pop(f"{{{NS_MARKUP_COMPAT}}}Ignorable", None)
        if rel_part.parts and rel_part.parts[0] in _MAIN_CONTENT_FOLDERS:
            self._prune_unknown_namespaces(snapshot)
        return self.adapt_for_schema(lxml.etree.ElementTree(snapshot), rel_part)

    def _prune_unknown_namespaces(self, root) -> None:
        for element in list(root.iter()):
            if not isinstance(element.tag, str):
                continue
            for attr in list(element.attrib):
                if "{" in attr and attr[1:].split("}")[0] not in _OOXML_NAMESPACE_SET:
                    del element.attrib[attr]
        def drop_foreign(node) -> None:
            for child in list(node):
                if not isinstance(child.tag, str):
                    node.remove(child)
                    continue
                if child.tag.startswith("{") and child.tag[1:].split("}")[0] not in _OOXML_NAMESPACE_SET:
                    node.remove(child)
                    continue
                drop_foreign(child)
        drop_foreign(root)

    def adapt_for_schema(self, tree, rel_part: Path):
        """Family hook: last-minute normalisation before XSD validation."""
        return tree

    def _xsd_errors(self, part: Path, base_dir: Path, schema_path=None):
        """Triple state: (None, None) unchecked, (True, set()) clean,
        (False, errors) schema or infrastructure failures."""
        schema_path = Path(schema_path) if schema_path else self.schema_for(part)
        if schema_path is None:
            return None, None
        try:
            schema = _compiled_schema(str(schema_path))
            tree = lxml.etree.parse(str(part), parser=_xml_parser())
            rel_part = Path(part).resolve().relative_to(Path(base_dir).resolve())
            prepared = self.prepare_for_schema(tree, rel_part)
            if schema.validate(prepared):
                return True, set()
            return False, {entry.message for entry in schema.error_log}
        except Exception as exc:  # missing schema, unreadable part, ...
            return False, {str(exc)}

    def _inherited_errors(self, part: Path) -> set:
        """Schema errors the original document already had for *part*."""
        if self.original_file is None:
            return set()
        import tempfile
        import zipfile

        rel_part = part.resolve().relative_to(self.unpacked_dir)
        with tempfile.TemporaryDirectory() as staging:
            staging_dir = Path(staging)
            try:
                with zipfile.ZipFile(self.original_file, "r") as archive:
                    safe_extract(archive, staging_dir)
            except (zipfile.BadZipFile, ValueError, OSError):
                return set()
            baseline_part = staging_dir / rel_part
            if not baseline_part.is_file():
                return set()
            _, errors = self._xsd_errors(baseline_part, staging_dir)
            return set(errors) if errors else set()

    def validate_file_against_xsd(self, xml_file, verbose=False):
        """Check one part against its schema, forgiving inherited errors.

        Returns ``(None, set())`` when no schema applies, ``(True, set())``
        when the part is clean or carries only pre-existing errors, and
        ``(False, errors)`` when new errors were introduced.  Infrastructure
        failures (for example a missing schema file) always count as new.
        """
        part = Path(xml_file).resolve()
        outcome, found = self._xsd_errors(part, self.unpacked_dir)
        if outcome is None:
            return None, set()
        if not found:
            return True, set()
        if any(not _schema_verdict(message) for message in found):
            return False, found
        fresh = set(found) - self._inherited_errors(part)
        fresh = {
            message
            for message in fresh
            if not any(token in message for token in _IGNORED_SCHEMA_MESSAGES)
        }
        if verbose:
            rel = self._relative(part)
            if fresh:
                print(f"FAILED - {rel}: {len(fresh)} new schema error(s)")
                for message in sorted(fresh)[:3]:
                    clipped = message if len(message) <= 250 else message[:250] + "..."
                    print(f"  - {clipped}")
            else:
                print(f"PASSED - {self._relative(part)}: only pre-existing errors")
        return (False, fresh) if fresh else (True, set())

    def check_xsd_delta(self) -> bool:
        clean = skipped = failing = 0
        problems = []
        for part in self.xml_files:
            outcome, fresh = self.validate_file_against_xsd(part)
            if outcome is None:
                skipped += 1
            elif outcome:
                clean += 1
            else:
                failing += 1
                rel = self._relative(part)
                problems.append(f"  {rel}: {len(fresh)} new schema error(s)")
                for message in sorted(fresh)[:3]:
                    clipped = message if len(message) <= 250 else message[:250] + "..."
                    problems.append(f"    - {clipped}")
        if self.verbose:
            print(f"XSD coverage: {clean} clean, {skipped} unchecked, {failing} failing")
        return self.report(
            "schema validation (differential)", problems,
            "no new schema errors relative to the original",
        )

    # ------------------------------------------------------------- repairs

    def repair_whitespace_preservation(self) -> int:
        """Mark edge-whitespace text holders with xml:space='preserve'."""
        fixed = 0
        for part in self.xml_files:
            try:
                tree = lxml.etree.parse(str(part), parser=_xml_parser())
            except (lxml.etree.XMLSyntaxError, OSError):
                continue
            touched = False
            for element in tree.getroot().iter():
                if not isinstance(element.tag, str):
                    continue
                if element.tag.rsplit("}", 1)[-1] not in _TEXT_HOLDERS:
                    continue
                text = element.text or ""
                if not text:
                    continue
                if text == text.strip(XML_SPACE):
                    continue
                if element.get(f"{{{NS_XML}}}space") == "preserve":
                    continue
                element.set(f"{{{NS_XML}}}space", "preserve")
                preview = repr(text[:30]) + ("..." if len(text) > 30 else "")
                print(
                    f"  Repaired: {part.name}: xml:space='preserve' added to"
                    f" <{element.tag.rsplit('}', 1)[-1]}>: {preview}"
                )
                fixed += 1
                touched = True
            if touched:
                tree.write(
                    str(part), xml_declaration=True, encoding="UTF-8",
                    standalone=True,
                )
        return fixed


if __name__ == "__main__":
    raise SystemExit("PackageValidator is a library; run office/validate.py instead.")
