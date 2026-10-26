"""Reviewable coverage inventory adapted from agent-skills PR #8.

An explicit script-to-suite map replaces substring matching, which could credit
an unrelated same-named helper or a comment as coverage. This records ownership,
not a line-coverage measurement. Vendored Lemo code is hash-checked by the motion
suite; executing every upstream demo is outside these local wrapper contracts.
"""

import ast
import json
from pathlib import Path
import subprocess
import unittest

from skill_scripts import ROOT

SCRIPT_SUFFIXES = {'.py', '.js', '.mjs', '.sh'}
VENDORED = 'skills/create-motion-videos/assets/lemo/'
SELF_TESTS = {
    'skills/create-motion-videos/scripts/test_prepare_runtime.py',
    'skills/pdf/scripts/test_interpreter.py',
    'skills/skill-creator/scripts/test_quick_validate.py',
    'skills/presenter-video/tests/test_provider_job.py',
}


def tracked_scripts():
    # Include files staged for this change, and nonignored new helpers, so a
    # missing test is caught before committing as well as in a clean CI checkout.
    result = subprocess.run(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '--', 'skills/'],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return {path for path in result.stdout.splitlines()
            if Path(path).suffix in SCRIPT_SUFFIXES}


class ScriptInventoryTests(unittest.TestCase):
    def test_every_maintained_script_has_an_existing_suite(self):
        """New or removed helpers require an explicit coverage-inventory update."""
        mapping = json.loads((ROOT / 'tests/script_inventory.json').read_text())
        recorded = [path for paths in mapping.values() for path in paths]
        self.assertEqual(len(recorded), len(set(recorded)), 'duplicate inventory entries')
        expected = {p for p in tracked_scripts() if not p.startswith(VENDORED)}
        self.assertEqual(set(recorded), expected)
        for suite, paths in mapping.items():
            with self.subTest(suite=suite):
                self.assertTrue((ROOT / suite).is_file())
                self.assertTrue(paths)
                self.assertTrue(any(isinstance(n, ast.FunctionDef) and n.name.startswith('test_')
                                    for n in ast.walk(ast.parse((ROOT / suite).read_text()))))
                for path in paths:
                    self.assertTrue((ROOT / path).is_file(), path)

    def test_vendored_exclusion_matches_the_pinned_manifest(self):
        """The single excluded tree is attributed, pinned source, not local helpers."""
        manifest = json.loads((ROOT / 'skills/create-motion-videos/references/upstream-manifest.json').read_text())
        pinned = {VENDORED + row['path'] for row in manifest['included']}
        excluded = {p for p in tracked_scripts() if p.startswith(VENDORED)}
        self.assertTrue(excluded)
        self.assertLessEqual(excluded, pinned)

    def test_all_suites_and_self_tests_are_wired_into_ci(self):
        """CI discovers every top-level suite and explicitly runs skill-local regressions."""
        workflow = (ROOT / '.github/workflows/ci.yml').read_text()
        self.assertIn("python -m unittest discover -s tests -p 'test_*.py'", workflow)
        for path in SELF_TESTS:
            self.assertIn('python ' + path, workflow)
        self.assertIn("python -m unittest discover -s tests/media -p 'test_*.py'", workflow)
        mapping = json.loads((ROOT / 'tests/script_inventory.json').read_text())
        for suite in mapping:
            if suite not in SELF_TESTS:
                self.assertEqual(Path(suite).parent, Path('tests'))
                self.assertTrue(Path(suite).name.startswith('test_'))
        discovered_self_tests = {p for p in tracked_scripts()
                                 if not p.startswith(VENDORED) and Path(p).name.startswith('test_')}
        self.assertEqual(discovered_self_tests, SELF_TESTS)

    def test_all_test_modules_parse(self):
        """All test modules are valid Python; the harness is not named for discovery."""
        for module in (ROOT / 'tests').glob('*.py'):
            with self.subTest(module=module.name):
                ast.parse(module.read_text(), filename=str(module))
        for module in (ROOT / 'tests/media').glob('test_*.py'):
            with self.subTest(module=module.name):
                ast.parse(module.read_text(), filename=str(module))
        self.assertFalse(Path('skill_scripts.py').match('test_*.py'))


if __name__ == '__main__':
    unittest.main()
