"""Pause planning and supported-route regressions without remote services or media tools."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from unittest import mock

from skill_scripts import SKILLS, ScriptCase


SCRIPTS = SKILLS / "presenter-video/scripts"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PresenterSegmentTests(ScriptCase):
    @classmethod
    def setUpClass(cls):
        cls.planner = load_script("plan_segments")

    def plan(self, spans, total=13, cap=6, min_gap=.25, min_segment=2, whole_seconds=False):
        return self.planner.plan(spans, total, cap, min_gap, min_segment, whole_seconds)

    def test_latest_feasible_pause_avoids_a_greedy_dead_end(self):
        """An earlier cut must win when taking the latest pause strands the remaining audio."""
        spans = [(0, 3.8), (4.2, 5.8), (6.2, 6.8), (7.2, 13)]
        result = self.plan(spans)
        self.assertEqual(result["seams_s"], [4, 7])
        self.assertEqual([s["requested_seconds"] for s in result["segments"]], [4, 3, 6])
        self.assertEqual(result["total_requested_seconds"], 13)
        self.assertEqual(result["segments"][-1]["audio_end_s"], 13)

    def test_latest_reachable_pause_remains_preferred(self):
        """Preserve long segments when several complete pause sequences are valid."""
        result = self.plan([(0, 3.8), (4.2, 5.8), (6.2, 10)], total=10)
        self.assertEqual(result["seams_s"], [6])

    def test_overlapping_spans_cannot_hide_a_narration_overrun(self):
        """Check the furthest speech end, even if a later-starting span ends earlier."""
        with self.assertRaisesRegex(ValueError, "timings end at 50"):
            self.plan([(0, 50), (1, 2)], total=10, cap=20)

    def test_nonfinite_options_are_rejected(self):
        """Invalid timing limits must never produce NaN/Infinity JSON or bypass the cap."""
        for option in ("total", "cap", "min_gap", "min_segment"):
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(option=option, value=value):
                    with self.assertRaisesRegex(ValueError, "finite"):
                        self.plan([(0, 1)], **{option: value})

    def test_negative_and_zero_limits_are_rejected(self):
        """Only the pause-gap limit may be zero; other limits must be positive."""
        for option, values in (("total", (0, -1)), ("cap", (0, -1)),
                               ("min_segment", (0, -1)), ("min_gap", (-1,))):
            for value in values:
                with self.subTest(option=option, value=value):
                    with self.assertRaises(ValueError):
                        self.plan([(0, 1)], **{option: value})

    def test_invalid_spans_are_rejected(self):
        """Negative, reversed, empty, and nonfinite speech spans cannot form a plan."""
        for spans in ([], [(-1, 1)], [(2, 1)], [(float("nan"), 1)],
                      [(0, float("inf"))], [(float("-inf"), 1)]):
            with self.subTest(spans=spans):
                with self.assertRaisesRegex(ValueError, "finite spans"):
                    self.plan(spans)

    def test_overlapping_speech_never_creates_a_false_pause(self):
        """Merge the occupied speech interval before choosing a cut."""
        result = self.plan([(1, 2), (0, 5), (6, 10)], total=10)
        self.assertEqual(result["seams_s"], [5.5])
        self.assertEqual(result["segments"][0]["ends_in_pause_s"], [5, 6])

    def test_whole_second_requests_fit_a_fractional_provider_cap(self):
        """Round billed durations upward while keeping each request within the cap."""
        result = self.plan([(0, 3.8), (4.2, 7.5)], total=7.5, cap=4.8,
                           whole_seconds=True)
        self.assertEqual(result["seams_s"], [4])
        self.assertEqual([s["requested_seconds"] for s in result["segments"]], [4, 4])
        self.assertEqual(result["segments"][-1]["audio_end_s"], 7.5)

    def test_unbroken_long_speech_has_no_valid_plan(self):
        """Refuse a cap violation when speech supplies no usable pauses."""
        with self.assertRaisesRegex(ValueError, "no sequence of pauses"):
            self.plan([(0, 13)])

    def test_short_single_clip_is_preserved(self):
        """An already short narration needs no artificial padding to the segment minimum."""
        result = self.plan([(0, 1)], total=1)
        self.assertEqual(result["seams_s"], [])
        self.assertEqual(result["segments"][0]["requested_seconds"], 1)

    def test_invalid_cli_input_preserves_an_existing_plan(self):
        """Reject invalid JSON timing values before replacing a user's output file."""
        timings = self.work / "timings.json"
        timings.write_text('[{"start": 0, "end": NaN}]')
        output = self.work / "plan.json"
        output.write_text("previous plan")
        result = self.run_python(SCRIPTS / "plan_segments.py",
                              "--timings", timings, "--audio-duration", "10", "--cap", "6",
                              "--output", output, code=2)
        self.assertIn("finite spans", result.stderr)
        self.assertEqual(output.read_text(), "previous plan")

    def test_output_preserves_neighboring_files_and_symlinks(self):
        """Publishing a plan must not consume a neighboring file or follow its symlink."""
        timings = self.work / "timings.json"
        timings.write_text('[{"start": 0, "end": 3}]')
        for kind in ("file", "symlink", "dangling"):
            with self.subTest(kind=kind):
                directory = self.work / kind
                directory.mkdir()
                output = directory / "plan.json"
                output.write_text("previous plan")
                neighbor = directory / "plan.json.tmp"
                target = directory / "unrelated.txt"
                if kind == "file":
                    neighbor.write_text("neighboring content")
                else:
                    if kind == "symlink":
                        target.write_text("unrelated content")
                    neighbor.symlink_to(target.name)
                before = set(directory.iterdir())
                result = self.run_python(SCRIPTS / "plan_segments.py",
                                         "--timings", timings, "--audio-duration", "3",
                                         "--cap", "6", "--output", output)
                self.assertFalse(output.is_symlink())
                self.assertEqual(output.read_text(), result.stdout)
                self.assertEqual(json.loads(result.stdout)["audio_duration_s"], 3)
                self.assertEqual(set(directory.iterdir()), before)
                if kind == "file":
                    self.assertEqual(neighbor.read_text(), "neighboring content")
                else:
                    self.assertTrue(neighbor.is_symlink())
                    self.assertEqual(neighbor.readlink(), Path(target.name))
                    if kind == "symlink":
                        self.assertEqual(target.read_text(), "unrelated content")
                    else:
                        self.assertFalse(target.exists())

    def test_failed_publication_preserves_plan_and_cleans_staging(self):
        """A failed replacement leaves the accepted plan intact and no staging file behind."""
        timings = self.work / "timings.json"
        timings.write_text('[{"start": 0, "end": 3}]')
        output = self.work / "plan.json"
        output.write_text("previous plan")
        before = set(self.work.iterdir())
        argv = ["plan_segments.py", "--timings", str(timings),
                "--audio-duration", "3", "--cap", "6", "--output", str(output)]
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(Path, "replace", side_effect=OSError("publication failed")):
            with self.assertRaisesRegex(OSError, "publication failed"):
                self.planner.main()
        self.assertEqual(output.read_text(), "previous plan")
        self.assertEqual(set(self.work.iterdir()), before)


class PresenterRouteTests(ScriptCase):
    def test_initializer_rejects_unbundled_route_and_style_options(self):
        """Unsupported explainer options must fail before creating any job files."""
        for arguments in (("--route", "styled"), ("--explainer-style", "v1-editorial")):
            with self.subTest(arguments=arguments):
                job_dir = self.work / "new-job"
                self.run_python(SCRIPTS / "init_job.py", "--job-dir", job_dir,
                             "--topic", "Synthetic topic", *arguments, code=2)
                self.assertFalse(job_dir.exists())

    def test_preflight_reports_unknown_route_without_an_unbundled_kits_dependency(self):
        """A legacy styled manifest gets a supported-route error, not a missing library request."""
        module = load_script("preflight")
        job = self.work / "job.json"
        job.write_text(json.dumps({"input": {"topic": "Synthetic topic"},
                                   "creative": {"route": "styled"}}))
        output = io.StringIO()
        with mock.patch.object(sys, "argv", ["preflight.py", str(job)]), \
                mock.patch.object(module.shutil, "which", return_value="ffprobe"), \
                mock.patch.object(module, "probe") as probe, \
                contextlib.redirect_stdout(output):
            self.assertEqual(module.main(), 1)
        report = json.loads(output.getvalue())
        self.assertFalse(report["ok"])
        self.assertIn("creative.route must be presenter, not 'styled'", report["errors"])
        self.assertNotIn("explainer/kits", output.getvalue())
        probe.assert_not_called()

    def test_state_checker_cannot_write_an_unsupported_route(self):
        """Reject a legacy styled manifest without changing its recorded state."""
        module = load_script("check_state")
        job = self.work / "job.json"
        original = json.dumps({"state": "verified", "creative": {"route": "styled"}})
        job.write_text(original)
        error = io.StringIO()
        with mock.patch.object(sys, "argv", ["check_state.py", str(job), "--write"]), \
                mock.patch.object(module.shutil, "which", return_value="ffprobe"), \
                contextlib.redirect_stderr(error):
            self.assertEqual(module.main(), 2)
        self.assertIn("creative.route must be presenter", error.getvalue())
        self.assertEqual(job.read_text(), original)
