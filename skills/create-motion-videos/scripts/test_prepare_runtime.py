"""Validate portable runtime preparation using a small synthetic bundle."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import prepare_runtime


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / "skill"
        self.source = self.skill / "assets/lemo"
        self.source.mkdir(parents=True)
        content = b"synthetic runtime\n"
        (self.source / "fixture.txt").write_bytes(content)
        self.manifest = self.skill / "manifest.json"
        self.manifest.write_text(json.dumps({
            "commit": "fixture", "repository": "synthetic",
            "included": [{"path": "fixture.txt", "sha256": hashlib.sha256(content).hexdigest()}],
        }))
        self.dest = self.root / "runtime"

    def invoke(self, *args):
        with patch.object(prepare_runtime, "SKILL", self.skill), \
             patch.object(prepare_runtime, "SOURCE", self.source), \
             patch.object(prepare_runtime, "MANIFEST", self.manifest), \
             patch.object(sys, "argv", ["prepare_runtime.py", str(self.dest), *args]), \
             redirect_stdout(io.StringIO()):
            prepare_runtime.main()

    def test_copy_and_reuse(self):
        """A verified runtime can be copied and reused without changing its source."""
        self.invoke()
        self.assertEqual((self.dest / "fixture.txt").read_bytes(), (self.source / "fixture.txt").read_bytes())
        self.invoke("--reuse")

    def test_protect_existing_and_drift(self):
        """Nonempty unrelated directories and changed bundle hashes are rejected."""
        self.dest.mkdir()
        (self.dest / "user.txt").write_text("keep")
        with self.assertRaises(SystemExit):
            self.invoke()
        self.assertEqual((self.dest / "user.txt").read_text(), "keep")
        self.dest = self.root / "new-runtime"
        (self.source / "fixture.txt").write_text("changed")
        with self.assertRaises(RuntimeError):
            self.invoke()
        self.assertFalse(self.dest.exists())

    def test_pinned_offline_tiers(self):
        """Install tiers select repository pins without executing upstream installers."""
        for tier in ("core", "voice", "music"):
            self.dest = self.root / tier
            with self.subTest(tier=tier), \
                 patch.object(prepare_runtime.shutil, "which", return_value="/tool"), \
                 patch.object(prepare_runtime.subprocess, "check_output", side_effect=["24", "[3, 12]"]), \
                 patch.object(prepare_runtime, "run") as run:
                self.invoke("--install", tier, "--skip-browser-download")
                commands = [call.args[0] for call in run.call_args_list]
                pip = next(cmd for cmd in commands if "pip" in cmd)
                self.assertIn(str(self.skill / "requirements/core.txt"), pip)
                if tier != "core":
                    self.assertIn(str(self.skill / f"requirements/{tier}.txt"), pip)
                self.assertNotIn("requirements.txt", pip)
                self.assertEqual(commands[0][:2], ["npm", "ci"])


if __name__ == "__main__":
    unittest.main()
