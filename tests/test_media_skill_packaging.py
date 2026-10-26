"""Packaging invariants for the standalone archive adaptations and vendored asset bundles."""

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest
from urllib.parse import unquote, urlsplit

from skill_scripts import SKILLS, binary


class MediaPackagingTests(unittest.TestCase):
    def test_bundled_markdown_links_stay_inside_each_skill(self):
        """Copied packages resolve their documented resources without sibling skills."""
        for name in ('explainer-video', 'presenter-video'):
            root = (SKILLS / name).resolve()
            for document in root.rglob('*.md'):
                for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', document.read_text()):
                    url = urlsplit(target)
                    if url.scheme or url.netloc or not url.path:
                        continue
                    resolved = (document.parent / unquote(url.path)).resolve()
                    with self.subTest(document=str(document), target=target):
                        self.assertTrue(resolved.is_relative_to(root))
                        self.assertTrue(resolved.exists())

    def test_original_lanshu_notice_is_preserved_in_each_package(self):
        """Standalone redistribution retains the original selected-source notice."""
        expected = hashlib.sha256((SKILLS / 'presenter-video/LICENSE-lanshu.txt').read_bytes()).hexdigest()
        # The pinned source notice, not an attribution summary, must travel with each copy.
        self.assertEqual(expected, '5ee4e300085ba144aae1ec5b72774ef5408bd933c1f02f429359313a4251bfad')
        for name in ('explainer-video', 'presenter-video'):
            self.assertEqual(hashlib.sha256((SKILLS / name / 'LICENSE-lanshu.txt').read_bytes()).hexdigest(), expected)


MANIFESTS = (
    ('create-motion-videos', Path('references/vendored-assets.json')),
    ('design-taste', Path('examples/vendored-assets.json')),
)


class VendoredAssetBundleTests(unittest.TestCase):
    """Every bundled third-party asset is hashed, attributed, and accompanied by its licence."""

    def bundles(self):
        for skill, relative in MANIFESTS:
            package = (SKILLS / skill).resolve()
            manifest = json.loads((package / relative).read_text())
            self.assertTrue(manifest['bundles'])
            for bundle in manifest['bundles']:
                yield package, bundle

    def test_every_listed_file_exists_with_its_pinned_hash(self):
        """A replaced or truncated asset changes its hash and fails this check."""
        for package, bundle in self.bundles():
            self.assertTrue(bundle['files'], bundle['id'])
            for entry in bundle['files']:
                path = package / entry['path']
                with self.subTest(bundle=bundle['id'], file=entry['path']):
                    self.assertTrue(path.is_file())
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry['sha256'])
                    self.assertEqual(path.stat().st_size, entry['bytes'])

    def test_the_bundle_list_is_complete(self):
        """An asset added to a vendored directory without a manifest entry is unreviewed."""
        for package, bundle in self.bundles():
            root = package / bundle['path']
            present = {path.relative_to(package).as_posix() for path in root.rglob('*') if path.is_file()}
            listed = {entry['path'] for entry in bundle['files']}
            with self.subTest(bundle=bundle['id']):
                self.assertEqual(present - listed, set(), 'unlisted file in a vendored bundle')
                self.assertEqual(listed - present, set(), 'manifest lists a missing file')

    def test_each_bundle_names_its_source_and_licence(self):
        """Redistribution needs the upstream identity, the licence, and a notice that travels."""
        for package, bundle in self.bundles():
            source = bundle['source']
            licence = bundle['license']
            with self.subTest(bundle=bundle['id']):
                self.assertTrue(source['repository'].startswith('https://github.com/'))
                self.assertRegex(source['commit'], r'^[0-9a-f]{40}$')
                self.assertRegex(source['retrieved'], r'^\d{4}-\d{2}-\d{2}$')
                self.assertTrue(licence['spdx'])
                self.assertTrue(licence['note'].strip())
                notice = package / licence['file']
                self.assertTrue(notice.is_file(), licence['file'])
                self.assertGreater(notice.stat().st_size, 200)

    def test_each_bundle_is_reachable_from_its_entry_point(self):
        """An asset no instruction points at is dead weight: SKILL.md must name its path."""
        for package, bundle in self.bundles():
            with self.subTest(bundle=bundle['id']):
                self.assertIn(bundle['path'], (package / 'SKILL.md').read_text())

    def test_the_screenshot_bundle_keeps_its_share_alike_notice(self):
        """CC BY-SA media must not be presented as MIT: credits and legal code travel with it."""
        package, bundle = next((p, b) for p, b in self.bundles() if b['id'] == 'example-screenshots')
        self.assertEqual(bundle['license']['spdx'], 'CC-BY-SA-4.0')
        credits = package / 'examples/v2/CREDITS.md'
        legal = package / 'examples/v2/LICENSE-CC-BY-SA-4.0.txt'
        notice = (package / 'NOTICE-examples.md').read_text()
        self.assertIn('CC BY-SA 4.0', credits.read_text())
        self.assertIn('Attribution-ShareAlike 4.0 International', legal.read_text())
        self.assertIn('not MIT', notice)
        self.assertIn('examples/v2/CREDITS.md', notice)
        self.assertGreaterEqual(len(re.findall(r'CC BY-SA', credits.read_text())), 10)

    def test_vendored_python_scripts_parse_and_javascript_passes_a_syntax_check(self):
        """A partial or corrupted copy is caught without installing the upstream runtimes."""
        python_files, javascript_files = [], []
        for package, bundle in self.bundles():
            for entry in bundle['files']:
                path = package / entry['path']
                if path.suffix == '.py':
                    python_files.append(path)
                elif path.suffix in {'.js', '.mjs'}:
                    javascript_files.append(path)
        self.assertTrue(python_files and javascript_files)
        for path in python_files:
            with self.subTest(script=str(path.name)):
                ast.parse(path.read_text(), filename=str(path))
        if binary('node') is None:
            self.skipTest('node is not installed')
        for path in javascript_files:
            with self.subTest(script=str(path.name)):
                result = subprocess.run([binary('node'), '--check', str(path)],
                                        capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_bundled_notices_name_the_third_party_sources(self):
        """The CC0 attribution and the lyric-alignment boundary are documented next to the assets."""
        motion = SKILLS / 'create-motion-videos'
        notices = (motion / 'references/mg-styles15-asset-notices.md').read_text()
        self.assertIn('ambientCG', notices)
        self.assertIn('Poly Haven', notices)
        self.assertIn('washi', notices)
        sources = (motion / 'SOURCES.md').read_text()
        self.assertIn('assets/hand-painted-cartoon', sources)
        self.assertIn('assets/lyric-alignment', sources)
        alignment = (motion / 'assets/lyric-alignment/LICENSE').read_text()
        self.assertIn('Giacomo Magnanini', alignment)


if __name__ == '__main__':
    unittest.main()
