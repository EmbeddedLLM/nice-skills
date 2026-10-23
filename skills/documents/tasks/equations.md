# Mathematical content in editable documents

Begin with the user's editing needs and the source representation. Preserve existing native Word equations when revising a DOCX. An equation image can be suitable for a fixed visual deliverable, but it does not provide native equation editing, searchable symbols, or an accessible mathematical reading order.

The [document production sources](../SOURCES.md) emphasize preserving native structure and identifying conversion losses. Apply that distinction to equations: clarify whether the recipient must revise notation, copy expressions, or use assistive technology. Do not replace native math with pictures simply because image generation is easier.

## Native route

Word stores structured mathematics as OMML, typically `m:oMath` for inline expressions or `m:oMathPara` for display content. Use a tested writer or converter that emits this structure, retaining an editable source for further corrections. Inspect the package to confirm the equation is native; plain LaTeX text, a screenshot, or an embedded SVG is not OMML.

Check fractions, limits, matrices, accents, and symbol variants against the approved source. Test a representative edit in a compatible application when available. An XML check alone cannot establish editability or screen-reader behavior in a particular application. If no suitable native conversion is available, state that limitation before substituting another representation.

## Rendered route

When a picture is an acceptable deliverable, keep the formula source alongside the output. The optional [equation runtime](../equation-runtime/) pins MathJax and Sharp dependencies. Copy it into a writable working directory and run `npm ci` there; installation needs registry access unless cached. Do not modify the bundled lockfile to install an arbitrary newer dependency.

Use MathJax's TeX input and SVG output to produce a vector expression, then rasterize through Sharp only if the destination requires PNG. Set the intended ink color, transparent background, physical placement size, and enough raster resolution for that size. Resolve SVG units and font references explicitly instead of relying on the recipient's environment. Inspect the rendered result before inserting it with `python-docx` at an explicit width.

Provide an appropriate text explanation or alternative description. A filename used as alt text does not communicate a mathematical expression. If notation itself is the task's subject, showing source LaTeX may be appropriate; otherwise remove unintended source-code artifacts from the reader-facing document.

## Final checks

Compare all symbols and values with the source, then inspect the saved page render at reading size and at detail scale. Check baseline alignment for inline math, display spacing, clipping, line breaks, legibility, and captions or equation numbers. Confirm that the final PDF, when requested, preserves the intended appearance. Report the representation, retained source, and any editor or accessibility behavior that was not tested.
