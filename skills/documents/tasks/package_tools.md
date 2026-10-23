# DOCX package tools

Run from this skill directory. Python 3.10+ is required. Install the optional XML dependencies with `python -m pip install -r scripts/requirements-office.txt`. Revision acceptance also needs local LibreOffice Writer (`soffice` on PATH); no paid Office license or service is required.

## Normalize split runs

```bash
python scripts/merge_runs.py input.docx --output merged.docx
```

Merges adjacent text-only runs with identical properties, removes proofing markers and revision-session attributes, and preserves revision-wrapper boundaries. Only `word/document.xml` is processed. Fields, drawings, breaks, and different run attributes prevent merging. Use a new output path, then render and inspect; normalization is optional, not a prerequisite for every edit. An unpacked working directory is edited in place.

## Comments and replies

For ordinary anchored comments, use the existing `comments_add.py` workflow. For modern comment parts and reply metadata:

```bash
python scripts/comment.py input.docx 'Review this clause' --author 'Editor' --output comments.docx
python scripts/comment.py comments.docx 'Reply text' --parent 0 --author 'Editor' --output replies.docx
```

This low-level helper creates comment definitions, relationships, and modern metadata. **It does not insert body anchors.** Add the printed `commentRangeStart`, `commentRangeEnd`, and `commentReference` markup around the intended runs before delivery; otherwise the comment can remain invisible. Comment IDs are allocated automatically; duplicate explicit IDs fail. The default author is `User`; pass the actual requested author. `--raw` accepts an XML fragment and is only for deliberately prepared markup. Existing modern parts must use the source tool's conventional Word prefixes; use targeted namespace-aware editing for differently serialized comment parts.

## Accept revisions through LibreOffice

```bash
python scripts/accept_changes.py tracked.docx accepted.docx --timeout 60
```

Uses an isolated temporary profile and copied input, runs LibreOffice's acceptance command, then checks for remaining revision markup before publishing a new file. Timeout, failed conversion, or remaining revisions returns failure without publishing. LibreOffice may change formatting or unsupported features: compare against the source and render the output. The existing `accept_tracked_changes.py` remains useful for report/reject and targeted XML operations; it is not a complete Word revision engine.

## Validate a package

```bash
python scripts/office/validate.py edited.docx
python scripts/office/validate.py edited.docx --original original.docx --author 'Editor'
python scripts/office/validate.py edited.docx --auto-repair --output repaired.docx
```

Normal validation is read-only. It checks XML, selected bundled XSD schemas, relationships, content types, identifiers, whitespace, and comment markers. `--original` discounts inherited schema errors; use the first command to inspect all reported schema errors. For example, python-docx's default template can omit the XSD-required zoom percentage; that is distinct from a rendering failure.

`--author` enables the additional body-text comparison: undo new `w:ins`/`w:del` changes and compare against the original. The author flag enables this check; it does not filter out edits by other authors. It does not prove preservation of headers, footers, notes, formatting, fields, paragraph joins, or every Word revision kind.

Repair is opt-in and requires a new packed output. It addresses whitespace and selected IDs; a repaired file is published only if validation passes. Exit `0` means the implemented checks passed, `1` means validation failed, and `2` means invalid input or an operational error. These are selective structural checks, not a full Office conformance certificate or a replacement for rendering.

Core-properties metadata is checked for XML/package integrity but skipped for XSD validation: the supplied core schema imports unbundled remote Dublin Core schemas. The bundled schema dependency closure is local, and missing required schemas are errors. No network schema downloads occur.

## Targeted package editing library

The rewritten form, note, stamp, style, and audit helpers share `scripts/word_package.py`. It requires `lxml` and has no command-line interface. `Package(path)` reads a DOCX without extracting it; `xml(name)` and `put_xml(name, root)` read or replace individual parts. `document_part(kind, fallback)` resolves an existing singleton part through its document relationship, including normalized relative or package-absolute targets. Ambiguous, external, or missing targets are errors. `register(name, kind)` supplies a document relationship and content-type override for a newly added Word part and refuses conflicting singleton bindings. `save(output)` preserves untouched member bytes, ZIP metadata, and the archive comment, then atomically replaces the destination. XML or write failures propagate without publishing a partial archive. Keep this module beside the scripts when copying the skill.

This narrow writer does not resolve cross-document identifiers, evaluate fields, or guarantee visual fidelity. Use it for explicit part-level edits after inspecting the package, then run the relevant structural and rendering checks.
