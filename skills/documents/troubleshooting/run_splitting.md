# Troubleshooting: run splitting

## Why a plain find-and-replace misses

Word does not store a paragraph as one string. Proofing boundaries, style changes, spell-check marks, fields, and revision history all cause it to break a sentence into several `<w:r>` runs, so the phrase you can read in the document may be spread across three of them. Reading paragraph text and searching it will find the phrase; writing the replacement back through that same path will not.

## Ways to work with it

- Stay at run level. Read and write `<w:t>` inside `<w:r>`, and accept that a target string may straddle two runs — in that case handle the pair.
- If you control the authoring step, plant a marker. Writing a distinctive hidden run while generating the document gives you something unambiguous to locate later when you patch the OOXML.
- For tracked replacements, do not try to rewrite text in place. Wrap the exact runs you want gone in `<w:del>` and put the new content in an adjacent `<w:ins>`.

## What the patcher gives you

`scripts/docx_ooxml_patch.py` has the two operations this usually needs:

- find paragraphs with a simple predicate such as "is indented" or "contains this substring";
- replace the _n_-th tracked insertion inside a paragraph, addressed by its `w:id`.
