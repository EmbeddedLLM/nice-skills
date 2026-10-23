#!/usr/bin/env python3
"""Self-tests for tools/measure_similarity.py.

Run from the repository root:

    python3 -m unittest discover -s tools -p 'test_*.py' -v

The fixtures are synthetic: a small corpus tree and a small local tree that
exercise each detection pass (byte identity, name-matched difflib, renamed
shingle containment), the generated-boilerplate exclusion, and the
``--fail-above`` gate.
"""

from __future__ import annotations

import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import measure_similarity as ms  # noqa: E402

GUIDE_LINES = [
    f"Sentence {i} of the quarterly reporting workflow explains one verification step." for i in range(24)
]
GUIDE_ORIGINAL = "\n".join(GUIDE_LINES) + "\n"
GUIDE_PARAPHRASE = (
    "\n".join(
        f"Rewritten observation {i} about reporting." if i % 3 == 0 else line
        for i, line in enumerate(GUIDE_LINES)
    )
    + "\n"
)

HELPER_ORIGINAL = "\n".join(
    [
        "def calibrate_flux_widget(payload, tolerance):",
        "    normalized = normalize_flux_payload(payload)",
        "    table = build_calibration_table(normalized, tolerance)",
    ]
    + [f"    table.adjust_band({band}, coefficient_{band} * tolerance)" for band in range(20)]
    + ["    return table.commit_calibration(normalized.identifier)", ""]
)
HELPER_RENAMED = "\n".join(
    [
        "# Rewritten module preamble: this variant ships under a new name and",
        "# carries a freshly worded comment block around the same logic.",
        "def calibrate_flux_widget(request, tolerance):",
        "    normalized = normalize_flux_payload(request)",
        "    table = build_calibration_table(normalized, tolerance)",
    ]
    + [f"    table.adjust_band({band}, coefficient_{band} * tolerance)" for band in range(20)]
    + ["    return table.commit_calibration(normalized.identifier)", ""]
)

BLOB_BYTES = b"BINARY\x00BLOB\x01DATA\x02\x03"

CORPUS_PACKAGE_JSON = '{\n  "name": "corpus-runtime",\n  "version": "1.0.0",\n  "dependencies": {\n    "left-pad": "^1.3.0"\n  }\n}\n'
LOCAL_PACKAGE_JSON = '{\n  "name": "corpus-runtime",\n  "version": "1.0.1",\n  "dependencies": {\n    "left-pad": "^1.3.0"\n  }\n}\n'

FRESH_TEXT = (
    "An entirely original note about gardening in coastal climates, soil salinity, "
    "windbreaks, drip irrigation scheduling, and mulch depth choices for raised beds. "
    "None of these sentences appear anywhere in the reference corpus.\n"
)


class SimilarityScanTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = pathlib.Path(self._tmp.name)
        self.corpus = root / "corpus"
        self.local = root / "local"
        self.fresh_local = root / "fresh_local"

        self._write(self.corpus / "docs" / "guide.md", GUIDE_ORIGINAL)
        self._write(self.corpus / "code" / "helper.py", HELPER_ORIGINAL)
        self._write(self.corpus / "docs" / "package.json", CORPUS_PACKAGE_JSON)
        self._write(self.corpus / "docs" / "LICENSE.txt", "MIT License\n\nCopyright (c) 2026 Example\n")
        (self.corpus / "assets").mkdir(parents=True)
        (self.corpus / "assets" / "blob.bin").write_bytes(BLOB_BYTES)

        self._write(self.local / "pkg" / "guide.md", GUIDE_PARAPHRASE)
        self._write(self.local / "pkg" / "widget_tool.py", HELPER_RENAMED)
        self._write(self.local / "pkg" / "package.json", LOCAL_PACKAGE_JSON)
        self._write(self.local / "pkg" / "LICENSE.txt", "MIT License\n\nCopyright (c) 2026 Example\n")
        self._write(self.local / "pkg" / "original.md", FRESH_TEXT)
        (self.local / "pkg2").mkdir(parents=True)
        (self.local / "pkg2" / "blob.bin").write_bytes(BLOB_BYTES)

        self._write(self.fresh_local / "pkg" / "original.md", FRESH_TEXT)

    @staticmethod
    def _write(path: pathlib.Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_main(self, *extra: str, local: pathlib.Path | None = None) -> tuple[int, dict]:
        out, err = io.StringIO(), io.StringIO()
        argv = ["--local", str(local or self.local), "--corpus", str(self.corpus), "--json", *extra]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ms.main(argv)
        return code, json.loads(out.getvalue())

    @staticmethod
    def _by_local(report: dict, section: str) -> dict[str, dict]:
        return {row["local"]: row for row in report[section]}

    def test_byte_identical_is_reported(self) -> None:
        """Ensures byte identical is reported."""
        _, report = self.run_main()
        identical = self._by_local(report, "identical")
        self.assertIn("pkg2/blob.bin", identical)
        self.assertTrue(identical["pkg2/blob.bin"]["corpus"].endswith("blob.bin"))

    def test_reworded_same_name_file_is_reported_by_difflib(self) -> None:
        """Ensures reworded same name file is reported by difflib."""
        _, report = self.run_main()
        similar = self._by_local(report, "similar")
        self.assertIn("pkg/guide.md", similar)
        self.assertGreaterEqual(similar["pkg/guide.md"]["difflib"], 0.35)
        self.assertTrue(similar["pkg/guide.md"]["difflib_source"].endswith("guide.md"))

    def test_renamed_reworded_file_is_reported_by_shingles(self) -> None:
        """Ensures renamed reworded file is reported by shingles."""
        _, report = self.run_main()
        similar = self._by_local(report, "similar")
        self.assertIn("pkg/widget_tool.py", similar)
        self.assertGreaterEqual(similar["pkg/widget_tool.py"]["shingle"], 0.30)
        self.assertTrue(similar["pkg/widget_tool.py"]["shingle_source"].endswith("helper.py"))

    def test_generated_boilerplate_is_excluded_by_default(self) -> None:
        """Ensures generated boilerplate is excluded by default."""
        _, report = self.run_main()
        similar = self._by_local(report, "similar")
        self.assertNotIn("pkg/package.json", similar)

    def test_generated_boilerplate_is_included_with_flag(self) -> None:
        """Ensures generated boilerplate is included with flag."""
        _, report = self.run_main("--include-noise")
        similar = self._by_local(report, "similar")
        self.assertIn("pkg/package.json", similar)
        self.assertGreaterEqual(similar["pkg/package.json"]["difflib"], 0.35)

    def test_license_notices_are_excluded_by_default(self) -> None:
        """Ensures license notices are excluded by default."""
        _, report = self.run_main()
        identical = self._by_local(report, "identical")
        self.assertNotIn("pkg/LICENSE.txt", identical)
        _, report = self.run_main("--include-noise")
        identical = self._by_local(report, "identical")
        self.assertIn("pkg/LICENSE.txt", identical)

    def test_unrelated_file_is_not_reported(self) -> None:
        """Ensures unrelated file is not reported."""
        _, report = self.run_main()
        similar = self._by_local(report, "similar")
        identical = self._by_local(report, "identical")
        self.assertNotIn("pkg/original.md", similar)
        self.assertNotIn("pkg/original.md", identical)

    def test_group_summary_counts(self) -> None:
        """Ensures group summary counts."""
        _, report = self.run_main("--by-skill")
        groups = report["groups"]
        self.assertEqual(groups["pkg"]["files"], 5)
        self.assertEqual(groups["pkg2"]["identical"], 1)
        self.assertGreaterEqual(groups["pkg"]["similar"], 2)

    def test_fail_above_gate_exit_codes(self) -> None:
        """Ensures fail above gate exit codes."""
        code, _ = self.run_main("--fail-above", "0.9")
        self.assertEqual(code, 1)  # byte-identical blob violates any threshold
        code, _ = self.run_main("--fail-above", "0.99", local=self.fresh_local)
        self.assertEqual(code, 0)

    def test_fail_above_rejects_out_of_range(self) -> None:
        """Ensures fail above rejects out of range."""
        with self.assertRaises(SystemExit) as caught:
            with contextlib.redirect_stderr(io.StringIO()):
                ms.main(["--local", str(self.local), "--corpus", str(self.corpus), "--fail-above", "1.5"])
        self.assertEqual(caught.exception.code, 2)

    def test_cli_requires_explicit_corpus(self):
        """Reject an omitted reference corpus instead of assuming a repository archive."""
        with contextlib.redirect_stderr(io.StringIO()) as errors, self.assertRaises(SystemExit) as caught:
            ms.main(['--local', str(self.local)])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn('--corpus', errors.getvalue())

    def test_missing_root_is_usage_error(self) -> None:
        """Ensures missing root is usage error."""
        with self.assertRaises(SystemExit) as caught:
            with contextlib.redirect_stderr(io.StringIO()):
                ms.main(["--local", str(self.local), "--corpus", str(self.corpus / "does-not-exist")])
        self.assertEqual(caught.exception.code, 2)

    def test_exclude_skips_local_subtree(self) -> None:
        """Ensures exclude skips local subtree."""
        _, report = self.run_main("--exclude", "pkg2")
        identical = self._by_local(report, "identical")
        self.assertNotIn("pkg2/blob.bin", identical)
        self.assertNotIn("pkg2", report["groups"])


if __name__ == "__main__":
    unittest.main()
