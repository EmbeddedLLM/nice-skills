# Exercise the local PDF toolchain

Run these checks from this skill directory with the selected dependencies already installed. Use absolute scratch paths, especially for the redaction harness. Only synthetic documents are generated; no user PDF is required.

```sh
python scripts/edit_smoketest.py --workdir /tmp/pdf-check-edit --dpi 72
python scripts/forms_smoketest.py --workdir /tmp/pdf-check-forms --dpi 72
python scripts/redact_smoketest.py --workdir /tmp/pdf-check-redact --dpi 72
```

The edit check creates `in.pdf`, writes `paginated.pdf`, verifies page labels and source preservation, then renders a page. The form check requires the prepared Node package: it fills and flattens a synthetic form, checks flattened text and field removal, and compares the rendered result with the original. It does not install dependencies. The redaction check requires PyMuPDF and checks both removal and rendering. Each check exits nonzero on an unmet assertion or failed subprocess and leaves artifacts for diagnosis.

Open the retained images to assess actual appearance. Programmatic success cannot establish readable typography, correct target-viewer behavior or suitability for a particular real form. For a user document, repeat the relevant workflow with its preservation requirements and record any unsupported features.

For a comparison-only check, reuse the synthetic edit artifact:

```sh
python scripts/compare_renders.py /tmp/pdf-check-edit/in.pdf /tmp/pdf-check-edit/paginated.pdf --out_dir /tmp/pdf-check-diff --dpi 72 --save_renders
```

Expect both pages to differ where labels were added. Review the report and images rather than treating any nonzero pixel difference as an automatic regression.
