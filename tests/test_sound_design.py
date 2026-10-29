"""Exercise every procedural preset plus deterministic rendering and cue failure semantics."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/sound-design/scripts'
sys.path.insert(0, str(SCRIPTS))
import sfx


class SoundTests(unittest.TestCase):
    def test_every_preset_renders_finite_stereo_with_its_expected_duration(self):
        """Ensures all shipped presets have complete recipes and produce usable unclipped audio."""
        self.assertEqual(len(sfx.bank()), 237)
        for identifier, row in sfx.bank().items():
            with self.subTest(sound=identifier):
                audio, seed = sfx.render(identifier)
                self.assertEqual(seed, row['seed'])
                self.assertEqual(audio.shape[1], 2)
                self.assertTrue(np.isfinite(audio).all())
                self.assertGreater(float(np.max(np.abs(audio))), 0)
                self.assertLessEqual(float(np.max(np.abs(audio))), 1)
                self.assertAlmostEqual(len(audio) / sfx.RATE, row['meta']['dur_s'], delta=.01)

    def test_seed_and_peak_anchor_are_reproducible(self):
        """Ensures repeated seeds reproduce samples and peak alignment uses the rendered waveform."""
        a, _ = sfx.render('cut_hit/sub', 7)
        b, _ = sfx.render('cut_hit/sub', 7)
        np.testing.assert_array_equal(a, b)
        mixed, cues = sfx.mix({'duration': 3, 'cues': [
            {'id': 'cut_hit/sub', 'seed': 7, 'at': 1, 'align': 'peak', 'gain_db': -6}]})
        self.assertEqual(cues[0]['anchor'], 1)
        self.assertEqual(np.argmax(np.max(np.abs(mixed), axis=1)), sfx.RATE)

    def test_invalid_cues_clipping_and_output_preservation(self):
        """Ensures invalid timelines and clipped signals fail without replacing output."""
        for plan in [
            {'duration': float('nan'), 'cues': []},
            {'duration': 1, 'cues': [{'id': 'cut_hit/sub', 'at': -1}]},
            {'duration': .1, 'cues': [{'id': 'cut_hit/sub', 'at': 0}]},
            {'duration': 1, 'cues': [{'id': 'missing', 'at': 0}]},
            {'duration': 1, 'cues': [{'id': 'cut_hit/sub', 'at': .5, 'align': 'bad'}]},
        ]:
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                sfx.mix(plan)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'sound.wav'
            output.write_bytes(b'previous')
            with self.assertRaises(ValueError):
                sfx.save(output, np.ones((5, 2), dtype=np.float32) * 2, force=True)
            self.assertEqual(output.read_bytes(), b'previous')
            samples, _ = sfx.render('cut_hit/sub')
            report = sfx.save(output, samples, force=True)
            rate, encoded = wavfile.read(output)
            self.assertEqual(rate, 48000)
            self.assertEqual(encoded.shape, samples.shape)
            self.assertEqual(encoded.dtype, np.int16)
            self.assertEqual(report['frames'], len(samples))

    def test_cli_resolves_assets_outside_skill_directory(self):
        """Ensures installed helpers find bundled presets independently of the working directory."""
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(SCRIPTS / 'sfx.py'), 'list', '--query', 'cut_hit'],
                                    cwd=tmp, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(any(r['id'] == 'cut_hit/sub' for r in json.loads(result.stdout)))


if __name__ == '__main__':
    unittest.main()
