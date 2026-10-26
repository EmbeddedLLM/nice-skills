# PPTX package editing and validation

Run from this skill directory. Python 3.10+; install `python -m pip install -r scripts/requirements-office.txt`. Thumbnail rendering also needs local LibreOffice Impress and Poppler (`soffice`, `pdftoppm`). All routes use free local tools.

## Add a slide or instantiate a layout

```bash
python scripts/add_slide.py input.pptx slide2.xml --after slide2.xml --output edited.pptx
python scripts/add_slide.py input.pptx slideLayout3.xml --output from-layout.pptx
```

Slide filenames identify package parts, not visual positions. The helper inserts into the presentation's slide list, allocates IDs, and updates content types and relationships. A new layout slide inherits the layout but starts without copied placeholders; add content explicitly. A duplicated slide retains content and layout but omits speaker notes. Its charts, embedded workbooks, SmartArt, and media remain shared: clone and reconnect those parts separately if independent edits are required.

Packed inputs require a new output path. Unpacked working directories are modified in place; keep the source package separately. The helpers use namespace-aware XML rather than relying on `p:` or `r:` spelling.

## Remove unused parts

After removing slide entries from `ppt/presentation.xml`:

```bash
python scripts/clean.py edited.pptx                         # preview removals
python scripts/clean.py edited.pptx --output cleaned.pptx
python scripts/clean.py unpacked-working-copy/ --apply      # explicit directory mutation
```

Cleanup removes unlisted presentation-slide relationships and follows the remaining package relationship graph. Shared/reachable resources survive; unreachable parts and their content-type overrides are pruned. A removed slide still reached by a hyperlink can remain in the package. The tool refuses unresolved live relationships before mutation. Cleanup does not repair custom shows, sections, or other semantic references after slide deletion; update those explicitly and validate the result. Use a disposable copy for unpacked editing.

## Structural and chart checks

```bash
python scripts/office/validate.py edited.pptx
python scripts/office/validate.py edited.pptx --original original.pptx
```

Checks include selected XSD schemas, relationships, content types, IDs, notes/layout links, shared master themes, stacked-bar label placement, and chart-axis references. `--original` discounts inherited schema defects. Exit `0` means the implemented checks passed, `1` means validation failed, and `2` is an input/operational failure. Optional `--auto-repair --output NEW.pptx` handles supported whitespace repairs in a temporary copy, publishing only after validation passes.

Schemas cover selected standard parts and strip extension namespaces for those checks; chart checks cover selected compatibility constraints. They do not establish exhaustive OOXML compliance or identical rendering in Microsoft PowerPoint, so keep rendering and inspecting the deck after every structural edit.

## Thumbnails with package identity

```bash
python scripts/thumbnail.py edited.pptx review/contact --cols 3
```

`--cols` must be positive; values above six are clamped to six with a warning. Produces JPEG contact sheets labeled with actual slide XML filenames in presentation order. Hidden slides receive labeled placeholders when the renderer omits them, or labeled rendered thumbnails when included. A page-count mismatch fails instead of attaching misleading labels. This complements the existing generic image montage helper.

Core-properties metadata is checked for XML/package integrity but skipped for XSD validation: the supplied core schema imports unbundled remote Dublin Core schemas. The bundled schema dependency closure is local, and missing required schemas are errors. No network schema downloads occur.
