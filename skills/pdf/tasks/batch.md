# Apply one operation across a collection

List the actual inputs first and choose a separate output root for each run. Check for identical basenames: the helper organizes results by filename, so inputs from different folders can collide. Narrow the glob or process separate collections when filenames are ambiguous. Do not assume the output root is empty.

```sh
python scripts/batch_pdf.py inspect --in_glob 'incoming/**/*.pdf' --out_root review/inventory
python scripts/batch_pdf.py render --in_glob 'incoming/**/*.pdf' --out_root review/pages --dpi 120
python scripts/batch_pdf.py normalize --in_glob 'incoming/**/*.pdf' --out_root review/rewritten
```

Quote the glob so the helper expands it. Inspect writes JSON per input; render writes page images below per-input directories; normalize rewrites PDFs using the edit helper. Install prerequisites for the chosen operation. No-match input is an error, and inspection records may contain per-file errors: read those records rather than treating process completion as full success.

Run one representative file first, including an encrypted, scanned or unusually sized example when present. Normalization is a rewrite, not a universal repair step. Identify features that must survive and compare them on the sample before scaling up.

Reconcile input and output counts, log failures, and review changed or anomalous files. For visual review, use contact sheets to locate issues and full-size pages to judge them. State exactly which files succeeded and which remain unresolved.
