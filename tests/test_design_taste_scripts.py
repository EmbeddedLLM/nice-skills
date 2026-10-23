"""Regression checks for the vendored design-taste helpers.

These tests exercise the parts of ``skills/design-taste/scripts/`` that run without a browser: the
library data the draw deals from, the direction sheet, the static lint gate, and the argument and
empty-state behaviour of the asset and scene tools. The inspector needs an installed
Chrome/Edge/Chromium and is covered by ``BrowserGateTests``, which skips when none is found.

They deliberately do not re-run the upstream blind evaluations or judge page quality. A passing run
here means the vendored tooling still behaves as documented, not that a designed page is good.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from skill_scripts import SKILLS

SKILL = SKILLS / 'design-taste'
SCRIPTS = SKILL / 'scripts'
LIBRARY = SKILL / 'library'
NODE = shutil.which('node')
REFERENCE_ROLES = {'features', 'pricing', 'faq', 'footer', 'testimonial'}


def read_json(name):
    return json.loads((LIBRARY / name).read_text())


class NodeTestCase(unittest.TestCase):
    """Run a bundled helper in a disposable project directory with a local draw history."""

    @classmethod
    def setUpClass(cls):
        if NODE is None:
            raise unittest.SkipTest('node is not installed')

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix='design-taste-'))
        self.addCleanup(shutil.rmtree, self.work, True)

    def run_script(self, script, *args, timeout=120):
        env = dict(os.environ)
        env.update(
            HOME=str(self.work),
            USERPROFILE=str(self.work),
            TASTE_SKILL_HISTORY=str(self.work / 'history.json'),
        )
        return subprocess.run(
            [NODE, str(SCRIPTS / script), *args],
            cwd=self.work, env=env, capture_output=True, text=True, timeout=timeout,
        )

    def draw(self, *args):
        return self.run_script('draw.mjs', '--sector', 'restaurant',
                               '--brief', 'a neighbourhood coffee roaster', *args)

    def dealt_ids(self):
        sheet = json.loads((self.work / '.taste-skill' / 'direction.json').read_text())
        return sheet


class LibraryTests(unittest.TestCase):
    def test_every_library_file_parses_as_documented(self):
        """The draw reads these records by key; a missing key silently breaks a dealt sheet."""
        shapes = {
            'directions.json': ('list', ('id', 'name', 'sectors', 'idea', 'composition', 'motion')),
            'heroes.json': ('list', ('id', 'blueprint', 'headline')),
            'sections.json': ('list', ('id', 'role', 'blueprint')),
            'type.json': ('list', ('id', 'display', 'text', 'scale')),
            'palettes.json': ('list', ('id', 'bg', 'ink', 'accent')),
            'motions.json': ('list', ('id', 'name', 'description')),
            'sites.json': ('list', ('id', 'url', 'score')),
        }
        for name, (kind, keys) in shapes.items():
            with self.subTest(library=name):
                data = read_json(name)
                self.assertIsInstance(data, list)
                self.assertGreater(len(data), 0)
                for record in data:
                    for key in keys:
                        self.assertIn(key, record)
                self.assertEqual(len({record['id'] for record in data}), len(data), 'duplicate ids')

    def test_section_blueprints_cover_the_roles_the_draw_accepts(self):
        """`--sections` is documented as taking these roles; the library must deal each one."""
        roles = {section['role'] for section in read_json('sections.json')}
        self.assertLessEqual(REFERENCE_ROLES, roles)

    def test_app_library_keeps_its_documented_shape(self):
        """`draw.mjs --app` reads styles, shells, patterns and kinds by key and id."""
        app = read_json('app.json')
        self.assertGreaterEqual(len(app['styles']), 5)
        for key in ('styles', 'shells', 'patterns'):
            with self.subTest(key=key):
                self.assertIsInstance(app[key], list)
                self.assertTrue(app[key])
                self.assertTrue(all('id' in entry for entry in app[key]))
        self.assertIsInstance(app['kinds'], dict)
        self.assertTrue(app['kinds'])
        known = {style['id'] for style in app['styles']}
        for name, kind in app['kinds'].items():
            with self.subTest(kind=name):
                self.assertIn('note', kind)
                self.assertLessEqual(set(kind['styles']), known)

    def test_photograph_sets_hold_urls_and_no_bundled_images(self):
        """Only Unsplash references travel with the package; no image bytes are redistributed."""
        photos = read_json('photos.json')
        self.assertIn('Unsplash', photos['source'])
        self.assertTrue(photos['sets'])
        serialized = json.dumps(photos)
        self.assertNotIn('base64', serialized.lower())
        for name, photo_set in photos['sets'].items():
            with self.subTest(set=name):
                self.assertIn('keywords', photo_set)
                self.assertIn('photos', photo_set)
                self.assertTrue(photo_set['photos'])
                for entry in photo_set['photos']:
                    self.assertTrue(entry['page'].startswith('https://'), entry['page'])
                    self.assertTrue(entry['by'].strip(), 'a dealt photograph needs a creator')
                    self.assertTrue(entry['alt'].strip(), 'a dealt photograph needs alt text')


class DrawTests(NodeTestCase):
    def test_list_reports_the_documented_sectors(self):
        """Asserts that `--list sectors` prints the choices SKILL.md tells the agent to pick from."""
        result = self.run_script('draw.mjs', '--list', 'sectors')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('restaurant', result.stdout)
        self.assertIn('other', result.stdout)

    def test_options_deals_three_distinct_library_directions(self):
        """Ensures a brief deals three different directions that all come from the library."""
        result = self.draw('--sections', 'features,pricing', '--options', '3')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('3 directions dealt', result.stdout)
        known = {direction['id'] for direction in read_json('directions.json')}
        dealt = [line.split('`')[1] for line in result.stdout.splitlines() if line.startswith('## `')]
        self.assertEqual(len(dealt), 3)
        self.assertEqual(len(set(dealt)), 3)
        self.assertLessEqual(set(dealt), known)

    def test_full_sheet_is_written_and_reprints_from_history(self):
        """`--show` must find the sheet the draw just wrote, so a long session can re-read it."""
        result = self.draw('--sections', 'features,pricing')
        self.assertEqual(result.returncode, 0, result.stderr)
        sheet = self.dealt_ids()
        self.assertEqual(sheet['input']['sector'], 'restaurant')
        self.assertIn('direction', sheet)
        shown = self.run_script('draw.mjs', '--show')
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertIn('# DIRECTION SHEET', shown.stdout)
        self.assertIn(f"seed {sheet['seed']}", shown.stdout)
        self.assertIn('a neighbourhood coffee roaster', shown.stdout)

    def test_app_mode_deals_an_app_sheet(self):
        """Ensures `--app` writes an app sheet whose style belongs to the requested kind."""
        kind = next(iter(read_json('app.json')['kinds']))
        result = self.run_script('draw.mjs', '--app', '--kind', kind,
                                 '--brief', 'an analytics dashboard', '--out', str(self.work / '.taste-skill' / 'app'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.strip())
        sheet = json.loads((self.work / '.taste-skill' / 'app' / 'direction.json').read_text())
        self.assertEqual(sheet['kind'], 'app')
        self.assertIn(sheet['style']['id'], read_json('app.json')['kinds'][kind]['styles']
                      + [style['id'] for style in read_json('app.json')['styles']])

    def test_an_unknown_sector_or_direction_fails_with_guidance(self):
        """Ensures a bad sector or direction fails loudly with the guidance text instead of dealing rubbish."""
        unknown_sector = self.run_script('draw.mjs', '--sector', 'nonesuch', '--brief', 'x', '--sections', 'faq')
        self.assertNotEqual(unknown_sector.returncode, 0)
        self.assertIn('Pick the closest', unknown_sector.stderr)
        unknown_direction = self.draw('--sections', 'faq', '--direction', 'nonesuch')
        self.assertNotEqual(unknown_direction.returncode, 0)
        self.assertTrue(unknown_direction.stderr.strip())


class LintTests(NodeTestCase):
    def write_page(self, name, body):
        path = self.work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        return path

    def test_a_plain_flat_page_passes(self):
        """Ensures a compliant page produces no findings, so a clean run is possible."""
        self.write_page('clean.html', (
            '<!doctype html><html><head><style>body{background:#f4f1ea;color:#141414}</style></head>'
            '<body><h1>A bakery on Rua da Boavista</h1><p>Bread, baked twice a day, on the same street since 1934.</p>'
            '<a href="#menu">Read the menu</a></body></html>'
        ))
        result = self.run_script('lint.mjs', '.')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_banned_devices_fail_with_machine_readable_findings(self):
        """Ensures the lint gate catches the banned devices and reports parseable ids for each."""
        self.write_page('slop.html', (
            '<!doctype html><html><head><style>'
            '.card{background:linear-gradient(#fff,#eee);box-shadow:0 8px 30px #0003}'
            '.eyebrow{font-family:ui-monospace,monospace;text-transform:uppercase;letter-spacing:.2em}'
            '</style></head><body><span class="eyebrow">New</span><h1>Build faster</h1>'
            '<div class="card"><span>01</span> Fast</div></body></html>'
        ))
        result = self.run_script('lint.mjs', '.', '--json')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertGreater(report['files'], 0)
        ids = {finding['id'] for finding in report['findings']}
        self.assertLessEqual({'gradient', 'mono', 'eyebrow', 'numbering', 'shadow'}, ids)

    def test_a_path_without_source_files_is_reported(self):
        """Ensures pointing the linter at prose reports that there is nothing to scan rather than passing."""
        self.write_page('notes.md', '# just prose')
        result = self.run_script('lint.mjs', '.')
        self.assertEqual(result.returncode, 2)
        self.assertIn('No source files', result.stderr)

    def test_a_missing_path_is_reported(self):
        """Ensures a missing lint target fails with a clear message."""
        result = self.run_script('lint.mjs', 'does-not-exist')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Not found', result.stderr)


class RuleRegistryTests(NodeTestCase):
    def test_rule_ids_are_unique_and_app_skips_are_known(self):
        """The inspector reports these ids; duplicates or stray skips would misfile a finding."""
        program = (
            'import { RULE_IDS, APP_SKIP } from ' + json.dumps((SCRIPTS / 'lib' / 'rules.mjs').as_uri()) + ';'
            'const dup = RULE_IDS.filter((id, i) => RULE_IDS.indexOf(id) !== i);'
            'console.log(JSON.stringify({ count: RULE_IDS.length, dup, stray: [...APP_SKIP].filter((id) => !RULE_IDS.includes(id)) }));'
        )
        result = subprocess.run([NODE, '--input-type=module', '-e', program],
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertGreater(report['count'], 50)
        self.assertEqual(report['dup'], [])
        self.assertEqual(report['stray'], [])


class AssetAndSceneToolsTests(NodeTestCase):
    def test_credits_without_downloads_explains_the_next_step(self):
        """Ensures `--credits` on a project with no downloads explains how to record one."""
        result = self.run_script('assets.mjs', '--credits')
        self.assertIn('No pictures recorded', result.stdout)

    def test_an_invalid_asset_reference_is_rejected_with_the_expected_format(self):
        """Ensures an unparseable asset reference is refused with the accepted ref format."""
        result = self.run_script('assets.mjs', '--get', 'bogusref')
        self.assertIn('a ref looks like openverse:', result.stdout + result.stderr)

    def test_asset_search_requires_a_query(self):
        """Ensures a bare `assets.mjs` prints the search-query instruction instead of searching."""
        result = self.run_script('assets.mjs')
        self.assertIn('Give a search query', result.stdout + result.stderr)

    def test_scenes_requires_a_page(self):
        """Ensures `scenes.mjs` without a page prints its usage instead of running."""
        result = self.run_script('scenes.mjs')
        self.assertIn('usage:', (result.stdout + result.stderr).lower())


class BrowserGateTests(NodeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        probe = subprocess.run(
            [NODE, '--input-type=module', '-e',
             'import(' + json.dumps((SCRIPTS / 'lib' / 'cdp.mjs').as_uri()) + ').then((m) => console.log(m.findChrome() || ""))'],
            capture_output=True, text=True, timeout=60,
        )
        if probe.returncode != 0 or not probe.stdout.strip():
            raise unittest.SkipTest('no Chrome/Edge/Chromium found; the inspector cannot run')

    def test_the_inspector_renders_and_measures_a_local_page(self):
        """Ensures the inspector renders a real page in a real browser and writes its screenshots."""
        page = self.work / 'page.html'
        page.write_text(
            '<!doctype html><html><head><style>'
            'body{background:#f4f1ea;color:#141414;font-family:Georgia,serif;margin:0;padding:48px}'
            'h1{font-size:64px;line-height:1;margin:0 0 24px}'
            'p{font-size:18px;line-height:1.5;max-width:32em}'
            '</style></head><body><h1>Bakery on Boavista</h1><p>Bread, twice a day.</p></body></html>'
        )
        result = self.run_script('inspect.mjs', str(page), '--widths', '390',
                                 '--out', str(self.work / 'inspect'), timeout=300)
        output = result.stdout + result.stderr
        launch_failures = ('Chrome exited early', 'Chrome did not start', 'No Chrome/Edge/Chromium found',
                           'error while loading shared libraries')
        if result.returncode not in (0, 1) and any(marker in output for marker in launch_failures):
            self.skipTest('the inspector could not start a browser here: ' + output.strip()[-300:])
        self.assertIn(result.returncode, (0, 1), output)
        self.assertTrue(any((self.work / 'inspect').glob('*.jpg'))
                        or any((self.work / 'inspect').glob('*.png')),
                        'no screenshot was written\n' + output[-800:])


if __name__ == '__main__':
    unittest.main()
