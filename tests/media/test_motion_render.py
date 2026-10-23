"""Real-browser capture and FFmpeg contracts; required dependencies never skip.

Run separately from the lightweight suites: python -m unittest discover -s
 tests/media -p 'test_*.py' -v. Install the adjacent locked npm package, its
 Chromium revision, and ffmpeg/ffprobe first. All scenes and outputs are temporary.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path(__file__).resolve().parent
RENDER = ROOT / "skills/create-motion-videos/scripts/render.mjs"
WIDTH, HEIGHT, FPS = 64, 48, 4


class MotionRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for executable in ("node", "ffmpeg", "ffprobe"):
            if not shutil.which(executable):
                raise RuntimeError(
                    f"Required media test dependency missing: {executable}; "
                    "see the install steps in tests/README.md (Browser and video integration)"
                )
        if not (RUNTIME / "node_modules/playwright-core/package.json").is_file():
            raise RuntimeError(
                "Run npm ci --prefix tests/media before the media tests; "
                "see the install steps in tests/README.md (Browser and video integration)"
            )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="motion-render-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.film = self.root / "film"
        self.film.mkdir()
        self.output = self.root / "clip.mp4"
        self.env = os.environ.copy()
        # Explicit test dependencies take precedence over personal runtime overrides.
        for name in ("FFMPEG", "PLAYWRIGHT_CHROME", "CODEX_PRIMARY_RUNTIME_NODE_MODULES"):
            self.env.pop(name, None)

    def scene(self, script, markup=""):
        (self.film / "index.html").write_text(
            '<!doctype html><meta charset="utf-8">'
            '<style>html,body{margin:0;width:100%;height:100%;background:black}</style>'
            + markup + '<script>window.DUR=1;'
            + script + '</script>', encoding="utf-8"
        )

    def command(self, *args):
        return ["node", str(RENDER), str(self.film), "--runtime", str(RUNTIME),
                "--size", f"{WIDTH}x{HEIGHT}", "--fps", str(FPS),
                "--timeout-ms", "3000", *map(str, args)]

    def run_render(self, *args, success=True, env=None):
        result = subprocess.run(self.command(*args), cwd=self.root,
                                env=env or self.env, capture_output=True,
                                text=True, timeout=40)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(self.root.glob(".motion-render-*")), [])
        return result

    def decoded_levels(self):
        """Decode every frame; sample flat interiors to tolerate H.264 rounding."""
        decoded = subprocess.run(
            ["ffmpeg", "-v", "error", "-xerror", "-i", str(self.output),
             "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
            capture_output=True, check=True, timeout=20)
        self.assertEqual(decoded.stderr, b"")
        frame_size = WIDTH * HEIGHT * 3
        self.assertEqual(len(decoded.stdout) % frame_size, 0)
        center = (HEIGHT // 2 * WIDTH + WIDTH // 2) * 3
        return [tuple(decoded.stdout[start + center:start + center + 3])
                for start in range(0, len(decoded.stdout), frame_size)]

    def assert_levels(self, expected):
        frames = self.decoded_levels()
        self.assertEqual(len(frames), len(expected))
        for actual, level in zip(frames, expected):
            for channel in actual:
                self.assertAlmostEqual(channel, level, delta=3)

    def test_async_seek_is_repeatable_forward_reverse_and_fresh(self):
        """Await asynchronous draws and compare real pixels across seek histories."""
        self.scene("""
            window.READY=false;
            setTimeout(()=>window.READY=true,50);
            window.seek=async t=>{
                await new Promise(resolve=>setTimeout(resolve,150));
                const level=40+Math.floor(t*4)*40;
                document.body.style.background=`rgb(${level},${level},${level})`;
            };
        """)
        stills = self.root / "stills"
        self.run_render("--check-only", "--times", "0,0.25,0.75", "--stills", stills)
        report = json.loads((stills / "check.json").read_text())
        self.assertIs(report["passed"], True)
        self.assertEqual((report["width"], report["height"]), (WIDTH, HEIGHT))
        self.assertEqual([frame["time"] for frame in report["frames"]], [0, .25, .75])
        images = sorted(stills.glob("frame_*.png"))
        self.assertEqual(len(images), 3)
        hashes = [hashlib.sha256(image.read_bytes()).hexdigest() for image in images]
        self.assertEqual(hashes, [frame["sha256"] for frame in report["frames"]])
        self.assertEqual(len(set(hashes)), 3, "A constant/undrawn scene must not pass this fixture")

    def test_stateful_seek_fails_determinism_check(self):
        """Reject scenes whose frames depend on the order of earlier seeks."""
        self.scene("let n=0;window.seek=()=>{const x=++n*20;"
                   "document.body.style.background=`rgb(${x},${x},${x})`;};")
        result = self.run_render("--check-only", "--times", "0,0.5", success=False)
        self.assertIn("Determinism check failed", result.stderr)

    def test_silent_mp4_metadata_and_all_decoded_frames(self):
        """Export complete frames at the requested rate, size, and selected start."""
        self.scene("window.DUR=2;window.render=t=>{const x=40+Math.floor(t*4)*40;"
                   "document.body.style.background=`rgb(${x},${x},${x})`;};")
        self.run_render("--out", self.output, "--from", ".25", "--duration", ".9")
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format",
             "-of", "json", str(self.output)], capture_output=True, text=True,
            check=True, timeout=20)
        probe = json.loads(result.stdout)
        self.assertEqual(len(probe["streams"]), 1, "The exporter promises silent video")
        video = probe["streams"][0]
        self.assertEqual(video["codec_type"], "video")
        self.assertEqual(video["codec_name"], "h264")
        self.assertEqual((video["width"], video["height"]), (WIDTH, HEIGHT))
        self.assertEqual(video["avg_frame_rate"], "4/1")
        self.assertEqual(int(video["nb_read_frames"]), 3)
        self.assertAlmostEqual(float(probe["format"]["duration"]), .75, places=3)
        self.assert_levels([80, 120, 160])

    def test_temporal_samples_average_within_each_output_frame(self):
        """Average independent sample groups without leaking adjacent frames."""
        self.scene("window.seek=t=>{const x=20+Math.floor(t*8)*20;"
                   "document.body.style.background=`rgb(${x},${x},${x})`;};")
        self.run_render("--out", self.output, "--samples", "2", "--shutter", "1")
        self.assert_levels([30, 70, 110, 150])

    def test_page_asset_and_network_errors_preserve_existing_output(self):
        """Refuse broken or network-dependent scenes without replacing a prior export."""
        cases = [
            ("throw new Error('synthetic browser failure');", "", "synthetic browser failure"),
            ("window.seek=()=>{};", '<img src="missing.png">', "HTTP 404"),
            ("window.seek=()=>{};", '<img src="https://media.invalid/image.png">',
             "External request blocked"),
        ]
        for script, markup, expected in cases:
            with self.subTest(expected=expected):
                self.scene(script, markup)
                self.output.write_bytes(b"previous reviewed output")
                result = self.run_render("--out", self.output, "--overwrite", success=False)
                self.assertIn(expected, result.stderr)
                self.assertEqual(self.output.read_bytes(), b"previous reviewed output")

    def test_seek_failure_removes_partial_capture(self):
        """A scene failure after encoding starts removes work and preserves prior output."""
        self.scene("window.seek=t=>{if(t>0)throw new Error('synthetic seek failure');};")
        self.output.write_bytes(b"previous reviewed output")
        result = self.run_render("--out", self.output, "--overwrite", success=False)
        self.assertIn("Frame 1/4", result.stdout)
        self.assertIn("synthetic seek failure", result.stderr)
        self.assertEqual(self.output.read_bytes(), b"previous reviewed output")

    def test_missing_encoder_preserves_existing_output(self):
        """An unavailable encoder must clean temporary capture files and preserve output."""
        self.scene("window.seek=()=>{};")
        self.output.write_bytes(b"previous reviewed output")
        env = {**self.env, "FFMPEG": str(self.root / "missing-ffmpeg")}
        result = self.run_render("--out", self.output, "--overwrite", success=False, env=env)
        self.assertIn("ENOENT", result.stderr)
        self.assertEqual(self.output.read_bytes(), b"previous reviewed output")

    def test_failed_encoder_preserves_existing_output(self):
        """A started encoder's diagnostic and failed exit survive capture cleanup."""
        self.scene("window.seek=()=>{};")
        encoder = self.root / "failed-encoder"
        encoder.write_text(f"#!{sys.executable}\nimport sys\n"
                           "sys.stdin.buffer.read()\n"
                           "print('synthetic encoder failure',file=sys.stderr)\n"
                           "sys.exit(7)\n")
        encoder.chmod(0o755)
        self.output.write_bytes(b"previous reviewed output")
        result = self.run_render("--out", self.output, "--overwrite", success=False,
                                 env={**self.env, "FFMPEG": str(encoder)})
        self.assertIn("synthetic encoder failure", result.stderr)
        self.assertEqual(self.output.read_bytes(), b"previous reviewed output")

    def test_sigterm_stops_encoder_and_removes_partial_output(self):
        """Cancellation reaps the active encoder and leaves no partial export behind."""
        self.scene("window.DUR=30;window.seek=()=>{};")
        marker = self.root / "encoder.pid"
        encoder = self.root / "waiting-encoder"
        encoder.write_text(f"#!{sys.executable}\nimport os,time\n"
                           f"open({str(marker)!r},'w').write(str(os.getpid()))\n"
                           "time.sleep(60)\n")
        encoder.chmod(0o755)
        self.output.write_bytes(b"previous reviewed output")
        process = subprocess.Popen(self.command("--out", self.output, "--overwrite"),
                                   cwd=self.root, env={**self.env, "FFMPEG": str(encoder)},
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 15
            while not marker.exists() and time.monotonic() < deadline and process.poll() is None:
                time.sleep(.05)
            self.assertTrue(marker.exists(), "Encoder did not start")
            encoder_pid = int(marker.read_text())
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 143, stdout + stderr)
            self.assertIn("Stopped by SIGTERM", stderr)
            with self.assertRaises(ProcessLookupError):
                os.kill(encoder_pid, 0)
            self.assertEqual(self.output.read_bytes(), b"previous reviewed output")
            self.assertEqual(list(self.root.glob(".motion-render-*")), [])
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=10)
            if marker.exists():
                try:
                    os.kill(int(marker.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass


if __name__ == "__main__":
    unittest.main()
