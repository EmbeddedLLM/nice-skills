"""ZIP/XML plumbing shared by the document tooling in this package.

Archive handling is deliberately defensive: unpacking validates every member
before anything is written to disk, and repacking goes through a temporary
file that is atomically renamed into place, so an interrupted run never
leaves a half-written document behind.
"""

from __future__ import annotations

import os
import posixpath
import re
import stat
import tempfile
import urllib.parse
import zipfile
from pathlib import Path

__all__ = [
    "XML_SPACE",
    "rendered_text",
    "opc_target",
    "rels_source_part",
    "safe_extract",
    "rezip",
]

# Boundary whitespace that XML consumers may collapse when xml:space is absent.
XML_SPACE = " \t\r\n"

_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def rendered_text(text: str, preserve: bool) -> str:
    """Text as a word processor renders it.

    Unless xml:space="preserve" applies, whitespace at either edge of a text
    element never reaches the page.
    """
    return text if preserve else text.strip(XML_SPACE)


def opc_target(target: str, source_part: str, target_mode: str = "") -> str | None:
    """Resolve a relationship *target* to a normalised part path in the package.

    Returns ``None`` for references that live outside the package (external
    mode or absolute URI).  Raises ``ValueError`` when the target cannot name
    a package part: backslashes, ``..`` escaping the root, or an empty result.
    """
    if not target or target_mode.lower() == "external" or _URI_SCHEME.match(target):
        return None

    decoded = urllib.parse.unquote(target)
    if "\\" in decoded:
        raise ValueError(f"not a POSIX part name: {target!r}")

    if decoded.startswith("/"):
        candidate = decoded.lstrip("/")
    else:
        candidate = posixpath.join(posixpath.dirname(source_part), decoded)

    resolved: list[str] = []
    for segment in candidate.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if not resolved:
                raise ValueError(f"target escapes the package root: {target!r}")
            resolved.pop()
        else:
            resolved.append(segment)

    if not resolved:
        raise ValueError(f"target names no part: {target!r}")
    return "/".join(resolved)


def rels_source_part(rels_file: Path, unpacked_dir: Path) -> str:
    """Part that owns a ``_rels/*.rels`` file, e.g. ``word/document.xml``."""
    rel = Path(rels_file).relative_to(Path(unpacked_dir))
    owner_dir = rel.parent.parent.as_posix()  # step out of `_rels`
    stem = rel.name[: -len(".rels")]
    return stem if owner_dir == "." else posixpath.join(owner_dir, stem)


def safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    """Extract *archive* under *destination*, but only if every member is safe.

    All members are vetted before the first byte is written: no absolute or
    scheme-qualified names, no backslashes, no ``..`` segments, no symlinks,
    no duplicates, and nothing that resolves outside *destination*.
    """
    destination = Path(destination).resolve()
    planned: set[Path] = set()
    for member in archive.infolist():
        name = member.filename
        if (
            name.startswith(("/", "\\"))
            or "\\" in name
            or _URI_SCHEME.match(name)
            or ".." in name.split("/")
            or stat.S_ISLNK(member.external_attr >> 16)
        ):
            raise ValueError(f"refusing unsafe archive member: {name!r}")
        final = (destination / name).resolve()
        if not final.is_relative_to(destination):
            raise ValueError(f"archive member escapes destination: {name!r}")
        if final in planned:
            raise ValueError(f"duplicate archive member: {name!r}")
        planned.add(final)
    archive.extractall(destination)


def rezip(source_dir: Path, package_path: Path) -> None:
    """Rebuild a packed document from *source_dir* and publish it atomically.

    ``[Content_Types].xml`` is written first and stored uncompressed; all
    other members follow in sorted order.  An existing destination keeps its
    permission bits; a new one honours the process umask.
    """
    source_dir = Path(source_dir)
    package_path = Path(package_path)
    content_types = source_dir / "[Content_Types].xml"
    members = sorted(p for p in source_dir.rglob("*") if p.is_file())

    handle, staging_name = tempfile.mkstemp(
        prefix=f"{package_path.name}.", suffix=".part", dir=package_path.parent
    )
    staging = Path(staging_name)
    try:
        with os.fdopen(handle, "wb") as raw:
            with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as archive:
                if content_types.is_file():
                    archive.write(
                        content_types, "[Content_Types].xml",
                        compress_type=zipfile.ZIP_STORED,
                    )
                for member in members:
                    if member == content_types:
                        continue
                    archive.write(member, member.relative_to(source_dir).as_posix())
        if package_path.exists():
            permissions = stat.S_IMODE(package_path.stat().st_mode)
        else:
            current_umask = os.umask(0)
            os.umask(current_umask)
            permissions = 0o666 & ~current_umask
        os.chmod(staging, permissions)
        os.replace(staging, package_path)
    finally:
        staging.unlink(missing_ok=True)
