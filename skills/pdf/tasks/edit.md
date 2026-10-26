# Make the requested PDF change

Before choosing an operation, record what the output must retain: page order, interactive fields, annotations, attachments, bookmarks, metadata, or signatures. Work on a separate output path. Rewriting a signed document can invalidate its signature; retain the signed original and describe that limitation.

`pdf_edit.py` uses pypdf for page and catalog changes, ReportLab for pagination, and PyMuPDF for repair/optimization. Install the dependencies for the selected operation. The command's `--help` lists its arguments.

| Intent                      | Invocation from this skill directory                                                       |
| --------------------------- | ------------------------------------------------------------------------------------------ |
| Combine files in order      | `python scripts/pdf_edit.py merge first.pdf second.pdf -o combined.pdf`                    |
| One file per page           | `python scripts/pdf_edit.py split source.pdf --out_dir review/pages`                       |
| Keep an ordered subset      | `python scripts/pdf_edit.py select source.pdf --pages 2,4-6 -o excerpt.pdf`                |
| One file per range          | `python scripts/pdf_edit.py extract source.pdf --ranges 2-4,6 --out_dir review/ranges`     |
| Turn selected pages         | `python scripts/pdf_edit.py rotate source.pdf --pages 2 --angle 90 -o turned.pdf`          |
| Change the visible boundary | `python scripts/pdf_edit.py crop source.pdf --inset 8mm -o trimmed.pdf`                    |
| Add a PDF overlay           | `python scripts/pdf_edit.py watermark source.pdf --watermark stamp.pdf -o marked.pdf`      |
| Add page labels             | `python scripts/pdf_edit.py paginate source.pdf --format '{page}/{total}' -o numbered.pdf` |

Page specifications are one-based. Selection removes duplicates and ignores out-of-range pages; inspect the resulting page list before delivery. Extract accepts reversed range endpoints. Split names are `source_p001.pdf`; range names are `source_p002-p004.pdf`. Subsets create new documents and require separate checks for retained forms and navigation. Full-document edits clone the catalog, but preservation still needs checking in the actual output.

Cropping changes visibility, not the underlying content. `--box` takes four bottom-left PDF coordinates. Uniform insets are measured from MediaBox and need `pt`, `in`, `cm`, or `mm`; empty or reversed crop rectangles fail. Pagination supports `br/bc/bl/tr/tc/tl` positions plus explicit `--x` and `--y`. Inspect text widths, existing footers, rotation, and mixed page dimensions.

Encryption uses `encrypt --user_password ...` with optional `--owner_password`; `decrypt --password ...` requires authorized credentials. Password arguments may be exposed in shell history or process listings: use a suitable local environment. A wrong password must fail without producing a decrypted result.

`repair source.pdf -o recovered.pdf` and `optimize source.pdf -o compact.pdf` rewrite using PyMuPDF. Optimization also offers `--recover`, `--optimize_streams`, `--compress_streams`, and `--linearize`; backend/version limitations can reject options. A rewrite cannot restore absent fonts or missing original content.

For interactive forms use [the form workflow](forms_annotations.md). The Python `fill-form source.pdf values.json -o completed.pdf` route takes a JSON **file**; check both values and appearances. This compatibility route warns and continues when appearance updates fail; saved output alone is not proof of a successful fill.

Reopen every result, compare page count/order and retained catalog features, and [compare renders](compare.md). Inspect changed pages at reading size. Keep the editable source when later revisions matter; the PDF is the reading deliverable.
