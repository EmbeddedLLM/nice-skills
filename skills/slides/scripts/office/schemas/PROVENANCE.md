# Schema provenance

The XSD files in this directory are unmodified electronic inserts of the respective published standards, fetched from the standards bodies on 2026-10-16:

- `ecma376-transitional/` — ECMA-376 Part 4, 5th edition (December 2016), annex `OfficeOpenXML-XMLSchema-Transitional.zip`, downloaded from ecma-international.org. ECMA-376-4 5th ed. is technically aligned with ISO/IEC 29500-4:2016.
- `ecma376-opc/` — ECMA-376 Part 2, 5th edition (December 2021), annex `OpenPackagingConventions-XMLSchema.zip`, downloaded from ecma-international.org.

The validator loads these through a scratch mirror that fills in the location-less XML-namespace imports (see `_schema_work_tree` in `validators/base.py`); the files here are never modified.
