#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regression tests for color-mode coherence in design_system.py (issue #428).

Style, palette and anti-patterns used to be resolved independently, so a
dark-primary style could be returned alongside a light palette and a
"Dark mode by default" anti-pattern.

Stdlib-only (unittest, not pytest) to match test_core.py -- this project ships
with zero external dependencies.

Run with:
    python -m unittest discover -s scripts/tests -v
or directly:
    python scripts/tests/test_design_system_mode.py
"""

import re
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = (Path(__file__).resolve().parents[2] / 'skills/design-research/scripts')
sys.path.insert(0, str(SCRIPTS_DIR))

from design_system import (  # noqa: E402
    _filter_anti_patterns_for_mode,
    _contrast_ratio,
    _mode_support_labels,
    _palette_is_dark,
    _query_wants_dark,
    _relative_luminance,
    _resolve_color_mode,
    _select_palette_for_mode,
    _style_is_dark_primary,
    BOX_WIDTH,
    DesignSystemGenerator,
    format_ascii_box,
    format_markdown,
    format_master_md,
)  # noqa: I001 - private helpers first, public class last

LIGHT_PALETTE = {"Product Type": "SaaS", "Background": "#F8FAFC", "Foreground": "#020617"}
DARK_PALETTE = {"Product Type": "Fintech/Crypto", "Background": "#0F172A", "Foreground": "#F8FAFC"}

# Verbatim from styles.csv row "Modern Dark (Cinema Mobile)".
DARK_PRIMARY_STYLE = {
    "Style Category": "Modern Dark (Cinema Mobile)",
    "Light Mode ✓": "✓ Light mode only as exception",
    "Dark Mode ✓": "✓ Dark Mode Primary",
}
DUAL_MODE_STYLE = {
    "Style Category": "Minimalism",
    "Light Mode ✓": "✓ Full",
    "Dark Mode ✓": "✓ Full",
}


class TestLuminance(unittest.TestCase):
    def test_parses_six_and_three_digit_hex(self):
        """Ensures parses six and three digit hex in the imported design research engine."""
        self.assertAlmostEqual(_relative_luminance("#FFFFFF"), 1.0, places=6)
        self.assertAlmostEqual(_relative_luminance("#000000"), 0.0, places=6)
        self.assertAlmostEqual(_relative_luminance("#FFF"), 1.0, places=6)

    def test_returns_none_for_unparseable(self):
        """Ensures returns none for unparseable in the imported design research engine."""
        for value in ("", "nope", "#12", "#GGGGGG", None):
            self.assertIsNone(_relative_luminance(value))

    def test_classifies_backgrounds_from_the_shipped_data(self):
        # Lightest dark background and darkest light background in colors.csv.
        """Ensures classifies backgrounds from the shipped data in the imported design research engine."""
        self.assertTrue(_palette_is_dark({"Background": "#1F2937"}))
        self.assertFalse(_palette_is_dark({"Background": "#E8ECF1"}))

    def test_missing_background_is_not_dark(self):
        """Ensures missing background is not dark in the imported design research engine."""
        self.assertFalse(_palette_is_dark({}))
        self.assertFalse(_palette_is_dark(None))


class TestModeResolution(unittest.TestCase):
    def test_dark_primary_style_detected(self):
        """Ensures dark primary style detected in the imported design research engine."""
        self.assertTrue(_style_is_dark_primary(DARK_PRIMARY_STYLE))

    def test_dual_mode_style_is_not_dark_primary(self):
        """Ensures dual mode style is not dark primary in the imported design research engine."""
        self.assertFalse(_style_is_dark_primary(DUAL_MODE_STYLE))
        self.assertFalse(_style_is_dark_primary({}))

    def test_query_keywords(self):
        """Ensures query keywords in the imported design research engine."""
        self.assertTrue(_query_wants_dark("fintech B2B professional dark mode"))
        self.assertTrue(_query_wants_dark("gaming app OLED"))
        self.assertFalse(_query_wants_dark("healthcare clinic booking app"))
        self.assertFalse(_query_wants_dark(""))

    def test_either_signal_resolves_dark(self):
        """Ensures either signal resolves dark in the imported design research engine."""
        self.assertEqual(_resolve_color_mode("saas dark mode", DUAL_MODE_STYLE), "dark")
        self.assertEqual(_resolve_color_mode("saas", DARK_PRIMARY_STYLE), "dark")
        self.assertEqual(_resolve_color_mode("saas", DUAL_MODE_STYLE), "light")


class TestPaletteSelection(unittest.TestCase):
    def test_dark_mode_skips_light_palettes(self):
        """Ensures dark mode skips light palettes in the imported design research engine."""
        chosen = _select_palette_for_mode([LIGHT_PALETTE, DARK_PALETTE], "dark")
        self.assertEqual(chosen["Background"], "#0F172A")

    def test_dark_mode_falls_back_to_top_hit_when_no_dark_ramp_exists(self):
        """Ensures dark mode falls back to top hit when no dark ramp exists in the imported design research engine."""
        chosen = _select_palette_for_mode([LIGHT_PALETTE], "dark")
        self.assertEqual(chosen["Background"], "#F8FAFC")

    def test_light_mode_keeps_the_existing_top_hit_behaviour(self):
        """Ensures light mode keeps the existing top hit behaviour in the imported design research engine."""
        chosen = _select_palette_for_mode([DARK_PALETTE, LIGHT_PALETTE], "light")
        self.assertEqual(chosen["Background"], "#0F172A")

    def test_empty_results(self):
        """Ensures empty results in the imported design research engine."""
        self.assertEqual(_select_palette_for_mode([], "dark"), {})

    def test_category_identity_wins_over_unrelated_dark_palette(self):
        """Ensures category identity wins over unrelated dark palette in the imported design research engine."""
        chosen = _select_palette_for_mode(
            [LIGHT_PALETTE, DARK_PALETTE], "dark", "SaaS")
        self.assertEqual("SaaS", chosen["Product Type"])
        self.assertEqual("derived-dark", chosen["_mode_derivation"])
        self.assertTrue(_palette_is_dark(chosen))
        self.assertGreaterEqual(
            _contrast_ratio(chosen["Ring"], chosen["Background"]), 3.0)


class TestAntiPatternGating(unittest.TestCase):
    def test_dark_clause_dropped_others_kept(self):
        """Ensures dark clause dropped others kept in the imported design research engine."""
        result = _filter_anti_patterns_for_mode(
            "Excessive animation + Dark mode by default", "dark")
        self.assertEqual(result, "Excessive animation")

    def test_light_mode_is_a_no_op(self):
        """Ensures light mode is a no op in the imported design research engine."""
        original = "Excessive animation + Dark mode by default"
        self.assertEqual(_filter_anti_patterns_for_mode(original, "light"), original)

    def test_unrelated_anti_patterns_survive_dark_mode(self):
        """Ensures unrelated anti patterns survive dark mode in the imported design research engine."""
        original = "Complex jargon + Tiny tap targets"
        self.assertEqual(_filter_anti_patterns_for_mode(original, "dark"), original)

    def test_empty_input(self):
        """Ensures empty input in the imported design research engine."""
        self.assertEqual(_filter_anti_patterns_for_mode("", "dark"), "")


class TestEndToEndCoherence(unittest.TestCase):
    """The exact reproduction from issue #428."""

    QUERY = "SaaS invoicing fintech B2B professional dark mode"

    def test_dark_query_gets_a_dark_background(self):
        """Ensures dark query gets a dark background in the imported design research engine."""
        ds = DesignSystemGenerator().generate(self.QUERY)
        background = ds["colors"]["background"]
        self.assertTrue(
            _palette_is_dark({"Background": background}),
            "dark-mode query returned a light background: {}".format(background),
        )

    def test_generator_exports_every_semantic_foreground_pair(self):
        """Ensures generator exports every semantic foreground pair in the imported design research engine."""
        colors = DesignSystemGenerator().generate("SaaS dashboard")["colors"]
        pairs = (
            ("on_primary", "primary"),
            ("on_secondary", "secondary"),
            ("on_accent", "accent"),
            ("foreground", "background"),
            ("card_foreground", "card"),
            ("muted_foreground", "muted"),
            ("on_destructive", "destructive"),
        )
        for foreground, background in pairs:
            with self.subTest(pair=foreground):
                self.assertTrue(colors[foreground])
                self.assertTrue(colors[background])
                self.assertGreaterEqual(
                    _contrast_ratio(colors[foreground], colors[background]), 4.5
                )
        self.assertEqual(colors["on_cta"], colors["on_accent"])

    def test_dark_query_foreground_is_lighter_than_background(self):
        """Ensures dark query foreground is lighter than background in the imported design research engine."""
        ds = DesignSystemGenerator().generate(self.QUERY)
        background = _relative_luminance(ds["colors"]["background"])
        foreground = _relative_luminance(ds["colors"]["foreground"])
        self.assertIsNotNone(background)
        self.assertIsNotNone(foreground)
        self.assertGreater(foreground, background)

    def test_dark_query_does_not_advise_against_dark_mode(self):
        """Ensures dark query does not advise against dark mode in the imported design research engine."""
        ds = DesignSystemGenerator().generate(self.QUERY)
        self.assertNotIn("dark mode", ds["anti_patterns"].lower())

    def test_light_query_keeps_a_light_background(self):
        """Ensures light query keeps a light background in the imported design research engine."""
        ds = DesignSystemGenerator().generate("healthcare clinic booking app")
        self.assertFalse(_palette_is_dark({"Background": ds["colors"]["background"]}))


class TestLightResultOutputCoherence(unittest.TestCase):
    """A light result that avoids dark mode must not also call dark "supported"."""

    QUERY = "beauty spa wellness"

    @classmethod
    def setUpClass(cls):
        cls.ds = DesignSystemGenerator().generate(cls.QUERY, "Serenity Spa")

    def test_dark_support_is_qualified_when_the_product_avoids_dark_mode(self):
        """Ensures dark support is qualified when the product avoids dark mode in the imported design research engine."""
        self.assertIn("dark mode", self.ds["anti_patterns"].lower())
        light, dark = _mode_support_labels(self.ds["style"], self.ds["anti_patterns"])
        self.assertIn("avoid for this product", dark)
        self.assertIn("avoid for this product", format_ascii_box(self.ds))
        self.assertIn("avoid for this product", format_markdown(self.ds))

    def test_labels_unchanged_when_dark_mode_is_not_avoided(self):
        """Ensures labels unchanged when dark mode is not avoided in the imported design research engine."""
        style = {"light_mode": "supported", "dark_mode": "supported"}
        self.assertEqual(_mode_support_labels(style, "Harsh animations"),
                         ("supported", "supported"))

    def test_ascii_box_lines_never_overflow_the_border(self):
        """Ensures ascii box lines never overflow the border in the imported design research engine."""
        for query in (self.QUERY, "SaaS invoicing fintech B2B professional dark mode"):
            with self.subTest(query=query):
                ds = DesignSystemGenerator().generate(query, motion=7)
                widths = {len(re.sub(r"\033\[[0-9;]*m", "", line))
                          for line in format_ascii_box(ds).splitlines()}
                self.assertEqual(widths, {BOX_WIDTH + 1})

    def test_master_button_text_meets_contrast_on_its_background(self):
        """Ensures master button text meets contrast on its background in the imported design research engine."""
        colors = self.ds["colors"]
        master = format_master_md(self.ds)
        primary = re.search(r"\.btn-primary \{\n  background: (#\w+);\n  color: (#\w+);", master)
        secondary = re.search(r"\.btn-secondary \{\n  background: transparent;\n  color: (#\w+);", master)
        self.assertGreaterEqual(_contrast_ratio(primary.group(2), primary.group(1)), 4.5)
        self.assertGreaterEqual(_contrast_ratio(secondary.group(1), colors["background"]), 4.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
