"""Contract tests for the ``vector-art`` skill's SVG Style Studio tooling.

The skill is a registry-driven pipeline: ``route_style.py`` maps a prompt to
styles, ``new_style.py`` extends the registry, ``convert_svg.py`` /
``optimize_svg.py`` / ``pixel_grid.py`` / ``text_to_path.py`` produce art, and
``validate_svg.py`` is the QC gate that checks a file against its style's
declared constraints.  ``svgtools.py`` is the shared library underneath.

Nothing here needs a browser: the registry-writing tools are exercised against
a *copy* of the skill so the checkout is never modified, and ``render_svg.py``
is checked through its CLI contract and its missing-Playwright failure path.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_scripts import (
    SKILLS,
    ScriptCase,
    binary,
    module_available,
    require_module,
)

VECTOR_ART = SKILLS / "vector-art"
SCRIPTS = VECTOR_ART / "scripts"
HAVE_NODE = binary("node") is not None

SAMPLE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"
     width="100" height="100">
  <title>Sample</title>
  <rect x="10.123456" y="10" width="30" height="30" fill="#ff0000"/>
  <circle cx="60" cy="60" r="20" fill="#00ff00" stroke="#0000ff"
          stroke-width="2"/>
  <g id="layer-one"><path d="M5 5 L20 5 L20 20 Z" fill="#101010"/></g>
</svg>
"""


@require_module("lxml")
class SvgToolsLibraryTests(ScriptCase):
    """``svgtools.py`` — the parsing helpers every other tool imports."""

    def run_tools(self, body):
        return self.import_snippet(
            textwrap.dedent(body), path_entries=[SCRIPTS]
        ).stdout

    def test_geometry_helpers_resolve_viewbox_and_numeric_tokens(self):
        """Ensures geometry helpers resolve viewbox and numeric tokens."""
        svg = self.write("a.svg", SAMPLE_SVG)
        ns = "{http://www.w3.org/2000/svg}"
        out = self.run_tools(
            f"""
            import json
            import svgtools as t
            root, error = t.parse_svg({str(svg)!r})
            assert error is None, error
            print(json.dumps(t.parse_viewbox(root)))
            print(t.fnum("12.5"), t.fnum("12.5px"), t.fnum("nope", 3.0),
                  t.fnum(None, -1.0))
            print(json.dumps(t.NUM_RE.findall("M10.5 -20 L3e2 4")))
            print(json.dumps([t.local({ns + "rect"!r}), t.local("rect"),
                                t.local(None), t.local(42)]))
            print(json.dumps(sorted(t.SHAPE_TAGS)))
            print(json.dumps(sorted(t.GRAPHIC_TAGS - t.SHAPE_TAGS)))
            """
        )
        lines = out.splitlines()
        self.assertEqual(json.loads(lines[0]), [0.0, 0.0, 100.0, 100.0])
        self.assertEqual(lines[1].split(), ["12.5", "12.5", "3.0", "-1.0"])
        self.assertEqual(json.loads(lines[2]), ["10.5", "-20", "3e2", "4"])
        self.assertEqual(json.loads(lines[3]), ["rect", "rect", "", ""])
        self.assertEqual(json.loads(lines[4]),
                         ["circle", "ellipse", "line", "path", "polygon", "polyline",
                          "rect"])
        self.assertEqual(json.loads(lines[5]), ["image", "text", "use"])

    def test_a_missing_viewbox_is_reported_as_none(self):
        """Ensures a missing viewbox is reported as none."""
        svg = self.write(
            "noviewbox.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"/>',
        )
        out = self.run_tools(
            f"""
            import svgtools as t
            root, error = t.parse_svg({str(svg)!r})
            assert error is None, error
            print(t.parse_viewbox(root))
            root, error = t.parse_svg("<svg><unclosed>")
            print(root is None, error is not None)
            """
        )
        self.assertEqual(out.splitlines()[0], "None")
        self.assertEqual(out.splitlines()[1], "True True")

    def test_element_iteration_and_id_index(self):
        """Ensures element iteration and id index."""
        svg = self.write("a.svg", SAMPLE_SVG)
        out = self.run_tools(
            f"""
            import json
            import svgtools as t
            root, error = t.parse_svg({str(svg)!r})
            assert error is None, error
            print(json.dumps([t.local(e.tag) for e in t.iter_elements(root)]))
            print(json.dumps(sorted(t.ids_map(root))))
            print(json.dumps([t.local(e.tag)
                              for e in t.iter_elements(root)
                              if t.local(e.tag) in t.GRAPHIC_TAGS]))
            """
        )
        lines = out.splitlines()
        # iter_elements includes the root <svg> itself.
        self.assertEqual(json.loads(lines[0]),
                         ["svg", "title", "rect", "circle", "g", "path"])
        self.assertEqual(json.loads(lines[1]), ["layer-one"])
        self.assertEqual(json.loads(lines[2]), ["rect", "circle", "path"])

    def test_path_parsing_reports_commands_and_rejects_garbage(self):
        """Ensures path parsing reports commands and rejects garbage."""
        out = self.run_tools(
            """
            import json
            import svgtools as t
            segments, commands = t.parse_path("M0 0 L10 10 Z")
            print(json.dumps(commands))
            print(json.dumps([[c, pts] for c, pts in segments]))
            print(json.dumps(t.path_bbox("M0 0 L10 20 Z")))
            print(json.dumps(t.path_bbox("M5 5 h10 v10 h-10 z")))
            for bad in ("M", "M0 0 Q1", "@@@"):
                try:
                    t.parse_path(bad)
                except t.PathParseError:
                    print("PathParseError")
                else:
                    print("ACCEPTED", repr(bad))
            """
        )
        lines = out.splitlines()
        self.assertEqual(json.loads(lines[0]), ["M", "L", "Z"])
        self.assertEqual(json.loads(lines[1]),
                         [["M", [[0.0, 0.0]]], ["L", [[10.0, 10.0]]],
                          ["Z", [[0.0, 0.0]]]])
        self.assertEqual(json.loads(lines[2]), [0.0, 0.0, 10.0, 20.0])
        self.assertEqual(json.loads(lines[3]), [5.0, 5.0, 15.0, 15.0])
        self.assertEqual(lines[4:], ["PathParseError"] * 3)
        self.assertNotIn("ACCEPTED", out)

    def test_transform_parsing_composes_matrices(self):
        """Ensures transform parsing composes matrices."""
        out = self.run_tools(
            """
            import json
            import svgtools as t
            print(json.dumps(t.parse_transform("")))
            print(json.dumps(t.parse_transform("translate(10, 20)")))
            print(json.dumps(t.mat_apply(t.parse_transform("translate(10, 20)"), 1, 1)))
            print(json.dumps(t.mat_mul(t.IDENTITY, t.IDENTITY)))
            print(json.dumps(t.mat_apply(t.parse_transform("scale(2)"), 3, 4)))
            print(json.dumps(t.mat_apply(
                t.parse_transform("translate(1, 1) scale(2)"), 3, 4)))
            """
        )
        lines = out.splitlines()
        self.assertEqual(json.loads(lines[0]), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEqual(json.loads(lines[1])[-2:], [10.0, 20.0])
        self.assertEqual(json.loads(lines[2]), [11.0, 21.0])
        self.assertEqual(json.loads(lines[3]), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEqual(json.loads(lines[4]), [6.0, 8.0])
        self.assertEqual(json.loads(lines[5]), [7.0, 9.0],
                         "nested transforms compose left to right")

    def test_css_and_style_attribute_collection(self):
        """Ensures css and style attribute collection."""
        svg = self.write(
            "styled.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
            "<style>.red { fill: #ff0000; stroke: none }</style>"
            '<rect x="0" y="0" width="5" height="5" style="fill:#00ff00"/></svg>',
        )
        out = self.run_tools(
            f"""
            import json
            import svgtools as t
            root, error = t.parse_svg({str(svg)!r})
            assert error is None, error
            css = t.collect_css(root)
            print(json.dumps(sorted(css)))
            print(json.dumps(css["class"]))
            print(json.dumps(css["id"]))
            print(json.dumps(css["tag"]))
            print(json.dumps(t.parse_style_attr("fill:#00ff00;stroke-width:2")))
            print(json.dumps(t.parse_style_attr("")))
            print(json.dumps(t.inherit_text_attrs(root)) if hasattr(t, "inherit_text_attrs") else "n/a")
            """
        )
        lines = out.splitlines()
        # collect_css buckets simple selectors by kind; combinators are out of scope.
        self.assertEqual(json.loads(lines[0]), ["class", "id", "tag"])
        self.assertEqual(json.loads(lines[1]),
                         {"red": {"fill": "#ff0000", "stroke": "none"}})
        self.assertEqual(json.loads(lines[2]), {}, "no #id selectors in the sample")
        self.assertEqual(json.loads(lines[3]), {}, "no bare tag selectors either")
        self.assertEqual(json.loads(lines[4]), {"fill": "#00ff00",
                                                "stroke-width": "2"})
        self.assertEqual(json.loads(lines[5]), {})

    def test_href_resolution_accepts_both_namespaces(self):
        """Ensures href resolution accepts both namespaces."""
        svg = self.write(
            "uses.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 10 10">'
            '<defs><rect id="r" width="4" height="4"/></defs>'
            '<use xlink:href="#r"/><use href="#r"/></svg>',
        )
        out = self.run_tools(
            f"""
            import svgtools as t
            root, error = t.parse_svg({str(svg)!r})
            assert error is None, error
            print([t.get_href(e) for e in t.iter_elements(root)
                   if t.local(e.tag) == "use"])
            """
        )
        self.assertEqual(out.strip(), "['#r', '#r']")


@require_module("lxml")
class ValidateSvgTests(ScriptCase):
    def validate(self, *args, code=0):
        return self.run_python(SCRIPTS / "validate_svg.py", *args, code=code)

    def test_a_titled_file_passes_and_reports_its_statistics(self):
        """Ensures a titled file passes and reports its statistics."""
        svg = self.write("clean.svg", SAMPLE_SVG)
        result = self.validate(svg)
        self.assertIn("(0 errors, 0 warnings)", result.stdout)
        self.assertTrue(result.stdout.startswith("OK"), result.stdout)
        self.assertAllIn(
            ["stats: viewBox=[0.0, 0.0, 100.0, 100.0]", "painted=3", "groups=1",
             "named_groups=1", "distinct_colors=4", "distinct_stroke_widths=1",
             "content_fill_pct=", "weight_offset_pct="],
            result.stdout,
        )
        # The fixed width/height are advisory INFO notes, not warnings.
        self.assertIn("INFO  fixed-size", result.stdout)
        self.assertIn("is fixed-size; drop it or use 100%", result.stdout)

    def test_a_missing_title_is_a_warning_not_an_error(self):
        """Ensures a missing title is a warning not an error."""
        svg = self.write("untitled.svg", SAMPLE_SVG.replace("  <title>Sample</title>\n", ""))
        result = self.validate(svg)
        self.assertIn("(0 errors, 1 warnings)", result.stdout)
        self.assertTrue(result.stdout.startswith("WARN"), result.stdout)
        self.assertIn("no <title>; add one for accessibility", result.stdout)

    def test_missing_viewbox_is_an_error_and_strict_makes_warnings_fatal(self):
        """Ensures missing viewbox is an error and strict makes warnings fatal."""
        svg = self.write(
            "noviewbox.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
            '<rect x="0" y="0" width="10" height="10" fill="#000"/></svg>',
        )
        result = self.validate(svg, code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("viewBox", result.stdout + result.stderr)

        warn_only = self.write(
            "warn.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<rect x="10" y="10" width="80" height="80" fill="#123456"/></svg>',
        )
        self.validate(warn_only, code=0)
        self.validate(warn_only, "--strict", code=None)

    def test_json_mode_is_machine_readable_and_matches_the_text_report(self):
        """Ensures json mode is machine readable and matches the text report."""
        svg = self.write("clean.svg", SAMPLE_SVG)
        payload = json.loads(self.validate(svg, "--json").stdout)
        self.assertIsInstance(payload, list)
        entry = payload[0]
        self.assertEqual(entry["file"], str(svg))
        self.assertTrue(entry["ok"])
        stats = entry["stats"]
        for key in ("bytes", "elements", "viewBox", "painted", "off_canvas",
                    "content_margins_pct", "content_fill_pct", "weight_offset_pct",
                    "groups", "named_groups", "gradients", "filters",
                    "distinct_colors"):
            self.assertIn(key, stats, f"missing stats key {key}")
        self.assertEqual(sorted(entry), ["file", "findings", "ok", "stats"])
        self.assertEqual(stats["viewBox"], [0.0, 0.0, 100.0, 100.0])
        self.assertEqual(stats["elements"], 6, "the root <svg> is counted too")
        self.assertEqual(stats["painted"], 3)
        self.assertEqual(stats["named_groups"], 1)
        self.assertIn("findings", entry)

    def test_style_checks_report_every_rule_the_file_breaks(self):
        """Style conformance is advisory: reported as warnings, exit stays 0."""
        soft = self.write(
            "soft.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
            'width="100" height="100"><title>Soft</title>'
            '<circle cx="50.5" cy="50" r="40" fill="#123456" stroke="#000" '
            'stroke-width="1"/></svg>',
        )
        result = self.validate(soft, "--style", "pixel-art")
        self.assertIn("(0 errors, 3 warnings)", result.stdout)
        self.assertAllIn(
            ["style:pixel-art:forbid-circle", "<circle> used 1 times",
             "style:pixel-art:shape-rendering", 'set shape-rendering="crispEdges"',
             "(0/1 elements have it)",
             "style:pixel-art:stroke", "this style is fill-only"],
            result.stdout,
        )

    def test_style_checks_flag_off_grid_coordinates(self):
        """Ensures style checks flag off grid coordinates."""
        offgrid = self.write(
            "offgrid.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
            'shape-rendering="crispEdges"><title>Off grid</title>'
            '<rect x="10.5" y="10" width="40" height="40" fill="#123456"/></svg>',
        )
        result = self.validate(offgrid, "--style", "pixel-art")
        self.assertIn("style:pixel-art:grid", result.stdout)
        self.assertIn("non-integer coordinates; snap to the grid", result.stdout)

        snapped = self.write(
            "snapped.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
            'shape-rendering="crispEdges"><title>Snapped</title>'
            '<rect x="10" y="10" width="40" height="40" fill="#123456"/></svg>',
        )
        self.assertNotIn("style:pixel-art:grid",
                         self.validate(snapped, "--style", "pixel-art").stdout)

        # The same file satisfies its own style, so no style warnings remain.
        crisp = self.write(
            "crisp.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8" '
            'shape-rendering="crispEdges"><title>Crisp</title>'
            '<rect x="1" y="1" width="4" height="4" fill="#123456"/></svg>',
        )
        result = self.validate(crisp, "--style", "pixel-art")
        self.assertNotIn("style:pixel-art", result.stdout)

    def test_an_unknown_style_is_reported_as_a_skipped_check(self):
        """Ensures an unknown style is reported as a skipped check."""
        svg = self.write("clean.svg", SAMPLE_SVG)
        result = self.validate(svg, "--style", "no-such-style")
        self.assertIn("WARN  unknown-style", result.stdout)
        self.assertIn("style 'no-such-style' not found in registry; "
                      "conformance checks skipped", result.stdout)

    def test_several_files_are_all_reported(self):
        """Ensures several files are all reported."""
        first = self.write("one.svg", SAMPLE_SVG)
        second = self.write("two.svg", SAMPLE_SVG.replace("Sample", "Other"))
        payload = json.loads(self.validate(first, second, "--json").stdout)
        self.assertEqual([Path(e["file"]).name for e in payload], ["one.svg", "two.svg"])

    def test_quiet_mode_drops_the_advisory_notes_but_keeps_warnings(self):
        """Ensures quiet mode drops the advisory notes but keeps warnings."""
        svg = self.write("untitled.svg",
                         SAMPLE_SVG.replace("  <title>Sample</title>\n", ""))
        loud = self.validate(svg).stdout
        quiet = self.validate(svg, "--quiet").stdout
        self.assertIn("INFO  fixed-size", loud)
        self.assertNotIn("INFO", quiet, "--quiet suppresses the advisory notes")
        self.assertIn("no <title>", quiet, "warnings still print")
        self.assertIn("stats:", quiet, "the statistics line always prints")
        self.assertLess(len(quiet), len(loud))

    def test_json_findings_carry_a_level_code_message_and_location(self):
        """Ensures json findings carry a level code message and location."""
        svg = self.write("untitled.svg",
                         SAMPLE_SVG.replace("  <title>Sample</title>\n", ""))
        entry = json.loads(self.validate(svg, "--json").stdout)[0]
        self.assertTrue(entry["ok"], "warnings alone do not make a file invalid")
        codes = [finding["code"] for finding in entry["findings"]]
        self.assertIn("title", codes)
        self.assertIn("fixed-size", codes)
        for finding in entry["findings"]:
            self.assertEqual(sorted(finding), ["code", "level", "message", "where"])
            self.assertIn(finding["level"], ("error", "warn", "info"))


@require_module("lxml")
class RouteStyleTests(ScriptCase):
    def route(self, *args, code=0):
        return self.run_python(SCRIPTS / "route_style.py", *args, code=code)

    def test_list_shows_the_registry_with_aliases(self):
        """Ensures list shows the registry with aliases."""
        out = self.route("--list").stdout
        self.assertIn("ukiyo-e", out)
        self.assertIn("minimal-modern", out)
        self.assertIn("Minimal / Modern", out)

    def test_a_named_style_resolves_to_a_single_mode_plan(self):
        """Ensures a named style resolves to a single mode plan."""
        payload = json.loads(self.route("Create a fox in ukiyo-e style",
                                        "--json").stdout)
        self.assertEqual(payload["mode"], "single")
        self.assertEqual(payload["styles"][0]["id"], "ukiyo-e")
        self.assertEqual(payload["styles"][0]["role"], "primary")
        self.assertEqual(payload["subject_hint"], "fox")
        self.assertEqual(payload["file_names"], ["fox-ukiyo-e.svg"])
        self.assertIn("validate_svg.py", payload["validate_cmd"])
        self.assertIn("--style ukiyo-e", payload["validate_cmd"])
        self.assertFalse(payload["ambiguous"])

    def test_an_aesthetic_phrase_without_a_style_asks_for_confirmation(self):
        """Ensures an aesthetic phrase without a style asks for confirmation."""
        payload = json.loads(self.route("make it feel nostalgic and warm",
                                        "--json").stdout)
        self.assertTrue(payload["needs_style"] or payload["confirm_style"]
                        or payload["aesthetic_phrase"], payload)

    def test_a_blend_request_produces_a_blend_plan(self):
        """Ensures a blend request produces a blend plan."""
        payload = json.loads(self.route("a cat in ukiyo-e blended with manga",
                                        "--json").stdout)
        ids = [style["id"] for style in payload["styles"]]
        self.assertIn("ukiyo-e", ids)
        self.assertTrue(payload["blend_plan"] or len(ids) > 1, payload)

    def test_the_menu_lists_candidates_for_an_ambiguous_prompt(self):
        """Ensures the menu lists candidates for an ambiguous prompt."""
        out = self.route("something stylish", "--menu").stdout
        self.assertTrue(out.strip())

    def test_show_and_compat_report_registry_metadata(self):
        """Ensures show and compat report registry metadata."""
        shown = self.route("--show", "ukiyo-e").stdout
        self.assertIn("ukiyo-e", shown)
        compat = self.route("--compat", "ukiyo-e", "manga").stdout
        self.assertAllIn(["PRIMARY Ukiyo-e owns STRUCTURE", "SECONDARY Manga",
                          "known-good pairing", "contributes SURFACE + MOOD only",
                          "Sanity test:"], compat)

    def test_lint_validates_the_whole_registry(self):
        """Ensures lint validates the whole registry."""
        result = self.route("--lint")
        self.assertTrue(result.stdout.strip())
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_the_brief_is_suppressed_on_request(self):
        """Ensures the brief is suppressed on request."""
        full = self.route("a fox in ukiyo-e style").stdout
        bare = self.route("a fox in ukiyo-e style", "--no-brief").stdout
        self.assertGreater(len(full), len(bare))


@require_module("lxml")
class ConvertSvgTests(ScriptCase):
    def convert(self, *args, code=0):
        return self.run_python(SCRIPTS / "convert_svg.py", *args, code=code)

    def setUp(self):
        super().setUp()
        self.svg = self.write("source.svg", SAMPLE_SVG)

    def test_inspect_reports_structure_palette_and_strokes(self):
        """Ensures inspect reports structure palette and strokes."""
        payload = json.loads(self.convert("inspect", self.svg, "--json").stdout)
        self.assertEqual(payload["viewBox"], [0.0, 0.0, 100.0, 100.0])
        self.assertEqual(payload["elements"]["rect"], 1)
        self.assertEqual(payload["elements"]["circle"], 1)
        self.assertEqual(payload["named_groups"],
                         [{"id": "layer-one", "children": 1}])
        # The palette is ordered dark to light.
        luminances = [entry["luminance"] for entry in payload["palette_dark_to_light"]]
        self.assertEqual(luminances, sorted(luminances))
        self.assertEqual({entry["color"] for entry in payload["palette_dark_to_light"]},
                         {"#101010", "#ff0000", "#00ff00", "#0000ff"})
        for entry in payload["palette_dark_to_light"]:
            self.assertEqual(sorted(entry), ["color", "hue", "luminance", "sat", "uses"])

    def test_inspect_has_a_human_readable_mode(self):
        """Ensures inspect has a human readable mode."""
        out = self.convert("inspect", self.svg).stdout
        self.assertIn("layer-one", out)
        self.assertIn("viewBox", out)

    def test_recolor_by_palette_maps_by_luminance_rank(self):
        """Ensures recolor by palette maps by luminance rank."""
        out = self.work / "recolored.svg"
        result = self.convert("recolor", self.svg, "-o", out, "--palette",
                              "#0b0221,#ff2a6d,#05d9e8,#d1f7ff")
        self.assertIn(f"wrote {out}", result.stdout)
        body = out.read_text()
        self.assertIn("#0b0221", body)
        self.assertIn("#d1f7ff", body)
        self.assertNotIn("#00ff00", body, "every source colour is remapped")
        # Structure is preserved: this is Style Preservation mode.
        self.assertEqual(body.count("<rect"), 1)
        self.assertEqual(body.count("<circle"), 1)

    def test_recolor_by_explicit_map_runs_before_the_palette(self):
        """Ensures recolor by explicit map runs before the palette."""
        out = self.work / "mapped.svg"
        self.convert("recolor", self.svg, "-o", out, "--map", "#ff0000=#111111")
        self.assertIn("#111111", out.read_text())
        self.assertNotIn("#ff0000", out.read_text())

    def test_recolor_adjustments_change_hsl_not_structure(self):
        """Ensures recolor adjustments change hsl not structure."""
        for flag, value in (("--darken", "0.25"), ("--lighten", "0.2"),
                            ("--saturate", "1.3"), ("--hue-shift", "20")):
            with self.subTest(flag=flag):
                out = self.work / f"adj{value.replace('.', '_')}{flag.strip('-')}.svg"
                self.convert("recolor", self.svg, "-o", out, flag, value)
                self.assertIn("<circle", out.read_text())

        grey = self.work / "grey.svg"
        self.convert("recolor", self.svg, "-o", grey, "--grayscale")
        body = grey.read_text()
        self.assertNotIn("#00ff00", body)

    def test_strokes_sets_width_caps_and_joins(self):
        """Ensures strokes sets width caps and joins."""
        out = self.work / "strokes.svg"
        result = self.convert("strokes", self.svg, "-o", out, "--set-width", "3",
                              "--linecap", "round", "--linejoin", "bevel")
        self.assertIn("touched", result.stdout)
        body = out.read_text()
        self.assertIn('stroke-width="3.0"', body)
        self.assertIn('stroke-linecap="round"', body)
        self.assertIn('stroke-linejoin="bevel"', body)

    def test_strokes_can_scale_outline_and_remove(self):
        """Ensures strokes can scale outline and remove."""
        scaled = self.work / "scaled.svg"
        self.convert("strokes", self.svg, "-o", scaled, "--width-scale", "2")
        self.assertIn('stroke-width="4"', scaled.read_text())

        outlined = self.work / "outlined.svg"
        self.convert("strokes", self.svg, "-o", outlined, "--outline", "#111111:3")
        self.assertIn("#111111", outlined.read_text())

        flat = self.work / "flat.svg"
        self.convert("strokes", self.svg, "-o", flat, "--remove")
        # Removal is explicit: the stroke attribute is set to "none".
        self.assertIn('stroke="none"', flat.read_text())
        self.assertNotIn('stroke="#0000ff"', flat.read_text())

    def test_rejected_stroke_options_write_nothing(self):
        """Ensures rejected stroke options write nothing."""
        for flag in ("--linecap", "--linejoin"):
            with self.subTest(flag=flag):
                out = self.work / f"bad-{flag.strip('-')}.svg"
                result = self.convert("strokes", self.svg, "-o", out, flag, "wobbly",
                                      code=2)
                self.assertIn("invalid choice: 'wobbly'",
                              result.stdout + result.stderr)
                self.assertFalse(out.exists())

    def test_inject_documents_its_layer_options(self):
        """Ensures inject documents its layer options."""
        out = self.convert("inject", "--help").stdout
        self.assertAllIn(["--defs", "--underlay", "--overlay", "--set", "--wrap-id",
                          "--drop-background", "--viewbox"], out)

    def test_inject_can_replace_the_background_and_viewbox(self):
        """Ensures inject can replace the background and viewbox."""
        out = self.work / "injected.svg"
        self.convert("inject", self.svg, "-o", out, "--viewbox", "0 0 120 120")
        self.assertIn('viewBox="0 0 120 120"', out.read_text())

    def test_every_subcommand_needs_an_input_file(self):
        """Ensures every subcommand needs an input file."""
        for command in ("inspect", "recolor", "strokes", "inject"):
            with self.subTest(command=command):
                self.convert(command, self.work / "absent.svg", code=None)


@require_module("lxml")
class OptimizeSvgTests(ScriptCase):
    def optimize(self, *args, code=0):
        return self.run_python(SCRIPTS / "optimize_svg.py", *args, code=code)

    def test_precision_rounding_shrinks_the_file_and_reports_the_saving(self):
        """Ensures precision rounding shrinks the file and reports the saving."""
        svg = self.write("source.svg", SAMPLE_SVG)
        out = self.work / "optimized.svg"
        result = self.optimize(svg, "-o", out, "--precision", "2")
        self.assertRegex(result.stdout,
                         r"source\.svg: \d+ -> \d+ bytes \(\d+%\)\s+\[numbers=\d+\]")
        self.assertLess(out.stat().st_size, svg.stat().st_size)
        self.assertIn('x="10.12"', out.read_text())
        self.assertNotIn("10.123456", out.read_text())

    def test_structure_is_preserved_by_the_optimiser(self):
        """Ensures structure is preserved by the optimiser."""
        svg = self.write("source.svg", SAMPLE_SVG)
        out = self.work / "optimized.svg"
        self.optimize(svg, "-o", out, "--precision", "2")
        body = out.read_text()
        for expected in ("<rect", "<circle", "<path", 'id="layer-one"', "<title>"):
            self.assertIn(expected, body)

    def test_minify_removes_inter_element_whitespace(self):
        """Ensures minify removes inter element whitespace."""
        svg = self.write("source.svg", SAMPLE_SVG)
        plain = self.work / "plain.svg"
        minified = self.work / "min.svg"
        self.optimize(svg, "-o", plain, "--precision", "2")
        self.optimize(svg, "-o", minified, "--precision", "2", "--minify")
        self.assertLess(minified.stat().st_size, plain.stat().st_size)
        self.assertNotIn("\n  ", minified.read_text())

    def test_dry_run_reports_without_writing(self):
        """Ensures dry run reports without writing."""
        svg = self.write("source.svg", SAMPLE_SVG)
        out = self.work / "never.svg"
        result = self.optimize(svg, "-o", out, "--dry-run", "--precision", "1")
        self.assertRegex(result.stdout, r"source\.svg: \d+ -> \d+ bytes")
        self.assertFalse(out.exists())

    def test_in_place_rewrites_the_source(self):
        """Ensures in place rewrites the source."""
        svg = self.write("source.svg", SAMPLE_SVG)
        before = svg.stat().st_size
        self.optimize(svg, "--in-place", "--precision", "0")
        self.assertLessEqual(svg.stat().st_size, before)
        self.assertNotIn("10.123456", svg.read_text())

    def test_use_hoisting_can_be_disabled(self):
        """Ensures use hoisting can be disabled."""
        svg = self.write(
            "repeats.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            "<title>Repeats</title>"
            '<rect x="1" y="1" width="10" height="10" fill="#111111"/>'
            '<rect x="1" y="1" width="10" height="10" fill="#111111"/>'
            '<rect x="1" y="1" width="10" height="10" fill="#111111"/></svg>',
        )
        hoisted = self.work / "hoisted.svg"
        plain = self.work / "plain.svg"
        self.optimize(svg, "-o", hoisted, "--precision", "2")
        self.optimize(svg, "-o", plain, "--precision", "2", "--no-use", "--no-hoist")
        self.assertNotIn("<use", plain.read_text())

    def test_in_place_takes_precedence_over_an_output_path(self):
        """Ensures in place takes precedence over an output path."""
        svg = self.write("source.svg", SAMPLE_SVG)
        out = self.work / "ignored.svg"
        self.optimize(svg, "-o", out, "--in-place", "--precision", "1")
        self.assertFalse(out.exists(), "--in-place wins, so -o is not written")
        self.assertNotIn("10.123456", svg.read_text())

    def test_a_missing_input_is_reported_without_a_partial_output(self):
        """Ensures a missing input is reported without a partial output."""
        out = self.work / "never.svg"
        self.optimize(self.work / "absent.svg", "-o", out, code=None)
        self.assertFalse(out.exists())

    def test_a_missing_input_is_an_error(self):
        """Ensures a missing input is an error."""
        self.optimize(self.work / "absent.svg", "-o", self.work / "x.svg", code=None)


@require_module("lxml")
class PixelGridTests(ScriptCase):
    def grid(self, *args, code=0):
        return self.run_python(SCRIPTS / "pixel_grid.py", *args, code=code)

    def make_sprite(self, body="..RR..\n.RRRR.\n..GG..\n"):
        return self.write("sprite.txt", body)

    def test_a_sprite_becomes_one_merged_path_per_colour(self):
        """Ensures a sprite becomes one merged path per colour."""
        sprite = self.make_sprite()
        out = self.work / "sprite.svg"
        result = self.grid(sprite, "-o", out, "--palette", "R=#ff0000,G=#00ff00")
        self.assertRegex(result.stdout,
                         r"wrote \S+sprite\.svg\s+\(6x3 grid, 2 colours, "
                         r"\d+ bytes\)")
        body = out.read_text()
        self.assertEqual(body.count("<path"), 2, "one merged path per colour")
        self.assertIn('id="c-R"', body)
        self.assertIn('id="c-G"', body)
        self.assertIn('fill="#ff0000"', body)
        self.assertIn('fill="#00ff00"', body)
        self.assertIn('shape-rendering="crispEdges"', body)
        self.assertIn('viewBox="0 0 6 3"', body)
        self.assertIn("<title>Pixel art</title>", body)

    def test_the_palette_may_live_in_the_sprite_header(self):
        """Ensures the palette may live in the sprite header."""
        sprite = self.write("inline.txt", "@R=#ff0000\n@G=#00ff00\nRR\nGG\n")
        out = self.work / "inline.svg"
        self.grid(sprite, "-o", out)
        self.assertIn("#ff0000", out.read_text())

    def test_an_unknown_key_is_refused_before_anything_is_written(self):
        """Ensures an unknown key is refused before anything is written."""
        sprite = self.make_sprite()
        out = self.work / "never.svg"
        result = self.grid(sprite, "-o", out, code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no palette colour for key(s): 'R', 'G'",
                      result.stdout + result.stderr)
        self.assertFalse(out.exists())

    def test_a_malformed_palette_line_is_reported(self):
        """Ensures a malformed palette line is reported."""
        sprite = self.write("bad.txt", "@R#ff0000\nRR\n")
        result = self.grid(sprite, "-o", self.work / "x.svg", code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("bad palette line", result.stdout + result.stderr)

    def test_dots_and_spaces_are_transparent(self):
        """Ensures dots and spaces are transparent."""
        sprite = self.write("sparse.txt", "@R=#ff0000\nR.R\n   \nR.R\n")
        out = self.work / "sparse.svg"
        result = self.grid(sprite, "-o", out)
        self.assertIn("3x3 grid", result.stdout)
        self.assertEqual(out.read_text().count("<path"), 1)

    def test_background_padding_outline_and_title_options(self):
        """Ensures background padding outline and title options."""
        sprite = self.make_sprite()
        out = self.work / "dressed.svg"
        self.grid(sprite, "-o", out, "--palette", "R=#ff0000,G=#00ff00",
                  "--bg", "#ffffff", "--pad", "2", "--outline", "#111111",
                  "--title", "My Sprite", "--mirror")
        body = out.read_text()
        self.assertIn("#ffffff", body)
        self.assertIn("My Sprite", body)
        self.assertIn("#111111", body)

    def test_the_grid_merges_a_whole_row_into_one_rectangle(self):
        """Ensures the grid merges a whole row into one rectangle."""
        sprite = self.write("wide.txt", "@R=#ff0000\n" + "R" * 8 + "\n")
        out = self.work / "wide.svg"
        result = self.grid(sprite, "-o", out)
        self.assertIn("8x1 grid, 1 colours", result.stdout)
        data = re.search(r'<path id="c-R"[^>]*\sd="([^"]+)"',
                         out.read_text()).group(1)
        self.assertEqual(data, "M0 0h8v1h-8z",
                         "a full row merges into a single integer rectangle")


@unittest.skipUnless(module_available("fontTools"), "requires fonttools")
@require_module("lxml")
class TextToPathTests(ScriptCase):
    """``text_to_path.py`` outlines glyphs so art does not depend on fonts."""

    def setUp(self):
        super().setUp()
        self.font = self.find_font()
        if self.font is None:
            self.skipTest("no .ttf/.otf font available on this machine")

    @staticmethod
    def find_font():
        roots = [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"),
                 Path.home() / ".fonts"]
        for root in roots:
            if not root.is_dir():
                continue
            for pattern in ("**/*.ttf", "**/*.otf"):
                for candidate in sorted(root.glob(pattern)):
                    return candidate
        return None

    def tool(self, *args, code=0):
        return self.run_python(SCRIPTS / "text_to_path.py", *args, code=code)

    def test_outlining_produces_path_data_not_text(self):
        """Ensures outlining produces path data not text."""
        result = self.tool(self.font, "Hello", "--d-only")
        data = result.stdout.strip()
        self.assertTrue(data.startswith("M"), data[:80])
        self.assertNotIn("<text", data)

    def test_the_svg_form_wraps_the_outline_in_a_path_element(self):
        """Ensures the svg form wraps the outline in a path element."""
        result = self.tool(self.font, "Hi", "--fill", "#ff0000", "--id", "logo",
                           "--size", "48")
        self.assertIn("<path", result.stdout)
        self.assertIn("#ff0000", result.stdout)

    def test_anchors_move_the_outline(self):
        """Ensures anchors move the outline."""
        starts = [self.tool(self.font, "AB", "--d-only", "--anchor", anchor).stdout
                  for anchor in ("start", "middle", "end")]
        self.assertEqual(len(set(starts)), 3, "each anchor must reposition the glyph")

    def test_tracking_widens_the_lettering(self):
        """Ensures tracking widens the lettering."""
        tight = self.tool(self.font, "AB", "--d-only").stdout
        loose = self.tool(self.font, "AB", "--d-only", "--tracking", "20").stdout
        self.assertNotEqual(tight, loose)

    def test_glyph_mode_lists_the_outlines_it_used(self):
        """Ensures glyph mode lists the outlines it used."""
        result = self.tool(self.font, "A", "--glyphs")
        self.assertTrue(result.stdout.strip())

    def test_a_missing_font_is_reported(self):
        """Ensures a missing font is reported."""
        result = self.tool(self.work / "absent.ttf", "Hi", code=None)
        self.assertNotEqual(result.returncode, 0)


class NewStyleTests(ScriptCase):
    """``new_style.py`` writes into the registry, so it runs against a copy."""

    def setUp(self):
        super().setUp()
        self.copy = self.work / "vector-art"
        shutil.copytree(VECTOR_ART, self.copy,
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.script = self.copy / "scripts/new_style.py"
        self.registry = self.copy / "styles/registry"

    def test_checks_documents_every_style_constraint(self):
        """Ensures checks documents every style constraint."""
        out = self.run_python(self.script, "--checks").stdout
        self.assertAllIn(
            ["forbid_elements", "require_elements_any", "max_colors", "min_colors",
             "forbid_path_curves", "integer_coords", "require_shape_rendering",
             "max_filters", "min_filters", "max_gradients", "min_gradients",
             "min_elements", "max_elements", "min_groups", "require_text",
             "forbid_text", "min_stroke_widths", "max_stroke_widths",
             "require_stroke", "forbid_stroke", "require_linecap", "require_linejoin",
             "dark_base", "light_base", "allow_bleed"],
            out,
        )

    def test_adding_a_style_extends_the_registry_and_a_reference_stub(self):
        """Ensures adding a style extends the registry and a reference stub."""
        result = self.run_python(
            self.script, "--id", "vaporwave", "--name", "Vaporwave",
            "--family", "genre", "--alias", "vapor wave", "--alias", "aesthetic",
            "--description", "Neon grids and sunsets", "--best-for", "posters",
            "--file", "genre")
        self.assertIn("added 'vaporwave'", result.stdout)
        self.assertIn("route_style.py --lint", result.stdout)

        registry = json.loads((self.registry / "genre.json").read_text())
        entry = self.style_by_id(registry, "vaporwave")
        self.assertEqual(entry["name"], "Vaporwave")
        self.assertEqual(entry["aliases"], ["vapor wave", "aesthetic"])
        self.assertIn("TODO", json.dumps(entry), "the stub is meant to be filled in")
        self.assertIn("posters", json.dumps(entry))

        references = (self.copy / "styles/references/genre.md").read_text()
        self.assertIn("vaporwave", references)

        # The real checkout is never touched.
        pristine = json.loads(
            (VECTOR_ART / "styles/registry/genre.json").read_text())
        self.assertNotIn("vaporwave", [item["id"] for item in pristine])

    def test_a_duplicate_id_is_refused(self):
        """Ensures a duplicate id is refused."""
        self.run_python(self.script, "--id", "dupe", "--name", "Dupe", "--family",
                        "genre", "--description", "d")
        result = self.run_python(self.script, "--id", "dupe", "--name", "Dupe",
                                 "--family", "genre", "--description", "d", code=None)
        self.assertNotEqual(result.returncode, 0)

    def test_a_new_family_starts_its_own_registry_and_reference_file(self):
        """Ensures a new family starts its own registry and reference file."""
        result = self.run_python(self.script, "--id", "neo", "--name", "Neo",
                                 "--family", "brand-new", "--description", "d")
        self.assertIn("added 'neo'", result.stdout)
        self.assertIn("styles/registry/brand-new.json", result.stdout)
        self.assertIn("styles/references/brand-new.md", result.stdout)
        registry = json.loads((self.registry / "brand-new.json").read_text())
        self.assertEqual([entry["id"] for entry in registry], ["neo"])
        self.assertTrue((self.copy / "styles/references/brand-new.md").is_file())

    def test_required_arguments_are_enforced(self):
        """Ensures required arguments are enforced."""
        result = self.run_python(self.script, "--id", "x", code=2)
        self.assertIn("--name", result.stdout + result.stderr)

    def test_a_style_can_extend_an_existing_one(self):
        """Ensures a style can extend an existing one."""
        result = self.run_python(self.script, "--id", "neo-ukiyo", "--name",
                                 "Neo Ukiyo", "--family", "genre", "--extends",
                                 "ukiyo-e", "--description", "d")
        self.assertIn("added 'neo-ukiyo'", result.stdout)
        registry = json.loads((self.registry / "genre.json").read_text())
        self.assertEqual(self.style_by_id(registry, "neo-ukiyo")["extends"], "ukiyo-e")

    @staticmethod
    def style_by_id(registry, style_id):
        for entry in registry:
            if entry.get("id") == style_id:
                return entry
        raise AssertionError(f"{style_id} was not added to the registry")


class RenderSvgCliTests(ScriptCase):
    """``render_svg.py`` needs Playwright; its CLI contract does not."""

    def test_help_documents_the_sheet_and_analysis_options(self):
        """Ensures help documents the sheet and analysis options."""
        out = self.run_python(SCRIPTS / "render_svg.py", "--help").stdout
        self.assertAllIn(["-o OUT", "-w WIDTH", "--bg", "--sheet", "--cols",
                          "--analyze", "--outdir", "headless Chromium"], out)

    def test_it_names_its_playwright_dependency_when_absent(self):
        """Ensures it names its playwright dependency when absent."""
        if module_available("playwright"):
            self.skipTest("playwright is installed; the failure path is unreachable")
        svg = self.write("a.svg", SAMPLE_SVG)
        result = self.run_python(SCRIPTS / "render_svg.py", svg, "-o",
                                 self.work / "a.png", code=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("playwright", result.stdout + result.stderr)
        self.assertFalse((self.work / "a.png").exists())

    def test_it_needs_at_least_one_input_file(self):
        """Ensures it needs at least one input file."""
        self.run_python(SCRIPTS / "render_svg.py", code=2)


if __name__ == "__main__":
    unittest.main()
