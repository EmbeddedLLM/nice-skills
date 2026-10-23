# Diagnose before modifying

Use preflight to gather evidence about opening failures, scans, forms and fonts:

```sh
python scripts/pdf_preflight.py source.pdf --json
```

The report contains `encrypted`, `ok_open`, `likely_scanned`, `xfa_present` and `warnings`. A successful command can still report an unusable PDF; inspect the fields. With authorized credentials, `--password` allows inspection of encrypted content. `encrypted` continues to describe the input even after authentication. A missing or incorrect password results in warnings and `ok_open: false`.

Choose a response based on the evidence:

- A likely scan needs a visual check, then OCR if searchable text is required.
- An XFA indication needs a compatible form workflow; AcroForm success does not establish XFA support.
- Missing font data needs the correct font or a regenerated source document.
- A damaged object/xref structure may justify `pdf_edit.py repair` on a separate copy when the original remains readable enough for recovery.

Do not run optimization automatically for every warning. A rewrite can discard features and cannot reconstruct missing content. If repair is necessary, compare page count, text, annotations, fields, metadata and renders against the best available source. Describe anything that cannot be checked.

This helper is not a print-production, PDF/A or accessibility conformance validator. Such requirements need dedicated checks and the intended output profile; do not infer compliance from an empty warning list.
