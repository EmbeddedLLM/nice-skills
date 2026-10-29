"""Contracts for publishing the complete skill and palette collections."""
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SITE = runpy.run_path(str(ROOT / "tools/build_site.py"))


class HomepageTests(unittest.TestCase):
    def test_complete_static_site(self):
        """Ensures every skill and theme is packaged with portable local assets."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            SITE["build"](output)
            page = (output / "index.html").read_text()
            css = (output / "themes.css").read_text()
            skills = list((ROOT / "skills").glob("*/SKILL.md"))
            self.assertEqual(page.count('<article class="skill"'), len(skills))
            for skill in skills:
                self.assertIn(f"/skills/{skill.parent.name}/SKILL.md", page)
            theme_tools = runpy.run_path(str(ROOT / "skills/theme-factory/scripts/themes.py"))
            _, _, themes = theme_tools["load"]()
            self.assertEqual(page.count('<optgroup'), 10)
            for theme in themes:
                self.assertIn(f'value="{theme["slug"]}"', page)
                self.assertIn(f'[data-palette="{theme["slug"]}"]', css)
            self.assertNotIn("{{", page)
            repository_links = re.findall(r'href="(https://github.com/[^"]+)"', page)
            self.assertTrue(repository_links)
            for link in repository_links:
                self.assertTrue(link.startswith("https://github.com/EmbeddedLLM/nice-skills"), link)
            for asset in re.findall(r'(?:src|href)="\./([^\"]+)"', page):
                self.assertTrue((output / asset).is_file(), asset)
            self.assertTrue((output / ".nojekyll").is_file())
            self.assertEqual({file.name for file in output.iterdir()},
                             {"index.html", "styles.css", "themes.css", "app.js", "favicon.svg", ".nojekyll"})

    def test_build_is_repeatable(self):
        """Ensures rebuilding an unchanged collection produces identical artifacts."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            SITE["build"](output)
            before = {file.name: file.read_bytes() for file in output.iterdir()}
            SITE["build"](output)
            self.assertEqual(before, {file.name: file.read_bytes() for file in output.iterdir()})

    def test_incomplete_catalog_preserves_output(self):
        """Ensures invalid catalog data fails before modifying a previous build."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills/example").mkdir(parents=True)
            (root / "skills/example/SKILL.md").write_text("Example")
            (root / "skills/README.md").write_text("# Empty catalog")
            output = root / "dist"
            output.mkdir()
            (output / "index.html").write_text("Previous build")
            with patch.dict(SITE["catalog"].__globals__, ROOT=root):
                with self.assertRaisesRegex(ValueError, "every published skill"):
                    SITE["build"](output)
            self.assertEqual((output / "index.html").read_text(), "Previous build")
            (root / "skills/README.md").write_text("| [missing](missing/SKILL.md) | Purpose | Requirements |")
            with patch.dict(SITE["catalog"].__globals__, ROOT=root):
                with self.assertRaisesRegex(ValueError, "Missing catalog entry"):
                    SITE["build"](output)
            self.assertEqual((output / "index.html").read_text(), "Previous build")
