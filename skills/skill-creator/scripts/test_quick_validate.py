"""Regression checks for metadata accepted by the skill authoring workflow."""

import tempfile
import unittest
from pathlib import Path

from quick_validate import validate_skill


class MetadataTests(unittest.TestCase):
    def check(self, frontmatter, body="# Example\n"):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "example-skill"
            path.mkdir()
            (path / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n{body}")
            return validate_skill(path)

    def test_valid_optional_fields(self):
        """Portable compatibility and string metadata remain supported."""
        ok, message = self.check(
            "name: example-skill\ndescription: Summarize supplied logs.\n"
            "compatibility: Python 3.12\nmetadata:\n  version: '1'"
        )
        self.assertTrue(ok, message)

    def test_required_values(self):
        """Blank and non-string metadata cannot silently pass validation."""
        for field in ("name", "description"):
            for value in ("''", "'   '", "null", "42", "[]"):
                fields = {"name": "example-skill", "description": "Summarize logs."}
                fields[field] = value
                with self.subTest(field=field, value=value):
                    self.assertFalse(self.check("\n".join(f"{k}: {v}" for k, v in fields.items()))[0])

    def test_directory_match(self):
        """A valid-looking name cannot register a different directory."""
        self.assertFalse(self.check("name: another-skill\ndescription: Summarize logs.")[0])

    def test_scaffold(self):
        """Generated placeholders must be replaced before publishing."""
        self.assertFalse(self.check("name: example-skill\ndescription: Summarize logs.", "[TODO: workflow]")[0])

    def test_limits_and_unknown_keys(self):
        """Malformed optional fields and unsupported keys fail explicitly."""
        base = "name: example-skill\ndescription: Summarize logs.\n"
        for extra in ("compatibility: []", "compatibility: ''", "metadata: []", "metadata:\n  version: 1", "unknown: true"):
            with self.subTest(extra=extra):
                self.assertFalse(self.check(base + extra)[0])
        self.assertFalse(self.check("name: example-skill\ndescription: " + "x" * 1025)[0])

    def test_bad_yaml_or_missing_file(self):
        """Invalid or absent frontmatter yields a diagnostic rather than success."""
        self.assertFalse(self.check("name: [")[0])
        self.assertFalse(self.check("- list")[0])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(validate_skill(tmp)[0])


if __name__ == "__main__":
    unittest.main()
