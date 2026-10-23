# Task: restrict editing (document protection)

## Goal

Set Word's protection flags in `word/settings.xml` so the file opens as read-only, comments-only, tracked-changes-only, or forms-only. Typical reasons: shipping a template that should not be casually edited, or forcing reviewers to comment rather than rewrite.

## Setting a mode

```bash
python scripts/set_protection.py input.docx --mode readOnly        --out protected.docx
python scripts/set_protection.py input.docx --mode comments        --out comments_only.docx
python scripts/set_protection.py input.docx --mode trackedChanges  --out tc_only.docx
python scripts/set_protection.py input.docx --mode forms           --out forms_only.docx
```

Aliases are accepted for the two multi-word modes: `read_only`, `read-only`, `readonly`, `tracked_changes`, `tracked-changes`.

## Clearing protection

```bash
python scripts/set_protection.py input.docx --mode off --out unprotected.docx
```

`--out` is required in every case; the input is never modified.

## Verifying

Layout must be untouched, so a render is the check:

```bash
python render_docx.py protected.docx --output_dir out_protected
```

Then open the file in Word and confirm the editing restriction actually shows in the Reviewing pane.

## Pitfalls

- Enforcement is Word's. Some viewers ignore protection entirely, so this is a guardrail for cooperating editors, not a security control.
- Password protection is deliberately not implemented: high complexity, low return.
- A package with no `word/settings.xml` is fine — the helper creates one.
