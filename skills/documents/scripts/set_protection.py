#!/usr/bin/env python3
"""Turn Word's "Restrict Editing" modes on or off in a DOCX.

The flag lives in `word/settings.xml` as `<w:documentProtection …/>`. Only the
simple, password-free modes are handled:

    off | readOnly | comments | trackedChanges | forms

Ergonomic spellings are accepted for the two camelCase modes (`read_only`,
`read-only`, `readonly`, `tracked_changes`, `tracked-changes`). A package with
no settings part gets one, and `[Content_Types].xml` is updated to declare it.

    python scripts/set_protection.py in.docx --mode readOnly --out out.docx
    python scripts/set_protection.py in.docx --mode off --out out.docx
"""

from __future__ import annotations

import argparse
import zipfile

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"w": W_NS, "ct": CT_NS}

SETTINGS_PART = "word/settings.xml"
CONTENT_TYPES_PART = "[Content_Types].xml"
SETTINGS_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"
)

MODE_ALIASES = {
    "off": "off",
    "readonly": "readOnly",
    "read_only": "readOnly",
    "comments": "comments",
    "trackedchanges": "trackedChanges",
    "tracked_changes": "trackedChanges",
    "forms": "forms",
}


def parse(archive: zipfile.ZipFile, name: str) -> etree._Element:
    return etree.fromstring(archive.read(name))


def dump(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def canonical_mode(raw: str) -> str:
    """Normalise a user-supplied mode name, or explain what is valid."""
    normalised = "_".join(part for part in raw.strip().replace("-", "_").split() if part).lower()
    if normalised not in MODE_ALIASES:
        raise SystemExit(
            f"[set_protection] invalid --mode={raw!r}. Use off, readOnly, comments, "
            "trackedChanges, forms (aliases: read_only, tracked_changes)."
        )
    return MODE_ALIASES[normalised]


def settings_root_or_new(archive: zipfile.ZipFile) -> etree._Element:
    if SETTINGS_PART in archive.namelist():
        return parse(archive, SETTINGS_PART)
    return etree.Element(f"{{{W_NS}}}settings", nsmap={"w": W_NS})


def declare_settings(content_types: etree._Element) -> bool:
    for override in content_types.findall(f"{{{CT_NS}}}Override"):
        if override.get("PartName") == f"/{SETTINGS_PART}":
            if override.get("ContentType") == SETTINGS_CONTENT_TYPE:
                return False
            override.set("ContentType", SETTINGS_CONTENT_TYPE)
            return True

    added = etree.SubElement(content_types, f"{{{CT_NS}}}Override")
    added.set("PartName", f"/{SETTINGS_PART}")
    added.set("ContentType", SETTINGS_CONTENT_TYPE)
    return True


def apply_mode(settings: etree._Element, mode: str) -> bool:
    """Replace any existing protection element with the requested mode."""
    edited = False
    for existing in list(settings.xpath(".//w:documentProtection", namespaces=NS)):
        existing.getparent().remove(existing)
        edited = True

    if mode == "off":
        return edited

    protection = etree.Element(f"{{{W_NS}}}documentProtection")
    protection.set(f"{{{W_NS}}}edit", mode)
    protection.set(f"{{{W_NS}}}enforcement", "1")  # without this Word ignores the mode
    protection.set(f"{{{W_NS}}}formatting", "0")   # formatting stays unlocked
    settings.insert(0, protection)
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_docx")
    ap.add_argument(
        "--mode",
        required=True,
        help="Protection mode: off | readOnly | comments | trackedChanges | forms "
             "(aliases accepted: read_only, read-only, readonly, tracked_changes, tracked-changes)",
    )
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    mode = canonical_mode(str(args.mode))

    with zipfile.ZipFile(args.in_docx, "r") as source:
        settings = settings_root_or_new(source)
        content_types = parse(source, CONTENT_TYPES_PART)

        rewritten: dict[str, bytes] = {}
        if apply_mode(settings, mode):
            rewritten[SETTINGS_PART] = dump(settings)
        if declare_settings(content_types):
            rewritten[CONTENT_TYPES_PART] = dump(content_types)

        existing = {info.filename for info in source.infolist()}
        with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as destination:
            for name in source.namelist():
                payload = rewritten[name] if name in rewritten else source.read(name)
                destination.writestr(name, payload)
            for name, payload in rewritten.items():
                if name not in existing:
                    destination.writestr(name, payload)

    print(f"[OK] wrote {args.out} (mode={mode})")


if __name__ == "__main__":
    main()
