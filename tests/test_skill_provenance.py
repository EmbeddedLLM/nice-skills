"""Check portable provenance, unchanged notices, and the remediation scope.

These are packaging invariants. They do not establish legal ownership or
measure whether an agent follows a prose workflow correctly.
"""
import hashlib
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

from skill_scripts import ROOT, SKILLS

PACKAGES = ('deep-research', 'documents', 'pdf', 'slides', 'spreadsheets')


class ProvenanceTests(unittest.TestCase):
    def manifests(self):
        for name in PACKAGES:
            package = SKILLS / name
            filename = 'provenance.json' if name == 'deep-research' else 'source-manifest.json'
            yield package, json.loads((package / 'references' / filename).read_text())

    def test_selected_sources_are_pinned_and_notices_are_intact(self):
        """A standalone copy retains the notices and immutable source identities."""
        for package, manifest in self.manifests():
            self.assertTrue(manifest['reference_files'])
            for reference in manifest['reference_files']:
                self.assertRegex(reference['sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(manifest['sources'])
            notices = list(manifest['package_notices'])
            for source in manifest['sources']:
                with self.subTest(package=package.name, source=source['id']):
                    self.assertRegex(source['commit'], r'^[0-9a-f]{40}$')
                    self.assertIn(source['license_spdx'], ('MIT', 'Apache-2.0'))
                    self.assertTrue(source['retained_notices'])
                    self.assertTrue(source['source_files'])
                    for item in source['source_files']:
                        self.assertTrue(item['url'].startswith(source['repository_url'] + '/blob/' + source['commit'] + '/'))
                        self.assertRegex(item['sha256'], r'^[0-9a-f]{64}$')
                    notices.extend(source['retained_notices'])
            for notice in notices:
                with self.subTest(package=package.name, notice=notice['local_path']):
                    path = (package / notice['local_path']).resolve()
                    self.assertTrue(path.is_relative_to(package.resolve()))
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), notice['sha256'])

    def test_replacement_scope_and_helpers_exist(self):
        """All issue-6 replacements remain present and attributed to the right package."""
        manifest = json.loads((ROOT / 'tools/remediation.json').read_text())
        self.assertEqual(len(manifest['files']), 62)
        paths = manifest['files'] + manifest['supporting_files']
        self.assertEqual(len(paths), len(set(paths)))
        for path in paths:
            self.assertTrue((SKILLS / path).is_file(), path)
        for package, provenance in self.manifests():
            if package.name == 'deep-research':
                continue
            recorded = provenance['adapted_guides'] + provenance['replacement_helpers']
            expected = [p.split('/', 1)[1] for p in manifest['files'] if p.startswith(package.name + '/')]
            self.assertEqual(set(recorded), set(expected))

    def test_local_links_in_rewritten_guides_resolve_within_package(self):
        """Changed guides remain usable without sibling skills or authoring references."""
        for package, manifest in self.manifests():
            guides = ['SKILL.md', 'SOURCES.md'] + manifest.get('adapted_guides', [])
            if package.name == 'deep-research':
                guides += ['references/product-research.md', 'THIRD_PARTY_NOTICES.md']
            for name in guides:
                path = package / name
                for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text()):
                    url = urlsplit(target)
                    if url.scheme or url.netloc or not url.path:
                        continue
                    resolved = (path.parent / unquote(url.path)).resolve()
                    with self.subTest(guide=str(path), target=target):
                        self.assertTrue(resolved.is_relative_to(package.resolve()))
                        self.assertTrue(resolved.exists())


if __name__ == '__main__':
    unittest.main()
