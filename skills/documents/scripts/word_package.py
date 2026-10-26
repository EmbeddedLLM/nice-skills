"""Local OOXML primitives for targeted, atomic DOCX edits (Python + lxml).

Package reads ZIP members without extraction. Call xml()/put_xml() for changed
parts, register() for a new document-owned part, then save(). Untouched member
bytes, ZIP entry metadata, and the archive comment survive. A failed write never
replaces the destination. This module has no CLI or network access.
"""

from copy import deepcopy
import os
import re
import posixpath
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

from lxml import etree as X

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
DOCUMENT = "word/document.xml"


def tag(local):
    return "{" + W + "}" + local


def element(local, **attributes):
    return X.Element(tag(local), {tag(k): str(v) for k, v in attributes.items()})


def text_of(node):
    return "".join(n.text or "" for n in node.iter(tag("t")))


def text_run(value, properties=None):
    run = element("r")
    if properties is not None:
        run.append(deepcopy(properties))
    text = X.SubElement(run, tag("t"))
    text.text = value
    if value and (value[0].isspace() or value[-1].isspace()):
        text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return run


class Package:
    def __init__(self, source):
        with zipfile.ZipFile(source) as archive:
            self.entries = archive.infolist()
            self.comment = archive.comment
            self.parts = {entry.filename: archive.read(entry) for entry in self.entries}

    def xml(self, name):
        return X.fromstring(self.parts[name], X.XMLParser(resolve_entities=False, no_network=True))

    def put_xml(self, name, root):
        self.parts[name] = X.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)

    def stories(self, include_headers=True):
        return [name for name in self.parts if name == DOCUMENT or
                (include_headers and re.fullmatch(r"word/(header|footer)\d+\.xml", name))]

    def document_part(self, kind, fallback):
        """Locate a singleton document part; ambiguous or broken bindings fail closed."""
        relpath = "word/_rels/document.xml.rels"
        if relpath not in self.parts:
            return fallback
        matches = [rel for rel in self.xml(relpath) if rel.get("Type") == R + "/" + kind]
        if not matches:
            return fallback
        if len(matches) != 1:
            raise ValueError(f"Ambiguous document relationship for {kind}")
        rel = matches[0]
        target = urlsplit(rel.get("Target", ""))
        if rel.get("TargetMode") == "External" or target.scheme or target.netloc or target.query or target.fragment:
            raise ValueError(f"Unsupported external or qualified relationship for {kind}")
        path = unquote(target.path)
        name = posixpath.normpath(path.lstrip("/") if path.startswith("/") else posixpath.join("word", path))
        if not path or name == ".." or name.startswith("../") or name not in self.parts:
            raise ValueError(f"Missing document part for {kind}: {name}")
        return name

    def register(self, name, kind):
        """Register a standard Word part and return its document relationship ID."""
        if kind not in ("header", "footer") and self.document_part(kind, name) != name:
            raise ValueError(f"Conflicting document relationship for {kind}")
        mime = ("application/vnd.openxmlformats-officedocument.theme+xml" if kind == "theme"
                else f"application/vnd.openxmlformats-officedocument.wordprocessingml.{kind}+xml")
        types = self.xml("[Content_Types].xml")
        override = next((n for n in types if n.get("PartName") == "/" + name), None)
        if override is None:
            override = X.SubElement(types, "{" + CT + "}Override", PartName="/" + name)
        if override.get("ContentType") != mime:
            override.set("ContentType", mime)
            self.put_xml("[Content_Types].xml", types)
        relpath = "word/_rels/document.xml.rels"
        rels = self.xml(relpath) if relpath in self.parts else X.Element("{" + REL + "}Relationships", nsmap={None: REL})
        target = posixpath.relpath(name, "word")
        for rel in rels:
            old_target = unquote(urlsplit(rel.get("Target", "")).path)
            normalized = posixpath.normpath(old_target.lstrip("/") if old_target.startswith("/") else posixpath.join("word", old_target))
            if rel.get("Type") == R + "/" + kind and normalized == name and rel.get("TargetMode") != "External":
                return rel.get("Id")
        taken = {rel.get("Id") for rel in rels}
        number = 1
        while f"rId{number}" in taken:
            number += 1
        rid = f"rId{number}"
        X.SubElement(rels, "{" + REL + "}Relationship", Id=rid, Type=R + "/" + kind, Target=target)
        self.put_xml(relpath, rels)
        return rid

    def save(self, destination):
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, staging = tempfile.mkstemp(prefix=".docx-", suffix=".tmp", dir=path.parent)
        os.close(fd)
        try:
            with zipfile.ZipFile(staging, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.comment = self.comment
                written = set()
                for entry in self.entries:
                    if entry.filename in self.parts:
                        archive.writestr(entry, self.parts[entry.filename])
                        written.add(entry.filename)
                for name, payload in self.parts.items():
                    if name not in written:
                        archive.writestr(name, payload)
            os.replace(staging, path)
        finally:
            if os.path.exists(staging):
                os.unlink(staging)
