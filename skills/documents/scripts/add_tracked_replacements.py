#!/usr/bin/env python3
"""Generate tracked-change replacements (old → new) inside a DOCX.

Enabling tracking and accepting revisions are covered elsewhere; this is the
tool that *creates* redlines. Each `--replace OLD=NEW` becomes a `<w:del>`
holding the old text followed by a `<w:ins>` holding the new, and
`<w:trackRevisions/>` is switched on in `word/settings.xml`.

Scope is deliberately narrow: only occurrences inside a single `w:t` node are
handled, and only the first match per replacement is converted. Text that Word
has split across runs is invisible to this tool — see
`troubleshooting/run_splitting.md`.

    python scripts/add_tracked_replacements.py in.docx --out out.docx \
      --replace "foo=bar" --replace "old phrase=new phrase" --author "Reviewer"
"""

from __future__ import annotations

import argparse
import datetime as dt
import zipfile

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
DOCUMENT_PART = "word/document.xml"
SETTINGS_PART = "word/settings.xml"


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def dump(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def revision_stamp() -> str:
    moment = dt.datetime.now(dt.timezone.utc).replace(microsecond=0, tzinfo=None)
    return moment.isoformat() + "Z"


def enable_tracking(settings_root: etree._Element) -> bool:
    if settings_root.find("w:trackRevisions", namespaces=NS) is not None:
        return False
    settings_root.insert(0, etree.Element(w("trackRevisions")))
    return True


def next_revision_id(document_root: etree._Element) -> int:
    """One past the highest integer `w:id` already used in the document."""
    used = []
    for element in document_root.xpath(".//*[@w:id]", namespaces=NS):
        try:
            used.append(int(element.get(w("id"))))
        except (TypeError, ValueError):
            continue
    return max(used) + 1 if used else 1


def revision_element(tag: str, text_tag: str, text: str, revision_id: int,
                     author: str, when: str) -> etree._Element:
    """One `w:del` or `w:ins` wrapper holding a single run."""
    wrapper = etree.Element(w(tag))
    wrapper.set(w("id"), str(revision_id))
    wrapper.set(w("author"), author)
    wrapper.set(w("date"), when)
    run = etree.SubElement(wrapper, w("r"))
    etree.SubElement(run, w(text_tag)).text = text
    return wrapper


def deletion(text: str, revision_id: int, author: str, when: str) -> etree._Element:
    return revision_element("del", "delText", text, revision_id, author, when)


def insertion(text: str, revision_id: int, author: str, when: str) -> etree._Element:
    return revision_element("ins", "t", text, revision_id, author, when)


def clone_properties(properties: etree._Element | None) -> etree._Element | None:
    """Deep-copy a run's `w:rPr` so split runs keep their formatting."""
    return etree.fromstring(etree.tostring(properties)) if properties is not None else None


def run_with_text(text: str, properties: etree._Element | None) -> etree._Element:
    run = etree.Element(w("r"))
    if properties is not None:
        run.append(clone_properties(properties))
    etree.SubElement(run, w("t")).text = text
    return run


def split_run_around(text_node: etree._Element, old: str, new: str, revision_id: int,
                     author: str, when: str) -> tuple[int, bool]:
    """Turn `…old…` inside one text node into before / del / ins / after."""
    text = text_node.text or ""
    if old not in text:
        return revision_id, False

    run = text_node.getparent()          # w:r
    container = run.getparent() if run is not None else None   # usually w:p
    if run is None or container is None:
        return revision_id, False

    position = container.index(run)
    before, after = text.split(old, 1)
    properties = clone_properties(run.find("w:rPr", namespaces=NS))

    replacement: list[etree._Element] = []
    if before:
        replacement.append(run_with_text(before, properties))
    replacement.append(deletion(old, revision_id, author, when))
    revision_id += 1
    replacement.append(insertion(new, revision_id, author, when))
    revision_id += 1
    if after:
        replacement.append(run_with_text(after, properties))

    for node in reversed(replacement):
        container.insert(position, node)
    container.remove(run)
    return revision_id, True


def add_tracked_replacements(in_docx: str, out_docx: str,
                             replacements: list[tuple[str, str]], author: str) -> None:
    when = revision_stamp()

    with zipfile.ZipFile(in_docx, "r") as source:
        names = source.namelist()
        document_root = etree.fromstring(source.read(DOCUMENT_PART))
        settings_root = (etree.fromstring(source.read(SETTINGS_PART))
                         if SETTINGS_PART in names else etree.Element(w("settings")))

        enable_tracking(settings_root)
        revision_id = next_revision_id(document_root)
        applied = 0

        for old, new in replacements:
            for text_node in document_root.xpath(".//w:t", namespaces=NS):
                revision_id, changed = split_run_around(
                    text_node, old, new, revision_id, author=author, when=when
                )
                if changed:
                    applied += 1
                    break  # one occurrence per replacement keeps ids predictable

        rewritten = {DOCUMENT_PART: dump(document_root), SETTINGS_PART: dump(settings_root)}

        with zipfile.ZipFile(out_docx, "w", zipfile.ZIP_DEFLATED) as destination:
            for info in source.infolist():
                name = info.filename
                payload = rewritten[name] if name in rewritten else source.read(name)
                destination.writestr(name, payload)

    print(f"[OK] wrote {out_docx} (replacements={applied})")


def parse_replacement(spec: str) -> tuple[str, str]:
    if "=" not in spec:
        raise SystemExit("--replace must be formatted as OLD=NEW")
    old, new = spec.split("=", 1)
    return old, new


def main() -> None:
    ap = argparse.ArgumentParser(description="Add tracked replacement edits (best-effort)")
    ap.add_argument("in_docx")
    ap.add_argument("--out", required=True)
    ap.add_argument("--author", default="Editor")
    ap.add_argument(
        "--replace",
        action="append",
        default=[],
        help="Replacement formatted as OLD=NEW (repeatable)",
    )
    args = ap.parse_args()

    replacements = [parse_replacement(spec) for spec in args.replace]
    if not replacements:
        raise SystemExit("Provide at least one --replace")

    add_tracked_replacements(args.in_docx, args.out, replacements, author=args.author)


if __name__ == "__main__":
    main()
