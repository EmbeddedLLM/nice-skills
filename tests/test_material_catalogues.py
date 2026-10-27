"""Verify the portable external-material indexes against their underlying collections."""
from collections import Counter
import json
from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / 'skills'


def read(path):
    return json.loads(path.read_text())


class MaterialCatalogueTests(unittest.TestCase):
    def test_every_skill_is_indexed_with_valid_portable_records(self):
        """Ensures every published skill has a complete, internally consistent portable index."""
        index = read(ROOT / 'SOURCE_CATALOGUE.json')['catalogues']
        published = {p.parent.name for p in SKILLS.glob('*/SKILL.md')}
        self.assertEqual({row['skill'] for row in index}, published)
        self.assertEqual(len(index), len(published))
        for item in index:
            with self.subTest(skill=item['skill']):
                root = SKILLS / item['skill']
                path = ROOT / item['catalogue_path']
                self.assertEqual(path, root / 'references/material-catalogue.json')
                data = read(path)
                self.assertEqual(data['skill'], item['skill'])
                self.assertEqual(data['schema_version'], 1)
                self.assertEqual(data['path_base'], 'skill-root')
                self.assertEqual(data['unknown_value'], 'Unknown')
                entries = data['entries']
                self.assertTrue(entries)
                self.assertEqual(len({r['id'] for r in entries}), len(entries))
                self.assertEqual(data['counts']['entries'], len(entries))
                self.assertEqual(item['entries'], len(entries))
                unknown = sum(r['source_url'] == 'Unknown' for r in entries)
                self.assertEqual(item['unknown_sources'], unknown)
                self.assertEqual(data['counts']['unknown_sources'], unknown)
                self.assertEqual(data['counts']['collections'], dict(Counter(r['collection'] for r in entries)))
                for row in entries:
                    with self.subTest(material=row['id']):
                        for field in ('id', 'collection', 'title', 'category', 'description',
                                      'source_url', 'source_commit', 'license', 'provenance_path', 'notes'):
                            self.assertIsInstance(row[field], str)
                            self.assertTrue(row[field].strip())
                        for field in ('uses', 'paths', 'notice_paths'):
                            self.assertIsInstance(row[field], list)
                            self.assertTrue(all(isinstance(v, str) and v for v in row[field]))
                        self.assertTrue(row['uses'])
                        self.assertTrue(row['paths'])
                        for field in ('source_url', 'distribution_url'):
                            if field in row and row[field] != 'Unknown':
                                url = urlsplit(row[field])
                                self.assertIn(url.scheme, ('https', 'http'))
                                self.assertTrue(url.netloc)
                        for field in ('source_commit', 'distribution_commit'):
                            if field in row:
                                self.assertTrue(row[field] == 'Unknown' or re.fullmatch(r'[0-9a-f]{40}', row[field]))
                        for rel in row['paths'] + row['notice_paths'] + [row['provenance_path']]:
                            target = (root / rel).resolve()
                            self.assertTrue(target.is_relative_to(root.resolve()), rel)
                            self.assertTrue(target.exists(), str(target))
                        if 'record_locator' in row:
                            self.assertTrue(str(row['record_locator']))

    def test_named_collections_keep_every_selectable_material(self):
        """Ensures new recipes, effects, guides, styles and fonts cannot disappear from the indexes."""
        def ids(skill, collection=None):
            rows = read(SKILLS / skill / 'references/material-catalogue.json')['entries']
            return {r['id'] for r in rows if collection is None or r['collection'] == collection}

        themes = SKILLS / 'theme-factory/references/hallmark'
        self.assertEqual(ids('theme-factory', 'hallmark'), {'hallmark:' + p.stem for p in themes.glob('*.md')})
        sounds = read(SKILLS / 'sound-design/assets/sounds.json')
        self.assertEqual(ids('sound-design', 'earshot') - {'earshot:synthesis'}, {'earshot:' + k for k in sounds})
        library = SKILLS / 'game-development/library'
        self.assertEqual(ids('game-development', 'gamedev'),
                         {'gamedev:' + str(p.parent.relative_to(library)) for p in library.rglob('SKILL.md')})
        styles = [r for p in (SKILLS / 'vector-art/styles/registry').glob('*.json') for r in read(p)]
        self.assertEqual(ids('vector-art', 'buildfast') - {'buildfast:helpers'}, {'buildfast:' + r['id'] for r in styles})
        motion = ids('create-motion-videos')
        for row in read(SKILLS / 'create-motion-videos/references/catalogue.json')['entries']:
            self.assertIn(row['id'], motion)
        for path in (SKILLS / 'create-motion-videos/assets/prompt-library').glob('*.json'):
            data = read(path)
            self.assertEqual(ids('create-motion-videos', data['library']),
                             {data['library'] + ':' + r['id'] for r in data['items']})
        fonts = read(SKILLS / 'create-motion-videos/references/font-replacements.json')['fonts']
        self.assertEqual(ids('create-motion-videos', 'font'), {'font:' + Path(r['path']).name for r in fonts})
        for path in (SKILLS / 'design-taste/library').glob('*.json'):
            data = read(path)
            if isinstance(data, list) and path.stem != 'sites':
                collection = 'taste-' + path.stem
                self.assertEqual(ids('design-taste', collection), {collection + ':' + r['id'] for r in data})

    def test_intermediaries_and_asset_licenses_remain_distinct(self):
        """Ensures known carriers do not conceal unresolved original sources or override asset terms."""
        motion = read(SKILLS / 'create-motion-videos/references/material-catalogue.json')['entries']
        for row in motion:
            if row['collection'] == 'mg-texture':
                self.assertEqual(row['source_url'], 'Unknown')
                self.assertTrue(row['distribution_url'].startswith('https://github.com/'))
            if row['collection'] == 'font':
                self.assertEqual(row['license'], 'OFL-1.1')
                self.assertTrue(row['notice_paths'])
            if row['source_url'].startswith('https://x.com/'):
                self.assertEqual(row['source_commit'], 'Unknown')
        taste = read(SKILLS / 'design-taste/references/material-catalogue.json')['entries']
        for row in taste:
            if row['category'] == 'image':
                self.assertEqual(row['license'], 'CC-BY-SA-4.0')
                self.assertIn('examples/v2/CREDITS.md', row['notice_paths'])


if __name__ == '__main__':
    unittest.main()
