## Working from screenshots or reference images

- Given a reference image or screenshot, pick data formats that suit the workbook's topic, audience, and purpose (number formats, date formats) rather than imitating the rendered look with plain text. Numbers and dates stay usable even when the screenshot renders locale punctuation or currency symbols.
- Formulas where they belong: when recreating from a screenshot, do not bulk-write every numeric table as static values. First separate clearly formula-derived ranges: probe adjacent numeric rows/columns for exact repeated relationships (sums, differences, products, ratios, constant multiples). Inputs stay hardcoded; derived ranges become formulas.
- Match the visible styling, but never read intentional formatting into ambiguous image artifacts (zoom, antialiasing, compression). Infer bold only from relative contrast or clear semantics; when every visible text looks the same weight, keep normal weight.
