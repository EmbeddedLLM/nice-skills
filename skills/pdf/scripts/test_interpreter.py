"""Exercise PDF wrapper subprocesses with an unusable `python` on PATH.

Run with this skill's requirements installed. Poppler is required for rendering;
the redaction and Node form tests run only when their optional dependencies exist.
No test installs dependencies or writes into the skill.
"""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from reportlab.pdfgen.canvas import Canvas

SCRIPTS = Path(__file__).resolve().parent


@unittest.skipUnless(os.name == "posix" and shutil.which("pdftoppm"), "Requires POSIX and Poppler")
class InterpreterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        fake_python = fake_bin / "python"
        fake_python.write_text("#!/bin/sh\nexit 99\n")
        fake_python.chmod(0o755)
        self.env = {**os.environ, "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", "")}
        self.pdf = self.root / "input.pdf"
        canvas = Canvas(str(self.pdf))
        canvas.drawString(50, 700, "Synthetic fixture")
        canvas.save()

    def command(self, script, *args, expected=0):
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / script), *map(str, args)],
            env=self.env, capture_output=True, text=True, timeout=90,
        )
        self.assertEqual(proc.returncode, expected, proc.stdout + proc.stderr)
        return proc

    def test_info_and_missing_input(self):
        """Inspection inherits the active environment and propagates input errors."""
        result = self.command("pdf_extract.py", "info", self.pdf, "--json")
        self.assertIsInstance(json.loads(result.stdout), dict)
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "pdf_extract.py"), "info", str(self.root / "absent.pdf")],
            env=self.env, capture_output=True, timeout=30,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertNotEqual(proc.returncode, 99)

    def test_compare_and_parity(self):
        """Both rendering wrappers launch the same installed Python environment."""
        self.command("compare_renders.py", self.pdf, self.pdf, "--out_dir", self.root / "diff", "--dpi", 72)
        summary = json.loads((self.root / "diff/summary.json").read_text())
        self.assertEqual(summary["changed_pages"], 0)
        self.command("renderer_parity.py", self.pdf, "--out_dir", self.root / "parity", "--dpi", 72)
        self.assertTrue((self.root / "parity/summary.json").is_file())

    def test_batch_operations(self):
        """Render, inspect, and normalize all retain the invoking interpreter."""
        for operation in ("render", "inspect", "normalize"):
            with self.subTest(operation=operation):
                out = self.root / operation
                self.command("batch_pdf.py", operation, "--in_glob", self.pdf, "--out_root", out)
                self.assertTrue(any(out.rglob("*")))
                if operation == "inspect":
                    report = json.loads((out / "input.pdf.json").read_text())
                    self.assertNotIn("error", report)
        self.command("batch_pdf.py", "render", "--in_glob", self.root / "missing*.pdf",
                     "--out_root", self.root / "missing", expected=2)

    def test_box_picker_and_edit_smoke(self):
        """Interactive page generation and pagination work without PATH Python."""
        self.command("box_picker_html.py", self.pdf, "--out", self.root / "picker.html", "--tmp_dir", self.root / "picker-pages", "--dpi", 72)
        self.assertIn("data:image/png;base64", (self.root / "picker.html").read_text())
        self.command("edit_smoketest.py", "--workdir", self.root / "edit", "--dpi", 72)

    @unittest.skipUnless(importlib.util.find_spec("fitz"), "Optional PyMuPDF not installed")
    def test_redaction_smoke(self):
        """The redaction smoke flow keeps its removal and rendering checks usable."""
        self.command("redact_smoketest.py", "--workdir", self.root / "redact", "--dpi", 72)

    @unittest.skipUnless((SCRIPTS.parent / "js/node_modules").is_dir(), "Optional Node runtime not prepared")
    def test_forms_smoke(self):
        """A prepared Node form runtime can launch the Python visual comparison."""
        self.command("forms_smoketest.py", "--workdir", self.root / "forms", "--dpi", 72)


if __name__ == "__main__":
    unittest.main()
