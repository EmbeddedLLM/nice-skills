"""Contract tests for the ``pdf`` skill's tooling.

The package documents a pipeline — inspect, extract, edit, redact, render,
compare — plus a forms workflow that goes from a rendered page to validated
bounding boxes to stamped output, and three end-to-end smoke tests.  These
tests drive each entrypoint against generated PDFs and assert:

* the JSON/CSV shapes the skill promises (``pdf_inspect --json``,
  ``compare_renders`` summaries, ``extract_form_structure`` output);
* that structural edits produce the requested page geometry and never touch
  the input;
* that redaction is *true* redaction — the text is gone from the content
  stream, not merely covered;
* the validation gate in ``check_bounding_boxes.py`` and the
  "reject everything, write nothing" rule shared by the form tools;
* the documented failure mode of every converter whose backend is absent.

The Node helpers under ``skills/pdf/js`` are exercised through a real Node
interpreter and skip when their ``node_modules`` are not installed.
"""

from __future__ import annotations

import csv
import json
import os
import runpy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fitz
from PIL import Image
from pypdf import PdfReader, PdfWriter

from skill_scripts import (
    SKILLS,
    ScriptCase,
    binary,
    module_available,
    node_modules_ready,
    require_module,
)

PDFS = SKILLS / "pdf"
SCRIPTS = PDFS / "scripts"
JS = PDFS / "js"

HAVE_POPPLER = binary("pdftoppm") is not None
HAVE_NODE = binary("node") is not None
HAVE_NODE_DEPS = node_modules_ready(JS)
HAVE_SOFFICE = binary("soffice") is not None or binary("libreoffice") is not None
HAVE_PANDOC = binary("pandoc") is not None
HAVE_LATEX = binary("latexmk") is not None or binary("pdflatex") is not None


@require_module("fitz")
class PdfFixtureMixin:
    """Builders for the small PDFs the suites share."""

    SECRET = "ada@example.com"
    OTHER_SECRET = "123-45-6789"

    def make_pdf(self, name="base.pdf", pages=3, size=(612, 792)):
        from reportlab.pdfgen import canvas

        path = self.work / name
        writer = canvas.Canvas(str(path), pagesize=size)
        for index in range(pages):
            writer.setFont("Helvetica", 12)
            writer.drawString(72, 700, f"Page {index + 1} heading")
            writer.drawString(
                72, 680, f"Contact {self.SECRET} and SSN {self.OTHER_SECRET} here."
            )
            writer.showPage()
        writer.save()
        return path

    def make_form(self, name="form.pdf"):
        """A one-page AcroForm with a text field and a checkbox."""
        path = self.work / name
        doc = fitz.open()
        page = doc.new_page(width=612, height=792)
        text = fitz.Widget()
        text.field_name = "Name"
        text.field_type = fitz.PDF_WIDGET_TYPE_TEXT
        text.rect = fitz.Rect(80, 100, 300, 120)
        page.add_widget(text)
        box = fitz.Widget()
        box.field_name = "Agree"
        box.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
        box.rect = fitz.Rect(80, 140, 95, 155)
        page.add_widget(box)
        doc.save(str(path))
        doc.close()
        return path

    def make_fields_json(self, name="fields.json", **overrides):
        payload = {
            "pages": [{"page_number": 1, "pdf_width": 612, "pdf_height": 792}],
            "form_fields": [{
                "page_number": 1,
                "description": "Name",
                "label_bounding_box": [20, 20, 70, 40],
                "entry_bounding_box": [80, 20, 200, 40],
                "entry_text": {"text": "Ada", "font_size": 10},
            }],
        }
        payload.update(overrides)
        return self.write_json(name, payload)

    def page_text(self, path, index=0):
        with fitz.open(str(path)) as doc:
            return doc[index].get_text()

    def page_count(self, path):
        with fitz.open(str(path)) as doc:
            return doc.page_count


class InspectAndExtractTests(PdfFixtureMixin, ScriptCase):
    def test_inspect_json_reports_structure_metadata_and_poppler_output(self):
        """Ensures inspect json reports structure metadata and poppler output."""
        source = self.make_pdf()
        payload = self.run_python(SCRIPTS / "pdf_inspect.py", source, "--json").json()
        self.assertEqual(payload["path"], str(source))
        self.assertEqual(payload["pages"], 3)
        self.assertFalse(payload["encrypted"])
        self.assertEqual(payload["page_sizes"],
                         [{"width_pt": 612, "height_pt": 792, "count": 3}])
        for key in ("form_fields", "attachments", "annotations", "outline_items"):
            self.assertEqual(payload[key], 0, key)
        self.assertIn("/Producer", payload["metadata"])
        # Poppler is consulted for the human-readable extras.
        self.assertRegex(payload["poppler_pdfinfo"], r"Pages:\s+3\n")
        self.assertRegex(payload["poppler_pdfinfo"], r"Encrypted:\s+no")
        self.assertIn("Helvetica", payload["poppler_pdffonts"])

    def test_inspect_text_mode_is_a_readable_summary(self):
        """Ensures inspect text mode is a readable summary."""
        out = self.run_python(SCRIPTS / "pdf_inspect.py", self.make_pdf()).stdout
        self.assertAllIn(["PDF:", "Pages: 3", "Encrypted: False",
                          "Page sizes (pt, rounded):", "612 x 792 (3 page(s))"], out)

    def test_inspect_reports_an_encrypted_file_and_needs_the_password(self):
        """Ensures inspect reports an encrypted file and needs the password."""
        source = self.make_pdf()
        encrypted = self.work / "enc.pdf"
        self.run_python(SCRIPTS / "pdf_edit.py", "encrypt", source, "-o", encrypted,
                        "--user_password", "secret")
        payload = self.run_python(SCRIPTS / "pdf_inspect.py", encrypted, "--password",
                                  "secret", "--json").json()
        self.assertTrue(payload["encrypted"])
        self.assertEqual(payload["pages"], 3)
        # Without the password the tool cannot read the page tree at all.
        self.run_python(SCRIPTS / "pdf_inspect.py", encrypted, "--json", code=None)

    def test_extract_text_returns_every_page(self):
        """Ensures extract text returns every page."""
        out = self.run_python(SCRIPTS / "pdf_extract.py", "text", self.make_pdf()).stdout
        for index in (1, 2, 3):
            self.assertIn(f"Page {index} heading", out)
        self.assertIn(self.SECRET, out)

    def test_extract_info_delegates_to_the_inspector(self):
        """Ensures extract info delegates to the inspector."""
        out = self.run_python(SCRIPTS / "pdf_extract.py", "info", self.make_pdf()).stdout
        self.assertAllIn(["Pages: 3", "Encrypted: False", "612 x 792"], out)

    def test_extract_forms_reports_field_types_and_states(self):
        """Ensures extract forms reports field types and states."""
        payload = self.run_python(SCRIPTS / "pdf_extract.py", "forms",
                                  self.make_form()).json()
        self.assertEqual(set(payload), {"Name", "Agree"})
        self.assertEqual(payload["Name"]["type"], "/Tx")
        self.assertEqual(payload["Name"]["field_kind"], "text")
        self.assertEqual(payload["Agree"]["type"], "/Btn")
        for field in payload.values():
            self.assertEqual(sorted(field),
                             ["alt_name", "default", "field_kind", "flags", "type",
                              "value"])

    def test_extract_words_writes_a_top_left_origin_csv(self):
        """Ensures extract words writes a top left origin csv."""
        out = self.work / "words.csv"
        self.run_python(SCRIPTS / "pdf_extract.py", "words", self.make_pdf(), "--out", out)
        with out.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(
            sorted(rows[0]), ["bottom", "doctop", "page", "text", "top", "x0", "x1"])
        self.assertIn("Page", [row["text"] for row in rows])
        self.assertTrue(all(float(row["top"]) > 0 for row in rows))

    def test_extract_words_accepts_the_pymupdf_method(self):
        """Ensures extract words accepts the pymupdf method."""
        out = self.work / "words2.csv"
        self.run_python(SCRIPTS / "pdf_extract.py", "words", self.make_pdf(),
                        "--method", "pymupdf", "--out", out)
        self.assertTrue(out.read_text().strip())

    def test_extract_annotations_lists_the_free_text_annotation(self):
        """Ensures extract annotations lists the free text annotation."""
        fields = self.make_fields_json()
        annotated = self.work / "ann.pdf"
        self.run_python(SCRIPTS / "fill_pdf_form_with_annotations.py",
                        self.make_pdf(), fields, annotated)
        payload = self.run_python(SCRIPTS / "pdf_extract.py", "annotations",
                                  annotated).json()
        self.assertEqual(payload[0]["subtype"], "/FreeText")
        self.assertEqual(payload[0]["page"], 1)

    def test_extract_images_and_tables_report_empty_results_cleanly(self):
        """Ensures extract images and tables report empty results cleanly."""
        images = self.run_python(SCRIPTS / "pdf_extract.py", "images", self.make_pdf(),
                                 "--out_dir", self.work / "imgs").stdout
        self.assertIn("Extracted 0 images to:", images)

        tables = self.work / "tables"
        result = self.run_python(SCRIPTS / "pdf_extract.py", "tables", self.make_pdf(),
                                 "--out_dir", tables, "--format", "csv")
        self.assertIn(f"Wrote tables to: {tables}", result.stdout)
        self.assertTrue(tables.is_dir())

    def test_extract_requires_an_output_directory_for_attachments(self):
        """Ensures extract requires an output directory for attachments."""
        result = self.run_python(SCRIPTS / "pdf_extract.py", "attachments",
                                 self.make_pdf(), code=2)
        self.assertIn("--out_dir", result.stdout + result.stderr)


class PdfEditTests(PdfFixtureMixin, ScriptCase):
    def edit(self, *args, code=0):
        return self.run_python(SCRIPTS / "pdf_edit.py", *args, code=code)

    def test_help_lists_every_documented_subcommand(self):
        """Ensures help lists every documented subcommand."""
        out = self.edit("--help").stdout
        self.assertAllInText(
            ["merge", "split", "select", "extract", "rotate", "crop", "watermark",
             "paginate", "encrypt", "decrypt", "optimize", "repair", "fill-form",
             "after ANY edit, render and visually verify"],
            out,
        )

    def test_merge_concatenates_in_order(self):
        """Ensures merge concatenates in order."""
        first = self.make_pdf("a.pdf", pages=2)
        second = self.make_pdf("b.pdf", pages=1)
        merged = self.work / "merged.pdf"
        self.edit("merge", first, second, "-o", merged)
        self.assertEqual(self.page_count(merged), 3)
        self.assertIn("Page 1 heading", self.page_text(merged, 2))

    def test_split_writes_one_numbered_file_per_page(self):
        """Ensures split writes one numbered file per page."""
        source = self.make_pdf(pages=3)
        out_dir = self.work / "split"
        self.edit("split", source, "--out_dir", out_dir)
        self.assertEqual(sorted(p.name for p in out_dir.iterdir()),
                         ["base_p001.pdf", "base_p002.pdf", "base_p003.pdf"])
        for part in sorted(out_dir.iterdir()):
            self.assertEqual(self.page_count(part), 1)

    def test_select_and_extract_honour_page_specifications(self):
        """Ensures select and extract honour page specifications."""
        source = self.make_pdf(pages=3)
        selected = self.work / "sel.pdf"
        self.edit("select", source, "--pages", "1,3", "-o", selected)
        self.assertEqual(self.page_count(selected), 2)
        self.assertIn("Page 3 heading", self.page_text(selected, 1))

        out_dir = self.work / "ranges"
        self.edit("extract", source, "--ranges", "1-2", "--out_dir", out_dir)
        produced = list(out_dir.iterdir())
        self.assertEqual(len(produced), 1)
        self.assertEqual(self.page_count(produced[0]), 2)
        # The source is never rewritten.
        self.assertEqual(self.page_count(source), 3)

    def test_rotate_sets_the_page_rotation(self):
        """Ensures rotate sets the page rotation."""
        source = self.make_pdf(pages=1)
        rotated = self.work / "rot.pdf"
        self.edit("rotate", source, "--angle", "90", "-o", rotated)
        with fitz.open(str(rotated)) as doc:
            self.assertEqual(doc[0].rotation, 90)

    def test_crop_requires_a_unit_and_shrinks_the_box(self):
        """Ensures crop requires a unit and shrinks the box."""
        source = self.make_pdf(pages=1)
        cropped = self.work / "crop.pdf"
        self.edit("crop", source, "--inset", "20pt", "-o", cropped)
        with fitz.open(str(cropped)) as doc:
            self.assertEqual(tuple(round(v) for v in doc[0].rect), (0, 0, 572, 752))

        rejected = self.edit("crop", source, "--inset", "20", "-o",
                             self.work / "bad.pdf", code=1)
        self.assertIn("--inset must look like '12pt' or '0.25in' or '5mm'",
                      rejected.stdout + rejected.stderr)
        self.assertFalse((self.work / "bad.pdf").exists())

    def test_watermark_overlays_every_page(self):
        """Ensures watermark overlays every page."""
        source = self.make_pdf(pages=3)
        stamp = self.work / "stamp.pdf"
        self.run_python(SCRIPTS / "make_watermark_pdf.py", "--text", "CONFIDENTIAL",
                        "--out", stamp, "--angle", "45", "--opacity", "0.2")
        self.assertEqual(self.page_count(stamp), 1)

        marked = self.work / "watermarked.pdf"
        self.edit("watermark", source, "--watermark", stamp, "-o", marked)
        self.assertEqual(self.page_count(marked), 3)
        self.assertIn("CONFIDENTIAL", self.page_text(marked, 0))
        self.assertIn("CONFIDENTIAL", self.page_text(marked, 2))

    def test_paginate_adds_page_numbers_from_the_requested_start(self):
        """Ensures paginate adds page numbers from the requested start."""
        source = self.make_pdf(pages=2)
        numbered = self.work / "pag.pdf"
        self.edit("paginate", source, "-o", numbered, "--start", "10")
        text = " ".join(self.page_text(numbered, index) for index in range(2))
        self.assertIn("10", text)
        self.assertIn("11", text)

    def test_encrypt_then_decrypt_round_trips(self):
        """Ensures encrypt then decrypt round trips."""
        source = self.make_pdf(pages=1)
        encrypted = self.work / "enc.pdf"
        self.edit("encrypt", source, "-o", encrypted, "--user_password", "pw",
                  "--owner_password", "owner")
        self.assertTrue(PdfReader(str(encrypted)).is_encrypted)

        decrypted = self.work / "dec.pdf"
        self.edit("decrypt", encrypted, "-o", decrypted, "--password", "pw")
        self.assertFalse(PdfReader(str(decrypted)).is_encrypted)
        self.assertIn("Page 1 heading", self.page_text(decrypted))

    def test_optimize_and_repair_produce_readable_output(self):
        """Ensures optimize and repair produce readable output."""
        source = self.make_pdf(pages=2)
        for command in ("optimize", "repair"):
            with self.subTest(command=command):
                out = self.work / f"{command}.pdf"
                self.edit(command, source, "-o", out)
                self.assertEqual(self.page_count(out), 2)
                self.assertIn("Page 1 heading", self.page_text(out))

    def test_fill_form_reads_a_json_file_and_sets_field_values(self):
        """Ensures fill form reads a json file and sets field values."""
        source = self.make_form()
        values = self.write_json("values.json", {"Name": "Bob"})
        filled = self.work / "filled.pdf"
        self.edit("fill-form", source, values, "-o", filled)
        with fitz.open(str(filled)) as doc:
            self.assertEqual([w.field_value for w in doc[0].widgets()], ["Bob", "Off"])

    def test_fill_form_needs_a_path_not_inline_json(self):
        """Ensures fill form needs a path not inline json."""
        result = self.edit("fill-form", self.make_form(), '{"Name":"Bob"}', "-o",
                           self.work / "no.pdf", code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.work / "no.pdf").exists())

    def test_page_edits_preserve_catalog_and_input_bytes(self):
        """Page-local edits retain form fields, metadata, outlines and attachments."""
        source = self.make_form()
        writer = PdfWriter(clone_from=source)
        writer.add_metadata({"/Title": "Preservation fixture"})
        writer.add_attachment("note.txt", b"Synthetic attachment")
        writer.add_outline_item("Form", 0)
        writer.write(str(source))
        original = source.read_bytes()
        stamp = self.make_pdf("stamp.pdf", pages=1)
        operations = (("rotate", "--angle", "90"), ("crop", "--inset", "5pt"),
                      ("paginate",), ("watermark", "--watermark", stamp),
                      ("encrypt", "--user_password", "test-password"))
        for command, *arguments in operations:
            with self.subTest(command=command):
                target = self.work / f"catalog-{command}.pdf"
                self.edit(command, source, *arguments, "-o", target)
                loaded = PdfReader(target)
                if loaded.is_encrypted:
                    loaded.decrypt("test-password")
                self.assertEqual(loaded.metadata.title, "Preservation fixture")
                self.assertEqual(set(loaded.get_fields()), {"Name", "Agree"})
                self.assertEqual(loaded.attachments["note.txt"], [b"Synthetic attachment"])
                self.assertEqual(loaded.outline[0].title, "Form")
                if command == "encrypt":
                    decrypted = self.work / "catalog-decrypt.pdf"
                    self.edit("decrypt", target, "--password", "test-password", "-o", decrypted)
                    reopened = PdfReader(decrypted)
                    self.assertEqual(set(reopened.get_fields()), {"Name", "Agree"})
                    self.assertEqual(reopened.attachments["note.txt"], [b"Synthetic attachment"])
                    self.assertEqual(reopened.metadata.title, "Preservation fixture")
                    self.assertEqual(reopened.outline[0].title, "Form")
        self.assertEqual(source.read_bytes(), original)

    def test_invalid_edits_leave_existing_destination_intact(self):
        """Rejected geometry or credentials must not overwrite an existing result."""
        source = self.make_pdf(pages=1)
        destination = self.write_bytes("existing.pdf", b"Keep existing result")
        encrypted = self.work / "encrypted.pdf"
        self.edit("encrypt", source, "--user_password", "correct", "-o", encrypted)
        cases = (("rotate", source, "--angle", "45"),
                 ("crop", source, "--inset", "900pt"),
                 ("decrypt", encrypted, "--password", "wrong"))
        for arguments in cases:
            with self.subTest(command=arguments[0]):
                result = self.edit(*arguments, "-o", destination, code=None)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(destination.read_bytes(), b"Keep existing result")

    def test_every_subcommand_requires_an_output_path(self):
        """Ensures every subcommand requires an output path."""
        source = self.make_pdf(pages=1)
        cases = (("merge", source), ("rotate", source), ("crop", source),
                 ("optimize", source), ("repair", source), ("paginate", source))
        for args in cases:
            with self.subTest(command=args[0]):
                self.edit(*args, code=2)


class PreflightTests(PdfFixtureMixin, ScriptCase):
    """``pdf_preflight.py`` — high-signal triage before any text extraction."""

    def preflight(self, *args, code=0):
        return self.run_python(SCRIPTS / "pdf_preflight.py", *args, code=code)

    def test_help_names_the_checks_it_runs(self):
        """Ensures help names the checks it runs."""
        out = self.preflight("--help").stdout
        self.assertAllInText(
            ["--password", "--json", "corruption/xref damage", "encryption",
             "likely-scanned pages", "XFA forms", "unembedded fonts",
             "Not a print-prepress checker"],
            out,
        )

    def test_a_text_pdf_is_clean(self):
        """Ensures a text pdf is clean."""
        out = self.preflight(self.make_pdf()).stdout
        self.assertAllIn(["PDF:", "Pages: 3", "Encrypted: False",
                          "Openable (PyMuPDF): True", "Likely scanned: False",
                          "XFA present: False"], out)
        self.assertNotIn("Warnings:", out)

    def test_json_mode_reports_the_same_facts_plus_the_font_excerpt(self):
        """Ensures json mode reports the same facts plus the font excerpt."""
        source = self.make_pdf()
        payload = self.preflight(source, "--json").json()
        self.assertEqual(
            sorted(payload),
            ["encrypted", "likely_scanned", "ok_open", "pages", "path",
             "pdffonts_excerpt", "warnings", "xfa_present"],
        )
        self.assertEqual(payload["path"], str(source))
        self.assertEqual(payload["pages"], 3)
        self.assertFalse(payload["encrypted"])
        self.assertTrue(payload["ok_open"])
        self.assertFalse(payload["likely_scanned"])
        self.assertFalse(payload["xfa_present"])
        self.assertEqual(payload["warnings"], [])
        # The PDF uses Helvetica, one of the standard 14 fonts a viewer always
        # has, so the embedding heuristic stays quiet and reports no excerpt.
        self.assertIsNone(payload["pdffonts_excerpt"])

    def test_an_image_only_pdf_is_flagged_and_points_at_the_ocr_tool(self):
        """Ensures an image only pdf is flagged and points at the ocr tool."""
        scan = self.work / "scan.pdf"
        with fitz.open() as doc:
            page = doc.new_page(width=612, height=792)
            pixels = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 612, 792))
            pixels.clear_with(120)
            page.insert_image(fitz.Rect(0, 0, 612, 792), pixmap=pixels)
            doc.save(str(scan))

        out = self.preflight(scan).stdout
        self.assertIn("Likely scanned: True", out)
        self.assertIn("Warnings:", out)
        self.assertIn("PDF looks scanned/image-only: run OCR (ocr_pdf.py) "
                      "before text extraction", out)

        payload = self.preflight(scan, "--json").json()
        self.assertTrue(payload["likely_scanned"])
        self.assertEqual(len(payload["warnings"]), 1)

    def test_an_encrypted_pdf_reports_that_it_cannot_be_opened(self):
        """Ensures an encrypted pdf reports that it cannot be opened."""
        encrypted = self.work / "enc.pdf"
        self.run_python(SCRIPTS / "pdf_edit.py", "encrypt", self.make_pdf(), "-o",
                        encrypted, "--user_password", "pw")
        payload = self.preflight(encrypted, "--json").json()
        self.assertTrue(payload["encrypted"])
        self.assertFalse(payload["ok_open"])
        self.assertTrue(payload["warnings"], "encryption without a password is a warning")

        unlocked = self.preflight(encrypted, "--password", "pw", "--json").json()
        self.assertTrue(unlocked["ok_open"])
        self.assertTrue(unlocked["encrypted"])
        self.assertEqual(unlocked["pages"], 3)
        self.assertEqual(unlocked["warnings"], [])

    def test_wrong_password_stays_encrypted_and_unopenable(self):
        """A rejected password cannot report an encrypted PDF as usable."""
        encrypted = self.work / "locked.pdf"
        self.run_python(SCRIPTS / "pdf_edit.py", "encrypt", self.make_pdf(), "-o",
                        encrypted, "--user_password", "pw")
        payload = self.preflight(encrypted, "--password", "wrong", "--json").json()
        self.assertTrue(payload["encrypted"])
        self.assertFalse(payload["ok_open"])
        self.assertTrue(any("password" in warning for warning in payload["warnings"]))

    def test_empty_user_password_is_readable_but_still_encrypted(self):
        """Owner-only restrictions do not require a user password to inspect pages."""
        from pypdf import PdfReader, PdfWriter, PdfWriter
        encrypted = self.work / "owner-only.pdf"
        writer = PdfWriter(clone_from=PdfReader(self.make_pdf()))
        writer.encrypt("", "owner-secret")
        writer.write(encrypted)
        payload = self.preflight(encrypted, "--json").json()
        self.assertTrue(payload["encrypted"])
        self.assertTrue(payload["ok_open"])
        self.assertEqual(payload["pages"], 3)
        self.assertEqual(payload["warnings"], [])

    def test_a_corrupt_file_is_diagnosed_rather_than_traced(self):
        """Preflight is a reporter: a broken input is data, not an exception."""
        broken = self.write_bytes("broken.pdf", b"%PDF-1.7\nthis is not a pdf\n")
        result = self.preflight(broken)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

        payload = self.preflight(broken, "--json").json()
        self.assertFalse(payload["ok_open"])
        self.assertEqual(payload["pages"], 0)
        self.assertEqual(len(payload["warnings"]), 2)
        self.assertIn("pypdf could not read the file:", payload["warnings"][0])
        self.assertIn("PyMuPDF could not open it (possible corruption/xref issue):",
                      payload["warnings"][1])

    def test_a_missing_file_is_reported(self):
        """Ensures a missing file is reported."""
        result = self.preflight(self.work / "absent.pdf", code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stdout)


class RedactionTests(PdfFixtureMixin, ScriptCase):
    def redact(self, *args, code=0):
        return self.run_python(SCRIPTS / "pdf_redact.py", *args, code=code)

    def test_help_promises_true_redaction_and_verification(self):
        """Ensures help promises true redaction and verification."""
        out = self.redact("--help").stdout
        self.assertAllInText(
            ["Redact PDF content for real", "apply_redactions()",
             "text", "boxes", "--boxes_json", "confirm the sensitive string no longer extracts"],
            out,
        )

    def test_text_redaction_removes_the_secret_from_the_content_stream(self):
        """Ensures text redaction removes the secret from the content stream."""
        source = self.make_pdf()
        out = self.work / "redacted.pdf"
        result = self.redact("text", source, out, "--text", self.SECRET)
        self.assertIn("Applied 3 redaction(s)", result.stdout)
        text = self.page_text(out)
        self.assertNotIn(self.SECRET, text)
        self.assertIn("Page 1 heading", text, "unrelated text survives")
        self.assertIn(self.OTHER_SECRET, text, "only the requested phrase is removed")
        # The removal is structural, not a black rectangle over selectable text.
        self.assertEqual(self.page_count(out), 3)

    def test_text_redaction_supports_ignore_case_and_whole_word(self):
        """Ensures text redaction supports ignore case and whole word."""
        source = self.make_pdf(pages=1)

        insensitive = self.work / "insensitive.pdf"
        result = self.redact("text", source, insensitive, "--text",
                             self.SECRET.upper(), "--ignore_case")
        self.assertIn("Applied 1 redaction(s)", result.stdout)
        self.assertNotIn(self.SECRET, self.page_text(insensitive))

        # --whole_word strips punctuation, so it matches words, not addresses.
        whole = self.work / "whole.pdf"
        result = self.redact("text", source, whole, "--text", "CONTACT",
                             "--whole_word", "--ignore_case")
        self.assertIn("Applied 1 redaction(s)", result.stdout)
        self.assertNotIn("Contact", self.page_text(whole))
        self.assertIn(self.SECRET, self.page_text(whole),
                      "a whole-word match must not swallow its neighbours")

        partial = self.work / "partial.pdf"
        result = self.redact("text", source, partial, "--text", "onta",
                             "--whole_word", "--ignore_case")
        self.assertIn("WARNING: no matches found", result.stdout + result.stderr)
        self.assertIn("Contact", self.page_text(partial))

    def test_text_redaction_can_take_a_phrase_file_and_a_page_range(self):
        """Ensures text redaction can take a phrase file and a page range."""
        source = self.make_pdf(pages=3)
        phrases = self.write("phrases.txt", f"{self.SECRET}\n{self.OTHER_SECRET}\n")
        out = self.work / "scoped.pdf"
        result = self.redact("text", source, out, "--text_file", phrases, "--pages", "2")
        self.assertIn("Applied 2 redaction(s)", result.stdout)
        self.assertIn(self.SECRET, self.page_text(out, 0), "page 1 is untouched")
        self.assertNotIn(self.SECRET, self.page_text(out, 1))
        self.assertIn(self.SECRET, self.page_text(out, 2), "page 3 is untouched")

    def test_text_redaction_requires_a_needle(self):
        """Ensures text redaction requires a needle."""
        result = self.redact("text", self.make_pdf(pages=1), self.work / "x.pdf", code=2)
        self.assertIn("provide --text and/or --text_file",
                      result.stdout + result.stderr)

    def test_box_redaction_accepts_both_documented_json_shapes(self):
        """Ensures box redaction accepts both documented json shapes."""
        source = self.make_pdf(pages=1)
        items = self.write_json("items.json",
                                {"items": [{"page": 1, "rect": [60, 80, 400, 100]}]})
        out = self.work / "boxed-items.pdf"
        result = self.redact("boxes", source, out, "--boxes_json", items)
        self.assertIn("Applied 1 redaction(s)", result.stdout)
        self.assertNotIn("Page 1 heading", self.page_text(out))
        self.assertIn("Contact", self.page_text(out), "only the box is removed")

        pages = self.write_json("pages.json", {"pages": {"1": {
            "boxes": [{"rect": [60, 80, 400, 100]}]}}})
        out2 = self.work / "boxed-pages.pdf"
        self.redact("boxes", source, out2, "--boxes_json", pages)
        self.assertNotIn("Page 1 heading", self.page_text(out2))

    def test_box_redaction_rejects_an_unsupported_shape(self):
        """Ensures box redaction rejects an unsupported shape."""
        boxes = self.write_json("bad.json", {"boxes": [{"page": 1, "rect": [0, 0, 1, 1]}]})
        result = self.redact("boxes", self.make_pdf(pages=1), self.work / "x.pdf",
                             "--boxes_json", boxes, code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsupported boxes JSON format", result.stdout + result.stderr)

    def test_box_redaction_warns_when_the_page_filter_matches_nothing(self):
        """Ensures box redaction warns when the page filter matches nothing."""
        source = self.make_pdf(pages=1)
        items = self.write_json("items.json",
                                {"items": [{"page": 9, "rect": [60, 80, 400, 100]}]})
        result = self.redact("boxes", source, self.work / "none.pdf",
                             "--boxes_json", items)
        self.assertIn("WARNING: no boxes applied", result.stdout + result.stderr)

    def test_a_missing_subcommand_is_a_usage_error(self):
        """Ensures a missing subcommand is a usage error."""
        self.redact(self.make_pdf(), self.work / "x.pdf", "--text", "x", code=2)


class RenderAndCompareTests(PdfFixtureMixin, ScriptCase):
    @unittest.skipUnless(HAVE_POPPLER, "rendering needs pdftoppm")
    def test_render_pdf_names_pages_and_honours_prefix_dpi_and_pages(self):
        """Ensures render pdf names pages and honours prefix dpi and pages."""
        source = self.make_pdf()
        out_dir = self.work / "render"
        result = self.run_python(SCRIPTS / "render_pdf.py", source, "--out_dir",
                                 out_dir, "--dpi", "72")
        self.assertEqual(result.stdout.strip(), f"Rendered 3 page(s) to {out_dir}")
        self.assertEqual(sorted(p.name for p in out_dir.iterdir()),
                         ["page-1.png", "page-2.png", "page-3.png"])
        with Image.open(out_dir / "page-1.png") as image:
            self.assertEqual(image.size, (612, 792))

        prefixed = self.work / "prefixed"
        self.run_python(SCRIPTS / "render_pdf.py", source, "--out_dir", prefixed,
                        "--dpi", "72", "--prefix", "sheet", "--pages", "2")
        self.assertEqual([p.name for p in prefixed.iterdir()], ["sheet-2.png"])

    def test_render_pdf_help_pins_the_engine_and_format_choices(self):
        """Ensures render pdf help pins the engine and format choices."""
        out = self.run_python(SCRIPTS / "render_pdf.py", "--help").stdout
        self.assertAllIn(["--out_dir", "--prefix", "--dpi", "--pages",
                          "--fmt {png,jpeg}", "--engine {pdftoppm,pdfium}"], out)

    @unittest.skipUnless(HAVE_POPPLER, "rendering needs pdftoppm")
    def test_render_pdf_clears_stale_pages_from_a_previous_run(self):
        """Ensures render pdf clears stale pages from a previous run."""
        source = self.make_pdf(pages=3)
        out_dir = self.work / "stale"
        self.run_python(SCRIPTS / "render_pdf.py", source, "--out_dir", out_dir,
                        "--dpi", "72")
        self.assertEqual(len(list(out_dir.glob("page-*.png"))), 3)
        self.run_python(SCRIPTS / "render_pdf.py", self.make_pdf("short.pdf", pages=1),
                        "--out_dir", out_dir, "--dpi", "72")
        self.assertEqual(sorted(p.name for p in out_dir.iterdir()), ["page-1.png"],
                         "a shorter re-render must not leave stale pages behind")

    @unittest.skipUnless(HAVE_POPPLER, "rendering needs pdftoppm")
    def test_compare_renders_reports_changed_pages_with_a_bbox(self):
        """Ensures compare renders reports changed pages with a bbox."""
        source = self.make_pdf()
        redacted = self.work / "redacted.pdf"
        self.run_python(SCRIPTS / "pdf_redact.py", "text", source, redacted, "--text",
                        self.SECRET)
        out_dir = self.work / "diff"
        self.run_python(SCRIPTS / "compare_renders.py", source, redacted, "--out_dir",
                        out_dir, "--dpi", "72")
        summary = self.read_json(out_dir / "summary.json")
        self.assertEqual(summary["pages_a"], 3)
        self.assertEqual(summary["pages_b"], 3)
        self.assertEqual(summary["changed_pages"], 3)
        self.assertEqual(summary["engine"], "pdftoppm")
        page = summary["per_page"][0]
        self.assertTrue(page["changed"])
        self.assertGreater(page["pct_changed"], 0)
        self.assertEqual(len(page["bbox"]), 4)
        self.assertEqual(page["diff"], str(out_dir / "diff/page-1.png"))
        self.assertTrue((out_dir / "diff/page-1.png").is_file())
        self.assertFalse((out_dir / "render_a").exists(),
                         "renders are cleaned up unless --save_renders is given")
        self.assertFalse((out_dir / "render_b").exists())

    @unittest.skipUnless(HAVE_POPPLER, "rendering needs pdftoppm")
    def test_compare_renders_keeps_renders_when_asked(self):
        """Ensures compare renders keeps renders when asked."""
        source = self.make_pdf(pages=1)
        out_dir = self.work / "kept"
        self.run_python(SCRIPTS / "compare_renders.py", source, source, "--out_dir",
                        out_dir, "--dpi", "72", "--save_renders")
        self.assertTrue((out_dir / "render_a/page-1.png").is_file())
        self.assertTrue((out_dir / "render_b/page-1.png").is_file())

    @unittest.skipUnless(HAVE_POPPLER, "rendering needs pdftoppm")
    def test_compare_renders_reports_no_changes_for_identical_inputs(self):
        """Ensures compare renders reports no changes for identical inputs."""
        source = self.make_pdf(pages=1)
        out_dir = self.work / "same"
        self.run_python(SCRIPTS / "compare_renders.py", source, source, "--out_dir",
                        out_dir, "--dpi", "72")
        summary = self.read_json(out_dir / "summary.json")
        self.assertEqual(summary["changed_pages"], 0)
        self.assertFalse(list((out_dir / "diff").iterdir()),
                         "unchanged pages must not produce diff images")

    def test_pixel_comparison_counts_a_single_blue_channel_level(self):
        """Exact RGB comparison must detect changes lost by luminance rounding."""
        helpers = runpy.run_path(str(SCRIPTS / "compare_renders.py"))
        first, second = self.work / "first.png", self.work / "second.png"
        Image.new("RGB", (2, 1), (0, 0, 0)).save(first)
        changed = Image.new("RGB", (2, 1), (0, 0, 0))
        changed.putpixel((1, 0), (0, 0, 1))
        changed.save(second)
        difference = helpers["diff_images"](first, second)
        self.assertEqual(difference["bbox"], [1, 0, 2, 1])
        self.assertEqual(difference["pct_changed"], .5)
        self.assertEqual(difference["max_channel"], 1)

    def test_comparison_records_missing_pages_and_pads_without_resampling(self):
        """Page-count and geometry differences retain their documented report behavior."""
        helpers = runpy.run_path(str(SCRIPTS / "compare_renders.py"))
        small, large = self.work / "small.png", self.work / "large.png"
        Image.new("RGB", (1, 1), "black").save(small)
        Image.new("RGB", (2, 1), "black").save(large)
        difference = helpers["diff_images"](small, large)
        self.assertEqual(difference["bbox"], [1, 0, 2, 1])
        self.assertEqual(difference["pct_changed"], .5)
        records = helpers["compare_pages"]([small, large], [small], self.work / "diff")
        self.assertFalse(records[0]["changed"])
        self.assertEqual(records[1], {"page": 2, "a": str(large), "b": None, "missing": True})

    @unittest.skipUnless(HAVE_POPPLER, "rendering needs pdftoppm")
    def test_comparison_uses_numeric_pages_and_removes_stale_differences(self):
        """Page ten reports as ten, and an unchanged rerun leaves no old diff PNG."""
        source = self.make_pdf(pages=12)
        rotated = self.work / "rotated.pdf"
        self.run_python(SCRIPTS / "pdf_edit.py", "rotate", source, "--pages", "10",
                        "--angle", "180", "-o", rotated)
        directory = self.work / "comparison"
        self.run_python(SCRIPTS / "compare_renders.py", source, rotated, "--out_dir",
                        directory, "--dpi", "36")
        report = self.read_json(directory / "summary.json")
        self.assertEqual([r["page"] for r in report["per_page"] if r["changed"]], [10])
        self.assertTrue((directory / "diff/page-10.png").is_file())
        self.run_python(SCRIPTS / "compare_renders.py", source, source, "--out_dir",
                        directory, "--dpi", "36")
        self.assertEqual(list((directory / "diff").glob("*.png")), [])

    def test_montage_rejects_invalid_dimensions_without_writing(self):
        """A nonpositive column count cannot produce a valid contact sheet."""
        source = self.work / "tile.png"
        Image.new("RGB", (2, 2), "white").save(source)
        target = self.work / "sheet.png"
        outcome = self.run_python(SCRIPTS / "create_montage.py", source, "--out", target,
                                  "--cols", "0", code=None)
        self.assertNotEqual(outcome.returncode, 0)
        self.assertFalse(target.exists())

    @unittest.skipUnless(HAVE_POPPLER, "rendering needs pdftoppm")
    def test_renderer_parity_compares_both_engines(self):
        """Ensures renderer parity compares both engines."""
        out_dir = self.work / "parity"
        self.run_python(SCRIPTS / "renderer_parity.py", self.make_pdf(pages=1),
                        "--out_dir", out_dir, "--dpi", "72")
        summary = self.read_json(out_dir / "summary.json")
        self.assertTrue((out_dir / "render_pdftoppm").is_dir())
        self.assertTrue((out_dir / "render_pdfium").is_dir())
        self.assertIn("per_page", json.dumps(summary))

    @unittest.skipUnless(HAVE_POPPLER, "rendering needs pdftoppm")
    def test_montage_accepts_a_directory_globs_and_explicit_files(self):
        """Ensures montage accepts a directory globs and explicit files."""
        source = self.make_pdf(pages=4)
        rendered = self.work / "pages"
        self.run_python(SCRIPTS / "render_pdf.py", source, "--out_dir", rendered,
                        "--dpi", "72")

        from_dir = self.work / "from_dir.png"
        self.run_python(SCRIPTS / "create_montage.py", rendered, "--out", from_dir,
                        "--cols", "2")
        with Image.open(from_dir) as image:
            self.assertGreater(image.width, 100)

        from_glob = self.work / "from_glob.png"
        self.run_python(SCRIPTS / "create_montage.py", str(rendered / "page-*.png"),
                        "--out", from_glob, "--cols", "4")
        self.assertTrue(from_glob.is_file())

        explicit = self.work / "explicit.png"
        self.run_python(SCRIPTS / "create_montage.py", rendered / "page-1.png",
                        rendered / "page-2.png", "--out", explicit, "--cols", "1",
                        "--tile_max_w", "200", "--margin", "4")
        with Image.open(explicit) as image:
            self.assertLessEqual(image.width, 210)


class FormGeometryTests(PdfFixtureMixin, ScriptCase):
    def test_check_bounding_boxes_passes_a_valid_top_left_spec(self):
        """Ensures check bounding boxes passes a valid top left spec."""
        fields = self.make_fields_json()
        out = self.run_python(SCRIPTS / "check_bounding_boxes.py", fields)
        self.assertEqual(out.stdout.strip(), "SUCCESS: All bounding boxes are valid")

    def test_check_bounding_boxes_rejects_reversed_and_out_of_page_boxes(self):
        """Ensures check bounding boxes rejects reversed and out of page boxes."""
        for label, entry in (
            ("reversed", [200, 20, 80, 40]),
            ("empty", [80, 20, 80, 20]),
            ("off-page", [80, 20, 900, 40]),
        ):
            with self.subTest(box=label):
                fields = self.make_fields_json(name=f"bad-{label}.json")
                payload = json.loads(fields.read_text())
                payload["form_fields"][0]["entry_bounding_box"] = entry
                fields.write_text(json.dumps(payload))
                result = self.run_python(SCRIPTS / "check_bounding_boxes.py", fields,
                                         code=1)
                self.assertIn("FAILURE", result.stdout + result.stderr)

    def test_check_bounding_boxes_validates_font_fit_for_pixel_units(self):
        """Ensures check bounding boxes validates font fit for pixel units."""
        fields = self.make_fields_json(name="pixels.json")
        payload = json.loads(fields.read_text())
        payload["pages"][0].update({"image_width": 1224, "image_height": 1584,
                                    "units": "pixels"})
        payload["form_fields"][0]["entry_bounding_box"] = [160, 40, 400, 80]
        payload["form_fields"][0]["label_bounding_box"] = [40, 40, 140, 80]
        payload["form_fields"][0]["entry_text"]["font_size"] = 10
        fields.write_text(json.dumps(payload))
        self.run_python(SCRIPTS / "check_bounding_boxes.py", fields)

        oversized = self.work / "oversized.json"
        payload["form_fields"][0]["entry_text"]["font_size"] = 200
        oversized.write_text(json.dumps(payload))
        result = self.run_python(SCRIPTS / "check_bounding_boxes.py", oversized, code=1)
        self.assertIn("FAILURE", result.stdout + result.stderr)

    def test_create_validation_image_draws_both_box_kinds_at_page_scale(self):
        """Ensures create validation image draws both box kinds at page scale."""
        fields = self.make_fields_json()
        rendered = self.work / "page"
        self.run_python(SCRIPTS / "render_pdf.py", self.make_pdf(pages=1), "--out_dir",
                        rendered, "--dpi", "72", "--pages", "1")
        out = self.work / "review.png"
        self.run_python(SCRIPTS / "create_validation_image.py", "1", fields,
                        rendered / "page-1.png", out)
        with Image.open(out) as image:
            self.assertEqual(image.size, (612, 792))
            self.assertEqual(image.mode, "RGB")
            pixels = image.convert("RGB").load()
        self.assertIn((255, 0, 0), self._colours(pixels, out),
                      "entry boxes are drawn red")
        self.assertIn((0, 0, 255), self._colours(pixels, out),
                      "label boxes are drawn blue")

    @staticmethod
    def _colours(pixels, path):
        with Image.open(path) as image:
            return set(image.convert("RGB").getdata())

    def test_fill_with_annotations_adds_editable_free_text_and_keeps_the_original(self):
        """Ensures fill with annotations adds editable free text and keeps the original."""
        source = self.make_pdf(pages=1)
        before = source.read_bytes()
        fields = self.make_fields_json()
        out = self.work / "annotated.pdf"
        self.run_python(SCRIPTS / "fill_pdf_form_with_annotations.py", source, fields,
                        out)
        with fitz.open(str(out)) as doc:
            page = doc[0]          # keep the page bound while reading its annots
            annotations = list(page.annots())
            self.assertEqual(len(annotations), 1)
            self.assertEqual(annotations[0].type[1], "FreeText")
            self.assertEqual(annotations[0].info["content"], "Ada")
        self.assertEqual(source.read_bytes(), before, "the input must not be modified")
        self.assertNotIn("Ada", self.page_text(source))

    def test_fill_with_annotations_rejects_a_rotated_page(self):
        """Ensures fill with annotations rejects a rotated page."""
        source = self.make_pdf(pages=1)
        rotated = self.work / "rotated.pdf"
        self.run_python(SCRIPTS / "pdf_edit.py", "rotate", source, "--angle", "90",
                        "-o", rotated)
        out = self.work / "nope.pdf"
        result = self.run_python(SCRIPTS / "fill_pdf_form_with_annotations.py", rotated,
                                 self.make_fields_json(), out, code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(out.exists(), "a rejected page geometry writes nothing")

    def test_place_text_by_boxes_stamps_values_and_can_draw_a_preview(self):
        """Ensures place text by boxes stamps values and can draw a preview."""
        source = self.make_pdf(pages=1)
        spec = self.write_json("spec.json", {"page": 1, "items": [
            {"name": "nm", "kind": "text", "rect": [72, 500, 300, 520],
             "font": "Helvetica", "font_size": 10, "wrap": False,
             "fit": "shrink_to_fit"},
            {"name": "ag", "kind": "check", "rect": [72, 470, 90, 488], "mark": "x"},
        ]})
        values = self.write_json("values.json", {"nm": "Ada Lovelace", "ag": True})
        out = self.work / "placed.pdf"
        preview = self.work / "preview.pdf"
        result = self.run_python(SCRIPTS / "place_text_by_boxes.py", source, spec,
                                 values, "--out", out, "--preview_pdf", preview,
                                 "--draw_guides")
        self.assertIn("[OK] preview:", result.stdout)
        self.assertTrue(preview.is_file())
        text = self.page_text(out)
        self.assertIn("Ada Lovelace", text)
        self.assertIn("Page 1 heading", text, "the original content is preserved")

    def test_box_overlay_preserves_catalog_and_rejects_late_bad_pages(self):
        """Overlay copies retain document features and fail before either output is written."""
        source = self.make_form()
        writer = PdfWriter(clone_from=source)
        writer.add_metadata({"/Title": "Overlay fixture"})
        writer.add_attachment("source.txt", b"Synthetic source")
        writer.write(str(source))
        original = source.read_bytes()
        spec = self.write_json("boxes.json", {"page": 1, "items": [
            {"name": "label", "rect": [40, 400, 200, 420]}]})
        values = self.write_json("box-values.json", {"label": "Verified overlay"})
        target, preview = self.work / "overlay.pdf", self.work / "preview.pdf"
        self.run_python(SCRIPTS / "place_text_by_boxes.py", source, spec, values,
                        "--out", target, "--preview_pdf", preview)
        for output in (target, preview):
            loaded = PdfReader(output)
            self.assertEqual(loaded.metadata.title, "Overlay fixture")
            self.assertEqual(set(loaded.get_fields()), {"Name", "Agree"})
            self.assertEqual(loaded.attachments["source.txt"], [b"Synthetic source"])
        snapshots = [p.read_bytes() for p in (target, preview)]
        self.write_json("boxes.json", {"pages": [
            {"page": 1, "items": []}, {"page": 99, "items": []}]})
        failure = self.run_python(SCRIPTS / "place_text_by_boxes.py", source, spec, values,
                                  "--out", target, "--preview_pdf", preview, code=None)
        self.assertNotEqual(failure.returncode, 0)
        self.assertEqual([p.read_bytes() for p in (target, preview)], snapshots)
        self.assertEqual(source.read_bytes(), original)

    def test_place_text_by_boxes_warns_about_geometry_it_cannot_use(self):
        """Ensures place text by boxes warns about geometry it cannot use."""
        source = self.make_pdf(pages=1)
        spec = self.write_json("spec.json", {"page": 1, "items": [
            {"name": "reversed", "kind": "text", "rect": [300, 520, 72, 500],
             "font_size": 10},
            {"name": "offpage", "kind": "text", "rect": [72, 5000, 300, 5020],
             "font_size": 10}]})
        values = self.write_json("values.json",
                                 {"reversed": "x", "offpage": "y", "unknown": "z"})
        out = self.work / "warned.pdf"
        result = self.run_python(SCRIPTS / "place_text_by_boxes.py", source, spec,
                                 values, "--out", out)
        # Geometry problems are warnings, not failures: the tool still writes.
        self.assertIn("[WARN] invalid rect for reversed", result.stdout)
        self.assertIn("[WARN] rect out of bounds for offpage", result.stdout)
        self.assertTrue(out.is_file())

    @unittest.skipUnless(HAVE_POPPLER, "the box picker renders the page first")
    def test_box_picker_emits_a_self_contained_html_and_a_render(self):
        """Ensures box picker emits a self contained html and a render."""
        source = self.make_pdf(pages=2)
        out = self.work / "picker.html"
        tmp = self.work / "picker-tmp"
        result = self.run_python(SCRIPTS / "box_picker_html.py", source, "--page", "1",
                                 "--dpi", "72", "--out", out, "--tmp_dir", tmp)
        self.assertIn("Rendered 1 page(s)", result.stdout)
        body = out.read_text()
        self.assertIn("<html", body.lower())
        self.assertIn("data:image/png;base64,", body, "the page is embedded")
        self.assertTrue(list(tmp.glob("*.png")))

    def test_extract_form_structure_reports_the_top_left_coordinate_contract(self):
        """Ensures extract form structure reports the top left coordinate contract."""
        source = self.make_form()
        out = self.work / "structure.json"
        result = self.run_python(SCRIPTS / "extract_form_structure.py", source, out)
        self.assertAllIn(["Surveying", "Found:", "page(s)", "Wrote"],
                         result.stdout)
        payload = self.read_json(out)
        self.assertEqual(payload["coordinate_system"],
                         "top-left PDF points; candidates require visual verification")
        self.assertEqual(payload["pages"],
                         [{"page_number": 1, "width": 612.0, "height": 792.0}])
        self.assertEqual(sorted(payload), ["checkboxes", "coordinate_system", "labels",
                                           "lines", "pages", "row_boundaries"])


class BatchTests(PdfFixtureMixin, ScriptCase):
    def test_batch_inspect_writes_one_json_per_input(self):
        """Ensures batch inspect writes one json per input."""
        self.make_pdf("a.pdf", pages=1)
        self.make_pdf("b.pdf", pages=2)
        out_root = self.work / "inspected"
        result = self.run_python(SCRIPTS / "batch_pdf.py", "inspect", "--in_glob",
                                 "*.pdf", "--out_root", out_root, cwd=self.work)
        self.assertIn("Inspected 2 PDF(s)", result.stdout)
        self.assertEqual(sorted(p.name for p in out_root.iterdir()),
                         ["a.pdf.json", "b.pdf.json"])
        self.assertEqual(self.read_json(out_root / "b.pdf.json")["pages"], 2)

    @unittest.skipUnless(HAVE_POPPLER, "rendering needs pdftoppm")
    def test_batch_render_creates_a_directory_per_input(self):
        """Ensures batch render creates a directory per input."""
        self.make_pdf("a.pdf", pages=2)
        out_root = self.work / "renders"
        result = self.run_python(SCRIPTS / "batch_pdf.py", "render", "--in_glob",
                                 "a.pdf", "--out_root", out_root, "--dpi", "72",
                                 cwd=self.work)
        self.assertIn("Rendered 1 PDF(s)", result.stdout)
        self.assertEqual(sorted(p.name for p in (out_root / "a.pdf").iterdir()),
                         ["page-1.png", "page-2.png"])

    def test_batch_normalize_rewrites_the_corpus(self):
        """Ensures batch normalize rewrites the corpus."""
        self.make_pdf("a.pdf", pages=1)
        out_root = self.work / "normalized"
        result = self.run_python(SCRIPTS / "batch_pdf.py", "normalize", "--in_glob",
                                 "a.pdf", "--out_root", out_root, cwd=self.work)
        self.assertIn("Normalized", result.stdout)
        produced = list(out_root.rglob("*.pdf"))
        self.assertEqual(len(produced), 1)
        self.assertIn("Page 1 heading", self.page_text(produced[0]))


class SmokeTestTests(PdfFixtureMixin, ScriptCase):
    """The three self-contained regression harnesses the skill ships."""

    @unittest.skipUnless(HAVE_POPPLER, "the edit smoke test renders its output")
    def test_edit_smoketest_paginates_and_verifies(self):
        """Ensures edit smoketest paginates and verifies."""
        workdir = self.work / "edit-smoke"
        result = self.run_python(SCRIPTS / "edit_smoketest.py", "--workdir", workdir,
                                 "--dpi", "72", timeout=300)
        self.assertIn("[OK] edit smoke test passed", result.stdout)
        self.assertTrue((workdir / "paginated.pdf").is_file())
        self.assertTrue(list((workdir / "render").glob("*.png")))

    @unittest.skipUnless(HAVE_POPPLER and HAVE_NODE and HAVE_NODE_DEPS,
                         "the forms smoke test needs pdftoppm and the pdf-lib deps")
    def test_forms_smoketest_fills_flattens_and_diffs(self):
        """Ensures forms smoketest fills flattens and diffs."""
        workdir = self.work / "forms-smoke"
        result = self.run_python(SCRIPTS / "forms_smoketest.py", "--workdir", workdir,
                                 "--dpi", "72", timeout=300)
        self.assertIn("[OK] forms smoke test passed. changed_pages=1", result.stdout)
        self.assertTrue((workdir / "form_filled.pdf").is_file())
        self.assertEqual(self.read_json(workdir / "diff/summary.json")["changed_pages"], 1)

    @unittest.skipUnless(HAVE_POPPLER, "the redaction smoke test renders before/after")
    def test_redact_smoketest_proves_the_secret_is_gone(self):
        """Ensures redact smoketest proves the secret is gone."""
        workdir = self.work / "redact-smoke"
        result = self.run_python(SCRIPTS / "redact_smoketest.py", "--workdir", workdir,
                                 "--dpi", "72", timeout=300)
        self.assertEqual(result.stdout.strip().splitlines()[-1], "OK")
        self.assertTrue((workdir / "redacted.pdf").is_file())
        self.assertTrue((workdir / "input.pdf").is_file())

    @unittest.skipUnless(HAVE_POPPLER, "the redaction smoke test renders before/after")
    def test_smoketest_workdirs_must_be_absolute(self):
        """The harness re-enters its workdir, so a relative path breaks it."""
        result = self.run_python(SCRIPTS / "redact_smoketest.py", "--workdir",
                                 "relative-smoke", "--dpi", "72", cwd=self.work,
                                 code=None, timeout=300)
        self.assertNotEqual(result.returncode, 0)


class ConverterTests(PdfFixtureMixin, ScriptCase):
    """Converters keep a usable CLI and fail loudly when a backend is absent."""

    def test_make_watermark_pdf_honours_pagesize_and_geometry(self):
        """Ensures make watermark pdf honours pagesize and geometry."""
        letter = self.work / "letter.pdf"
        self.run_python(SCRIPTS / "make_watermark_pdf.py", "--text", "DRAFT",
                        "--out", letter, "--pagesize", "letter")
        a4 = self.work / "a4.pdf"
        self.run_python(SCRIPTS / "make_watermark_pdf.py", "--text", "DRAFT",
                        "--out", a4, "--pagesize", "a4", "--font_size", "48",
                        "--angle", "30", "--center_x", "0.5", "--center_y", "0.5")
        with fitz.open(str(letter)) as doc:
            self.assertEqual(tuple(round(v) for v in doc[0].rect), (0, 0, 612, 792))
            self.assertIn("DRAFT", doc[0].get_text())
        with fitz.open(str(a4)) as doc:
            self.assertEqual(tuple(round(v) for v in doc[0].rect), (0, 0, 595, 842))

    def test_latex_to_pdf_reports_a_missing_engine_with_install_guidance(self):
        """Ensures latex to pdf reports a missing engine with install guidance."""
        source = self.write("doc.tex", "\\documentclass{article}"
                                      "\\begin{document}hi\\end{document}\n")
        if HAVE_LATEX:
            out = self.work / "latex.pdf"
            self.run_python(SCRIPTS / "latex_to_pdf.py", source, "-o", out, timeout=300)
            self.assertTrue(out.is_file())
            return
        result = self.run_python(SCRIPTS / "latex_to_pdf.py", source, "-o",
                                 self.work / "latex.pdf", code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("latexmk not found. Install texlive/latexmk",
                      result.stdout + result.stderr)

    def test_latex_to_pdf_requires_exactly_one_output_form(self):
        """Ensures latex to pdf requires exactly one output form."""
        source = self.write("doc.tex", "\\documentclass{article}"
                                      "\\begin{document}hi\\end{document}\n")
        self.run_python(SCRIPTS / "latex_to_pdf.py", source, code=2)
        self.run_python(SCRIPTS / "latex_to_pdf.py", source, "-o", self.work / "a.pdf",
                        "--out_dir", self.work / "d", code=2)

    @unittest.skipUnless(HAVE_PANDOC, "md_to_pdf.py shells out to pandoc")
    def test_md_to_pdf_converts_markdown(self):
        """Ensures md to pdf converts markdown."""
        source = self.write("doc.md", "# Title\n\nBody text.\n")
        out = self.work / "doc.pdf"
        self.run_python(SCRIPTS / "md_to_pdf.py", source, "--output", out, timeout=300)
        self.assertIn("Title", self.page_text(out))

    def test_md_to_pdf_requires_an_output_path(self):
        """Ensures md to pdf requires an output path."""
        source = self.write("doc.md", "# Title\n")
        self.run_python(SCRIPTS / "md_to_pdf.py", source, code=2)

    @unittest.skipUnless(HAVE_SOFFICE, "lo_convert_to_pdf.py drives LibreOffice")
    def test_lo_convert_produces_a_pdf(self):
        """Ensures lo convert produces a pdf."""
        from docx import Document

        source = self.work / "doc.docx"
        document = Document()
        document.add_paragraph("Hello from Writer")
        document.save(str(source))
        out_dir = self.work / "converted"
        self.run_python(SCRIPTS / "lo_convert_to_pdf.py", source, "--out_dir", out_dir,
                        timeout=300)
        produced = list(out_dir.glob("*.pdf"))
        self.assertEqual(len(produced), 1)
        self.assertIn("Hello from Writer", self.page_text(produced[0]))

    @unittest.skipUnless(os.name == "posix", "uses a local executable fixture")
    def test_lo_convert_passes_the_output_directory_as_a_separate_argument(self):
        """The native --outdir syntax works with spaces without needing LibreOffice."""
        executable = self.write(
            "bin/soffice",
            f"#!{sys.executable}\n"
            "import sys\n"
            "from pathlib import Path\n"
            "from pypdf import PdfWriter\n"
            "args = sys.argv[1:]\n"
            "if '--outdir' not in args:\n"
            "    sys.exit('LibreOffice requires --outdir followed by a directory')\n"
            "directory = Path(args[args.index('--outdir') + 1])\n"
            "source = Path(args[-1])\n"
            "writer = PdfWriter()\n"
            "writer.add_blank_page(width=612, height=792)\n"
            "writer.write(directory / (source.stem + '.pdf'))\n",
        )
        executable.chmod(0o755)
        source = self.write("input with spaces.docx", "synthetic fixture")
        output = self.work / "output with spaces"
        self.run_python(SCRIPTS / "lo_convert_to_pdf.py", source, "--out_dir", output,
                        env={"PATH": str(executable.parent) + os.pathsep + os.environ["PATH"]})
        self.assertEqual(len(PdfReader(output / "input with spaces.pdf").pages), 1)
        self.assertEqual(source.read_text(), "synthetic fixture")

    def test_lo_convert_reports_a_missing_soffice(self):
        """Ensures lo convert reports a missing soffice."""
        if HAVE_SOFFICE:
            self.skipTest("LibreOffice is installed; the failure path is unreachable")
        result = self.run_python(SCRIPTS / "lo_convert_to_pdf.py", self.make_pdf(),
                                 "--out_dir", self.work / "out", code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("soffice", result.stdout + result.stderr)

    def test_html_to_pdf_reports_its_playwright_dependency(self):
        """Ensures html to pdf reports its playwright dependency."""
        if module_available("playwright"):
            out = self.run_python(SCRIPTS / "html_to_pdf.py", "--help").stdout
            self.assertIn("--output", out)
            return
        # The import happens at module load, so the missing backend is named.
        result = self.run_python(SCRIPTS / "html_to_pdf.py", "--help", code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("playwright", result.stdout + result.stderr)

    def test_ocr_pdf_documents_its_options_and_requires_an_output(self):
        """Ensures ocr pdf documents its options and requires an output."""
        out = self.run_python(SCRIPTS / "ocr_pdf.py", "--help").stdout
        self.assertAllIn(["--lang", "--force", "--fallback", "--deskew", "--jobs",
                          "--optimize", "--dpi", "--keep_tmp"], out)
        result = self.run_python(SCRIPTS / "ocr_pdf.py", self.make_pdf(pages=1), code=2)
        self.assertIn("-o/--output", result.stdout + result.stderr)


@unittest.skipUnless(HAVE_NODE and HAVE_NODE_DEPS,
                     "requires `skills/pdf/js` dependencies (run install_deps.sh)")
class JsToolTests(PdfFixtureMixin, ScriptCase):
    """The Node helpers built on pdf-lib and pdfjs-dist."""

    def js(self, script, *args, code=0):
        return self.run_node(JS / script, *args, cwd=self.work, code=code)

    def test_extract_form_fields_lists_names_and_widget_types(self):
        """Ensures extract form fields lists names and widget types."""
        out = self.js("extract_form_fields.mjs", self.make_form()).stdout
        self.assertEqual([line.split("\t") for line in out.splitlines()],
                         [["Name", "PDFTextField"], ["Agree", "PDFCheckBox"]])

    def test_extract_text_pdfjs_returns_page_separated_text(self):
        """Ensures extract text pdfjs returns page separated text."""
        out = self.js("extract_text_pdfjs.mjs", self.make_pdf()).stdout
        for index in (1, 2, 3):
            self.assertIn(f"Page {index} heading", out)
        self.assertIn(self.SECRET, out)

    def test_fill_form_accepts_both_positional_and_flag_invocations(self):
        """Ensures fill form accepts both positional and flag invocations."""
        source = self.make_form()
        values = self.write_json("values.json", {"Name": "Ada", "Agree": True})

        positional = self.work / "positional.pdf"
        result = self.js("fill_form.mjs", source, values, positional, "--flatten")
        self.assertIn("[OK] wrote", result.stdout)
        self.assertIn("Ada", self.page_text(positional))
        with fitz.open(str(positional)) as doc:
            self.assertEqual(list(doc[0].widgets()), [],
                             "--flatten must remove the interactive fields")

        flagged = self.work / "flagged.pdf"
        self.js("fill_form.mjs", "--input", source, "--values", values, "--output",
                flagged)
        self.assertIn("Ada", self.page_text(flagged))
        with fitz.open(str(flagged)) as doc:
            self.assertTrue(list(doc[0].widgets()),
                            "without --flatten the fields stay interactive")

    def test_fill_form_rejects_unknown_fields_and_writes_nothing(self):
        """Ensures fill form rejects unknown fields and writes nothing."""
        source = self.make_form()
        values = self.write_json("bad.json", {"Nope": "x"})
        out = self.work / "rejected.pdf"
        result = self.js("fill_form.mjs", source, values, out, code=1)
        self.assertIn("Form values rejected; no output written:", result.stderr)
        self.assertIn('no form field with the name "Nope"', result.stderr)
        self.assertFalse(out.exists())

    def test_fill_form_type_error_preserves_existing_output(self):
        """One invalid checkbox rejects a valid text update without touching output or input."""
        source = self.make_form()
        original = source.read_bytes()
        mapping = self.write_json("invalid.json", {"Name": "Casey", "Agree": "true"})
        target = self.write_bytes("existing.pdf", b"Existing deliverable")
        result = self.run_node(JS / "fill_form.mjs", source, mapping, target, code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checkbox value must be true or false", result.stderr)
        self.assertEqual(target.read_bytes(), b"Existing deliverable")
        self.assertEqual(source.read_bytes(), original)

    def test_fill_form_prints_usage_without_arguments(self):
        """Ensures fill form prints usage without arguments."""
        result = self.js("fill_form.mjs", code=2)
        self.assertAllIn(["Usage (positional):", "Usage (flags):", "--flatten"],
                         result.stdout + result.stderr)

    def test_install_deps_is_idempotent(self):
        """Ensures install deps is idempotent."""
        result = self.run_shell(JS / "install_deps.sh", cwd=self.work)
        self.assertIn("dependencies already present", result.stdout)


if __name__ == "__main__":
    unittest.main()
