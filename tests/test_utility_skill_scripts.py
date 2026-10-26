"""Contract tests for skill creation, GIF easing, seeded art, and browser inspection."""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml
from PIL import Image

from skill_scripts import (
    SKILLS,
    ScriptCase,
    binary,
    module_available,
    require_module,
)

HAVE_NODE = binary("node") is not None




class SkillCreatorTests(ScriptCase):
    def setUp(self):
        super().setUp()
        self.scripts = SKILLS / "skill-creator/scripts"

    def tool(self, name):
        return self.scripts / name

    def make_skill(self, frontmatter, body="# My Skill\n\nDo things.\n", name=None):
        directory = self.work / (name or frontmatter["name"])
        directory.mkdir(parents=True, exist_ok=True)
        rendered = yaml.safe_dump(frontmatter, sort_keys=False)
        (directory / "SKILL.md").write_text(f"---\n{rendered}---\n\n{body}")
        return directory

    def test_quick_validate_accepts_a_well_formed_skill(self):
        """Ensures quick validate accepts a well formed skill."""
        directory = self.make_skill({"name": "my-skill",
                                     "description": "Does a thing."})
        out = self.run_python(self.tool("quick_validate.py"), directory).stdout
        self.assertEqual(out.strip(), "Skill is valid!")

    def test_quick_validate_enforces_the_frontmatter_contract(self):
        """Ensures quick validate enforces the frontmatter contract."""
        cases = {
            "missing SKILL.md": None,
            "no frontmatter": "# Just a heading\n",
            "not a mapping": "---\n- a\n- b\n---\n\nBody\n",
            "missing name": {"description": "no name"},
            "missing description": {"name": "x"},
            "uppercase name": {"name": "My-Skill", "description": "d"},
            "leading hyphen": {"name": "-bad", "description": "d"},
            "double hyphen": {"name": "ba--d", "description": "d"},
            "unknown key": {"name": "ok", "description": "d", "surprise": 1},
        }
        for label, frontmatter in cases.items():
            with self.subTest(case=label):
                if frontmatter is None:
                    target = self.work / "absent"
                    target.mkdir(exist_ok=True)
                elif isinstance(frontmatter, str):
                    target = self.work / f"raw-{abs(hash(label))}"
                    target.mkdir()
                    (target / "SKILL.md").write_text(frontmatter)
                else:
                    target = self.make_skill(frontmatter,
                                             name=frontmatter.get("name", f"case-{abs(hash(label))}"))
                result = self.run_python(self.tool("quick_validate.py"), target,
                                         code=None)
                self.assertNotEqual(result.returncode, 0, f"{label} should fail")
                self.assertNotIn("Skill is valid!", result.stdout)

    def test_quick_validate_reports_a_missing_file_as_an_error_message(self):
        """Ensures quick validate reports a missing file as an error message."""
        out = self.run_python(self.tool("quick_validate.py"), self.work / "absent",
                              code=None)
        self.assertIn("SKILL.md not found", out.stdout + out.stderr)

    def test_quick_validate_enforces_the_name_length_cap(self):
        """Ensures quick validate enforces the name length cap."""
        long_name = "a" * 65
        directory = self.make_skill({"name": long_name, "description": "d"},
                                    name=long_name)
        result = self.run_python(self.tool("quick_validate.py"), directory, code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("64", result.stdout + result.stderr)

    def test_every_published_skill_passes_the_validator(self):
        """All published entrypoints must meet the repository metadata contract."""
        entrypoints = sorted(SKILLS.glob("*/SKILL.md"))
        self.assertTrue(entrypoints)
        for entrypoint in entrypoints:
            with self.subTest(skill=entrypoint.parent.name):
                self.run_python(self.tool("quick_validate.py"), entrypoint.parent)

    def test_init_skill_scaffolds_the_documented_layout(self):
        """Ensures init skill scaffolds the documented layout."""
        result = self.run_python(self.tool("init_skill.py"), "My New Skill", "--path",
                                 self.work, "--resources", "scripts,references",
                                 "--examples")
        root = self.work / "my-new-skill"
        self.assertTrue((root / "SKILL.md").is_file())
        self.assertTrue((root / "scripts/example.py").is_file())
        self.assertTrue((root / "references/api_reference.md").is_file())
        self.assertIn("Run the validator", result.stdout)
        # A scaffold is intentionally unfinished and must fail validation.
        result = self.run_python(self.tool("quick_validate.py"), root, code=1)
        self.assertIn("TODO", result.stdout)

        frontmatter = yaml.safe_load(
            (root / "SKILL.md").read_text().split("---")[1])
        self.assertEqual(frontmatter["name"], "my-new-skill")

    def test_init_skill_rejects_unknown_resource_directories(self):
        """Ensures init skill rejects unknown resource directories."""
        result = self.run_python(self.tool("init_skill.py"), "x", "--path", self.work,
                                 "--resources", "scripts,bogus", code=1)
        self.assertIn("assets, references, scripts", result.stdout + result.stderr)

    def test_init_skill_normalizes_the_directory_name(self):
        """Ensures init skill normalizes the directory name."""
        for raw, expected in (("  Weird   NAME  ", "weird-name"),
                              ("with_underscores", "with-underscores"),
                              ("MiXeD CaSe", "mixed-case")):
            with self.subTest(raw=raw):
                self.run_python(self.tool("init_skill.py"), raw, "--path", self.work)
                self.assertTrue((self.work / expected / "SKILL.md").is_file(),
                                sorted(p.name for p in self.work.iterdir()))















class CatalogTests(unittest.TestCase):
    """The catalog is the install entry point: it must list every skill and its links must resolve."""

    def test_the_catalog_lists_every_published_skill(self):
        """Ensures every published skill is linked from the catalog, and no catalog row is dangling."""
        catalog = (SKILLS / "README.md").read_text()
        listed = set(re.findall(r"\]\((\w[\w-]*)/SKILL\.md\)", catalog))
        published = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
        self.assertEqual(listed - published, set(), "catalog links a skill that does not exist")
        self.assertEqual(published - listed, set(), "skill missing from the catalog")

    def test_bundled_markdown_links_stay_inside_their_skill(self):
        """A copied skill resolves its own documentation; the pinned Lemo tree is exempt."""
        pinned = SKILLS / "create-motion-videos/assets/lemo"
        broken = []
        for entrypoint in sorted(SKILLS.glob("*/SKILL.md")):
            root = entrypoint.parent.resolve()
            for document in root.rglob("*.md"):
                if document.is_relative_to(pinned.resolve()) or "node_modules" in document.parts:
                    continue
                for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", document.read_text(errors="replace")):
                    url = urlsplit(target)
                    if url.scheme or url.netloc or not url.path:
                        continue
                    resolved = (document.parent / unquote(url.path)).resolve()
                    if not resolved.is_relative_to(root) or not resolved.exists():
                        broken.append(f"{document.relative_to(SKILLS)}: {target}")
        self.assertEqual(broken, [], "bundled link does not resolve inside its skill")

    def test_each_vendored_skill_records_its_source_and_notice(self):
        """A redistributed upstream skill keeps its licence text and pinned source record."""
        for name in ("design-taste", "security-audit"):
            package = SKILLS / name
            with self.subTest(skill=name):
                self.assertTrue((package / "LICENSE.txt").is_file())
                self.assertIn("MIT", (package / "LICENSE.txt").read_text())
                sources = (package / "SOURCES.md").read_text()
                self.assertRegex(sources, r"[0-9a-f]{40}")
                self.assertIn("https://github.com/", sources)


@require_module("PIL")
class GifEasingTests(ScriptCase):
    """``gif-creator/core/easing.py`` — the timing API SKILL.md points at."""

    def run_easing(self, body):
        return self.import_snippet(
            textwrap.dedent(body),
            path_entries=[SKILLS / "gif-creator"],
        ).stdout

    def test_the_registry_exposes_the_documented_curve_names(self):
        """Ensures the registry exposes the documented curve names."""
        out = self.run_easing(
            """
            import json
            from core import easing
            print(json.dumps(sorted(easing.EASING_FUNCTIONS)))
            """
        )
        names = json.loads(out.strip())
        for expected in ("linear", "ease_in", "ease_out", "ease_in_out", "bounce",
                         "bounce_in", "bounce_out", "elastic", "elastic_in",
                         "elastic_out", "back_in", "back_out", "back_in_out"):
            self.assertIn(expected, names)
        # The two documented aliases point at the back curves.
        self.assertIn("anticipate", names)
        self.assertIn("overshoot", names)

    def test_every_curve_maps_the_unit_interval_onto_itself(self):
        """Ensures every curve maps the unit interval onto itself."""
        out = self.run_easing(
            """
            from core import easing
            bad = []
            for name, fn in sorted(easing.EASING_FUNCTIONS.items()):
                if round(fn(0.0), 9) != 0.0 or round(fn(1.0), 9) != 1.0:
                    bad.append((name, fn(0.0), fn(1.0)))
                for step in range(101):
                    value = fn(step / 100)
                    if not isinstance(value, float):
                        bad.append((name, "not a float", value))
            print(bad)
            """
        )
        self.assertEqual(out.strip(), "[]")

    def test_aliases_resolve_to_the_same_curve(self):
        """Ensures aliases resolve to the same curve."""
        out = self.run_easing(
            """
            from core import easing
            print(easing.EASING_FUNCTIONS["anticipate"]
                  is easing.EASING_FUNCTIONS["back_in"])
            print(easing.EASING_FUNCTIONS["overshoot"]
                  is easing.EASING_FUNCTIONS["back_out"])
            print(easing.get_easing("linear") is easing.linear)
            print(easing.get_easing("not-a-curve") is easing.linear)
            """
        )
        self.assertEqual(out.split(), ["True", "True", "True", "True"])

    def test_interpolate_applies_the_named_curve_between_two_values(self):
        """Ensures interpolate applies the named curve between two values."""
        out = self.run_easing(
            """
            from core import easing
            print(easing.interpolate(0, 10, 0.0), easing.interpolate(0, 10, 1.0))
            print(easing.interpolate(0, 10, 0.5, "linear"))
            print(round(easing.interpolate(100, 0, 0.25, "linear"), 6))
            print(easing.interpolate(0, 10, 0.5, "unknown-curve")
                  == easing.interpolate(0, 10, 0.5, "linear"))
            """
        )
        lines = out.split()
        self.assertEqual(lines[0], "0.0", "t=0 returns the start value")
        self.assertEqual(lines[1], "10.0", "t=1 returns the end value")
        self.assertEqual(lines[2], "5.0")
        self.assertEqual(lines[3], "75.0", "interpolation works in both directions")
        self.assertEqual(lines[4], "True", "an unknown curve falls back to linear")

    def test_squash_and_stretch_applies_the_documented_scale_factors(self):
        """Ensures squash and stretch applies the documented scale factors."""
        out = self.run_easing(
            """
            from core import easing
            print(easing.apply_squash_stretch((1.0, 1.0), 0.5))
            print(easing.apply_squash_stretch((1.0, 1.0), 0.0))
            print(easing.apply_squash_stretch((1.0, 1.0), 1.0))
            print(easing.apply_squash_stretch((2.0, 3.0), 1.0, "both"))
            print(easing.apply_squash_stretch((1.0, 1.0), 0.5, "horizontal"))
            print(easing.apply_squash_stretch((1.0, 1.0), 0.5, "unknown"))
            for intensity in (0.0, 0.25, 0.5, 1.0):
                w, h = easing.apply_squash_stretch((1.0, 1.0), intensity)
                print("product", round(w * h, 6), round(1 - intensity ** 2 / 4, 6))
            """
        )
        lines = out.splitlines()
        self.assertEqual(lines[0], "(1.25, 0.75)", "vertical widens and flattens")
        self.assertEqual(lines[1], "(1.0, 1.0)", "zero intensity is the identity")
        self.assertEqual(lines[2], "(1.5, 0.5)", "full intensity is the maximum")
        self.assertEqual(lines[3], "(1.4, 2.0999999999999996)",
                         "'both' shrinks by 0.3 * intensity on each axis")
        self.assertEqual(lines[4], "(0.75, 1.25)", "horizontal is the mirror image")
        self.assertEqual(lines[5], "(1.0, 1.0)", "an unknown direction is a no-op")
        for line in lines[6:]:
            _, product, expected = line.split()
            self.assertEqual(product, expected,
                             "vertical/horizontal preserve volume to second order")

    def test_arc_motion_peaks_midway_and_pins_the_endpoints(self):
        """Ensures arc motion peaks midway and pins the endpoints."""
        out = self.run_easing(
            """
            from core import easing
            print(easing.calculate_arc_motion((0, 0), (10, 0), 5, 0.0))
            print(easing.calculate_arc_motion((0, 0), (10, 0), 5, 1.0))
            print(easing.calculate_arc_motion((0, 0), (10, 0), 5, 0.5))
            print(easing.calculate_arc_motion((0, 0), (10, 0), 0, 0.5))
            """
        )
        lines = out.splitlines()
        self.assertEqual(lines[0], "(0.0, 0.0)")
        self.assertEqual(lines[1], "(10.0, 0.0)")
        self.assertEqual(lines[2], "(5.0, -5.0)", "the apex is the full arc height")
        self.assertEqual(lines[3], "(5.0, 0.0)", "zero height is a straight line")


@unittest.skipUnless(HAVE_NODE, "requires node")
class AlgorithmicArtTemplateTests(ScriptCase):
    """The seeded generator template the skill hands to the model."""

    def setUp(self):
        super().setUp()
        self.template = SKILLS / "algorithmic-art/assets/generator_template.js"

    def load(self, extra=""):
        """Load the template in a bare VM sandbox and expose it as ``Art``.

        The template attaches itself to ``globalThis``, which inside
        ``runInNewContext`` is the sandbox itself; ``extra`` therefore runs in
        the outer Node context and reaches it through ``Art``.
        """
        return (
            "const fs = require('fs');\n"
            "const vm = require('vm');\n"
            "const sandbox = {Math, JSON, Object, Array, Number, String, Boolean,\n"
            "                 Error, isNaN, parseInt, parseFloat, console};\n"
            "vm.createContext(sandbox);\n"
            f"vm.runInContext(fs.readFileSync({str(self.template)!r}, 'utf8'), sandbox);\n"
            "const Art = sandbox.SeededArt;\n" + extra
        )

    def make_canvas(self, size=100):
        """A recording 2D-context stub, injected from the outer context."""
        return (
            "const ops = [];\n"
            f"const canvas = {{width: {size}, height: {size}, getContext: () => ({{\n"
            "  set fillStyle(v) { ops.push('fill:' + v); },\n"
            "  fillRect: (...a) => ops.push('rect:' + a.join(',')),\n"
            "  beginPath: () => ops.push('begin'),\n"
            "  arc: (...a) => ops.push('arc:' + a.join(',')),\n"
            "  fill: () => ops.push('fillPath')})};\n"
        )

    def test_the_template_exposes_a_seeded_art_namespace(self):
        """Ensures the template exposes a seeded art namespace."""
        _, value = self.run_node_json(self.load(
            "emit({keys: Object.keys(Art),\n"
            "      randomType: typeof Art.random,\n"
            "      drawType: typeof Art.drawArt});"))
        self.assertEqual(value["keys"], ["random", "drawArt"])
        self.assertEqual(value["randomType"], "function")
        self.assertEqual(value["drawType"], "function")

    def test_the_seeded_rng_is_deterministic_and_uniform(self):
        """Ensures the seeded rng is deterministic and uniform."""
        _, value = self.run_node_json(self.load(
            "const rng = Art.random(42);\n"
            "const first = [rng(), rng(), rng()];\n"
            "const again = (() => { const r = Art.random(42);\n"
            "  return [r(), r(), r()]; })();\n"
            "const other = (() => { const r = Art.random(43);\n"
            "  return [r(), r(), r()]; })();\n"
            "const many = (() => { const r = Art.random(7);\n"
            "  return Array.from({length: 2000}, () => r()); })();\n"
            "emit({first, repeatable: JSON.stringify(first) === JSON.stringify(again),\n"
            "      differs: JSON.stringify(first) !== JSON.stringify(other),\n"
            "      min: Math.min(...many), max: Math.max(...many)});"))
        self.assertTrue(value["repeatable"], "the same seed must repeat")
        self.assertTrue(value["differs"], "a different seed must diverge")
        self.assertGreaterEqual(value["min"], 0)
        self.assertLess(value["max"], 1)
        self.assertLess(value["min"], 0.05, "2000 draws must reach the low end")
        self.assertGreater(value["max"], 0.95, "2000 draws must reach the high end")

    def test_draw_art_validates_its_seed_and_count(self):
        """Ensures draw art validates its seed and count."""
        _, value = self.run_node_json(self.load(
            self.make_canvas()
            + "const err = (opts) => {\n"
            "  try { Art.drawArt(canvas, opts); return null; }\n"
            "  catch (e) { return e.message; }\n"
            "};\n"
            "Art.drawArt(canvas, {seed: 1, count: 3});\n"
            "emit({opKinds: [...new Set(ops.map((o) => o.split(':')[0]))],\n"
            "      arcs: ops.filter((o) => o.startsWith('arc:')).length,\n"
            "      badSeed: err({seed: 1.5, count: 3}),\n"
            "      zeroCount: err({seed: 1, count: 0}),\n"
            "      tooMany: err({seed: 1, count: 2001}),\n"
            "      defaultsOk: err(undefined)});"))
        self.assertEqual(value["arcs"], 3)
        self.assertIn("rect", value["opKinds"])
        self.assertIn("arc", value["opKinds"])
        self.assertIn("fill", value["opKinds"])
        self.assertEqual(value["badSeed"],
                         "Use an integer seed and count from 1 to 2000")
        self.assertEqual(value["zeroCount"], value["badSeed"])
        self.assertEqual(value["tooMany"], value["badSeed"])
        self.assertIsNone(value["defaultsOk"])

    def test_draw_art_is_reproducible_for_a_fixed_seed(self):
        """Ensures draw art is reproducible for a fixed seed."""
        source = self.load(
            self.make_canvas(50)
            + "const record = (seed, count) => {\n"
            "  ops.length = 0;\n"
            "  Art.drawArt(canvas, {seed, count});\n"
            "  return ops.join('|');\n"
            "};\n"
            "const same = record(5, 20) === record(5, 20);\n"
            "const first = record(5, 20);\n"
            "const second = record(6, 20);\n"
            "emit({same, differs: first !== second, draws: first.length > 0});")
        _, value = self.run_node_json(source)
        self.assertTrue(value["same"], "the same seed must draw the same art")
        self.assertTrue(value["differs"], "a different seed must draw different art")
        self.assertTrue(value["draws"])




class WebappTestingInspectTests(ScriptCase):
    def setUp(self):
        super().setUp()
        self.script = SKILLS / "webapp-testing/scripts/inspect_page.py"

    def test_help_pins_the_documented_options(self):
        """Ensures help pins the documented options."""
        out = self.run_python(self.script, "--help").stdout
        self.assertAllInText(
            ["--ready", "--width", "--height", "target", "output",
             "No hard-coded page controls", "network-idle waits"],
            out,
        )

    def test_it_reports_the_playwright_dependency_when_absent(self):
        """Ensures it reports the playwright dependency when absent."""
        if module_available("playwright"):
            self.skipTest("playwright is installed; the failure path is unreachable")
        page = self.write("page.html", "<html><body><h1>Hi</h1></body></html>")
        result = self.run_python(self.script, page, self.work / "out.json", code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("playwright", result.stdout + result.stderr)
        self.assertFalse((self.work / "out.json").exists())

    @require_module("playwright")
    def test_it_captures_a_screenshot_and_console_log(self):
        """Ensures it captures a screenshot and console log."""
        page = self.write("page.html",
                          "<html><body><h1>Hi</h1>"
                          "<script>console.log('from page')</script></body></html>")
        out = self.work / "report"
        self.run_python(self.script, page, out, timeout=300)
        self.assertTrue(out.is_dir())
        self.assertTrue(list(out.glob("*.png")))
        self.assertTrue(list(out.glob("*.json")))


if __name__ == "__main__":
    unittest.main()
