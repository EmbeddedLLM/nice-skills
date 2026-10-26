"""Exercise narration-first production without credentials or paid services."""

import importlib.util
import io
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch
import wave

from skill_scripts import ScriptCase, SKILLS, require_binary


def load_story():
    spec = importlib.util.spec_from_file_location("explainer_story", SKILLS / "explainer-video/scripts/story.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExplainerCase(ScriptCase):
    def setUp(self):
        super().setUp()
        self.topic = self.work / "story"
        self.topic.mkdir()
        (self.topic / "script.md").write_text(
            "---\ntitle: A simple queue\n---\n## queue | Requests wait\n"
            "Requests arrive.\nThe worker handles each request.\n", encoding="utf-8")


class ExplainerContractTests(ExplainerCase):
    def test_credentials_do_not_enable_paid_speech(self):
        """A populated API key cannot silently select a billable request."""
        script = load_story()
        with patch.object(sys, "argv", ["story.py", str(self.topic)]), \
             patch.dict(script.os.environ, {"MINIMAX_API_KEY": "synthetic-never-send"}), \
             patch.object(script.urllib.request, "urlopen") as network, \
             patch("sys.stderr", new_callable=io.StringIO), \
             self.assertRaises(SystemExit) as error:
            script.main()
        self.assertEqual(error.exception.code, 2)
        network.assert_not_called()
        self.assertFalse((self.topic / "audio").exists())

    def test_conflicting_audio_modes_are_rejected(self):
        """Local narration cannot accidentally become a paid or silent run."""
        for flags in (("--audio", "recording.wav", "--tts-provider", "minimax"),
                      ("--audio", "recording.wav", "--dry"),
                      ("--dry", "--tts-provider", "minimax")):
            with self.subTest(flags=flags):
                self.run_python(self.script("explainer-video", "scripts", "story.py"),
                                self.topic, *flags, code=2)
        self.assertFalse((self.topic / "audio").exists())

    def test_explicit_provider_without_credentials_fails_before_writes(self):
        """Opting into MiniMax still requires a credential, with no fallback."""
        script = load_story()
        with patch.object(sys, "argv", ["story.py", str(self.topic), "--tts-provider", "minimax"]), \
             patch.dict(script.os.environ, {}, clear=True), \
             patch.object(script.urllib.request, "urlopen") as network, \
             patch("sys.stdout", new_callable=io.StringIO), \
             self.assertRaises(SystemExit) as error:
            script.main()
        self.assertIn("MINIMAX_API_KEY", str(error.exception))
        network.assert_not_called()
        self.assertFalse((self.topic / "audio").exists())

    def test_estimate_only_does_not_require_credentials(self):
        """Script review stays read-only and can run entirely offline."""
        before = set(self.topic.iterdir())
        self.run_python(self.script("explainer-video", "scripts", "story.py"), self.topic, "--check")
        self.assertEqual(set(self.topic.iterdir()), before)

    def test_paid_request_contract_is_mocked(self):
        """The optional request carries pronunciation and caches complete results."""
        script = load_story()
        response = {"base_resp": {"status_code": 0}, "data": {
            "audio": "00ff", "subtitle_file": "https://example.invalid/subtitles"}}
        subtitles = [{"timestamped_words": []}]
        mp3, timestamps = self.work / "line.mp3", self.work / "line.json"
        with patch.dict(script.os.environ, {"MINIMAX_API_KEY": "synthetic-never-send"}), \
             patch.object(script.urllib.request, "urlopen", side_effect=[
                 io.BytesIO(json.dumps(response).encode()), io.BytesIO(json.dumps(subtitles).encode())
             ]) as network:
            script.tts("重算", "test-voice", 1.05, str(mp3), str(timestamps), ("重算/(chong2)(suan4)",))
        payload = json.loads(network.call_args_list[0].args[0].data)
        self.assertEqual(payload["pronunciation_dict"], {"tone": ["重算/(chong2)(suan4)"]})
        self.assertEqual(mp3.read_bytes(), b"\x00\xff")
        self.assertEqual(json.loads(timestamps.read_text()), subtitles)
        self.assertFalse(list(self.work.glob("*.part")))

    def test_no_detectable_speech_span_uses_forward_estimated_timings(self):
        """A full-recording pause cannot produce reversed line intervals."""
        script = load_story()
        bounds, matched = script.place_lines(["Requests arrive.", "Work continues."], [(0, 2.46)], 2.46)
        self.assertFalse(matched)
        self.assertEqual(bounds[0][0], 0)
        self.assertAlmostEqual(bounds[-1][1], 2.46)
        self.assertTrue(all(0 <= start < end <= 2.46 for start, end in bounds))
        self.assertLessEqual(bounds[0][1], bounds[1][0])

    def test_short_caption_lines_do_not_overlap_or_extend_the_recording(self):
        """Caption readability cannot be improved by inventing extra audio time."""
        (self.topic / "story.json").write_text(json.dumps({"lines": [
            {"text": "One", "start": 0, "end": 0.2, "words": [["One", 0]]},
            {"text": "Two", "start": 0.2, "end": 0.3, "words": [["Two", 0.2]]}
        ]}))
        result = self.run_python(self.script("explainer-video", "scripts", "srt.py"), self.topic)
        self.assertIn("00:00:00,000 --> 00:00:00,200", result.stdout)
        self.assertIn("00:00:00,200 --> 00:00:00,300", result.stdout)
        (self.topic / "story.json").write_text(json.dumps({"lines": [
            {"text": "Two", "start": 0.2, "end": 0.2, "words": [["Two", 0.2]]}
        ]}))
        result = self.run_python(self.script("explainer-video", "scripts", "srt.py"), self.topic, code=1)
        self.assertIn("correct the story timing", result.stderr)

    def test_pause_markers_preserve_provider_word_timing(self):
        """Removing speech markup must not shift actual returned timestamps."""
        script = load_story()
        raw = "一<#0.45#>二<#0.45#>三"
        words = [{"word_begin": raw.index(unit), "word_end": raw.index(unit) + 1, "time_begin": at}
                 for unit, at in zip("一二三", (125, 1375, 2625))]
        self.assertEqual(script.words_from_engine(raw, [{"timestamped_words": words}], 7),
                         [["一", 7.125], ["二", 8.375], ["三", 9.625]])
        self.assertEqual(script.shown(raw), "一二三")


@require_binary("ffmpeg")
@require_binary("ffprobe")
class ExplainerLocalProductionTests(ExplainerCase):
    def setUp(self):
        super().setUp()
        # Deliberately copy outside the checkout and execute from another cwd.
        self.skill = self.work / "installed-explainer"
        shutil.copytree(SKILLS / "explainer-video", self.skill)
        self.recording = self.work / "recording.wav"
        rate, duration = 16000, 2.46
        with wave.open(str(self.recording), "wb") as output:
            output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
            output.writeframes(b"".join(struct.pack("<h", int(9000 * math.sin(2 * math.pi * 440 * i / rate)))
                                       for i in range(round(rate * duration))))
        self.images = []
        for color, rgb in (("red", (255, 0, 0)), ("blue", (0, 0, 255))):
            path = self.work / f"{color}.ppm"
            path.write_bytes(b"P6\n32 18\n255\n" + bytes(rgb) * 32 * 18)
            self.images.append(path)

    def build_story(self):
        self.run_python(self.skill / "scripts/story.py", self.topic, "--audio", self.recording,
                        cwd=self.work, env={"MINIMAX_API_KEY": "synthetic-never-send"})
        return json.loads((self.topic / "story.json").read_text())

    def scenes(self, duration):
        path = self.work / "scenes.json"
        path.write_text(json.dumps({"width": 160, "height": 90, "fps": 10, "scenes": [
            {"image": "red.ppm", "duration": duration / 2},
            {"image": "blue.ppm", "duration": duration / 2}]}))
        return path

    def test_supplied_audio_to_captions_and_video_from_isolated_skill(self):
        """The copied package produces real decoded video and captions without an API."""
        before = self.recording.read_bytes()
        story = self.build_story()
        self.assertEqual(story["timing"], "estimated")
        previous_end = 0
        for line in story["lines"]:
            self.assertGreaterEqual(line["start"], previous_end)
            self.assertLess(line["start"], line["end"])
            self.assertLessEqual(line["end"], story["duration"])
            word_times = [timestamp for _, timestamp in line["words"]]
            self.assertEqual(word_times, sorted(word_times))
            self.assertTrue(all(line["start"] <= value <= line["end"] for value in word_times))
            previous_end = line["end"]
        self.assertAlmostEqual(story["duration"], 2.46, places=2)
        self.assertNotIn("draft", story)
        self.assertEqual(self.recording.read_bytes(), before)
        self.assertEqual(list((self.topic / "audio/tts").iterdir()), [])
        captions = self.work / "captions.srt"
        self.run_python(self.skill / "scripts/srt.py", self.topic / "story.json", captions, cwd=self.work)
        self.assertIn("Requests arrive", captions.read_text())
        directory_captions = self.work / "directory-captions.srt"
        self.run_python(self.skill / "scripts/srt.py", self.topic, directory_captions, cwd=self.work)
        self.assertEqual(directory_captions.read_bytes(), captions.read_bytes())
        self.assertIn(" --> ", captions.read_text())
        def seconds(timestamp):
            hours, minutes, value = timestamp.replace(",", ".").split(":")
            return int(hours) * 3600 + int(minutes) * 60 + float(value)
        previous_end = 0
        for line in captions.read_text().splitlines():
            if " --> " in line:
                start, end = map(seconds, line.split(" --> "))
                self.assertGreaterEqual(start, previous_end)
                self.assertLess(start, end)
                self.assertLessEqual(end, story["duration"])
                previous_end = end
        output = self.work / "render.mp4"
        self.run_python(self.skill / "scripts/render_story.py", self.topic / "story.json",
                        self.scenes(story["duration"]), output, cwd=self.work)
        probe = self._run(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-of", "json", str(output)])
        streams = json.loads(probe.stdout)["streams"]
        video = next(item for item in streams if item["codec_type"] == "video")
        self.assertEqual((video["width"], video["height"]), (160, 90))
        self.assertEqual(video["avg_frame_rate"], "10/1")
        self.assertEqual(int(video["nb_read_frames"]), 25)
        self.assertTrue(any(item["codec_type"] == "audio" for item in streams))
        for timestamp, channel in (("0.2", 0), ("1.8", 2)):
            pixel = subprocess.check_output([
                "ffmpeg", "-v", "error", "-ss", timestamp, "-i", str(output),
                "-frames:v", "1", "-vf", "scale=1:1", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"
            ])
            self.assertGreater(pixel[channel], 200)
            self.assertLess(pixel[2 - channel], 30)
        self.assertFalse(list(self.work.glob(".explainer-*")))
        existing = output.read_bytes()
        self.run_python(self.skill / "scripts/render_story.py", self.topic / "story.json",
                        self.work / "scenes.json", output, code=1)
        self.assertEqual(output.read_bytes(), existing)

    def test_failed_audio_replacement_preserves_accepted_recording_and_story(self):
        """Invalid replacement media cannot erase an already accepted audio revision."""
        self.build_story()
        audio, metadata = self.topic / "audio/narration.wav", self.topic / "story.json"
        before_audio, before_metadata = audio.read_bytes(), metadata.read_bytes()
        invalid = self.work / "invalid.wav"
        invalid.write_text("not audio")
        self.run_python(self.skill / "scripts/story.py", self.topic, "--audio", invalid, code=1)
        self.assertEqual(audio.read_bytes(), before_audio)
        self.assertEqual(metadata.read_bytes(), before_metadata)
        self.assertFalse(list((self.topic / "audio").glob(".import-*")))

    def test_reusing_derived_recording_does_not_transcode_or_modify_it(self):
        """Revising timing against the accepted derived file preserves its exact bytes."""
        self.build_story()
        audio = self.topic / "audio/narration.wav"
        before = audio.read_bytes()
        self.run_python(self.skill / "scripts/story.py", self.topic, "--audio", audio)
        self.assertEqual(audio.read_bytes(), before)
        self.assertEqual(json.loads((self.topic / "story.json").read_text())["timing"], "estimated")

    def test_bad_timeline_and_bad_image_do_not_publish_output(self):
        """Missing or unrenderable scenes and invalid durations cannot yield partial delivery."""
        story = self.build_story()
        config_path = self.scenes(story["duration"])
        original = json.loads(config_path.read_text())
        cases = [
            {**original, "width": 159},
            {**original, "fps": True},
            {**original, "scenes": [{"image": "red.ppm", "duration": 2.4}]},
            {**original, "scenes": [{"image": "red.ppm", "duration": 1}]},
            {**original, "scenes": [{"image": "red.ppm", "duration": float("nan")}]},
            {**original, "scenes": [{"image": "missing.png", "duration": story["duration"]}]},
        ]
        bad = self.work / "broken.png"
        bad.write_text("not an image")
        cases.append({**original, "scenes": [{"image": "broken.png", "duration": story["duration"]}]})
        for config in cases:
            with self.subTest(config=config):
                config_path.write_text(json.dumps(config))
                output = self.work / "failed.mp4"
                self.run_python(self.skill / "scripts/render_story.py", self.topic / "story.json",
                                config_path, output, code=1)
                self.assertFalse(output.exists())
                self.assertFalse(list(self.work.glob(".explainer-*")))

    def test_dangling_output_symlink_is_not_followed(self):
        """A reserved output link must not cause writes to its missing target."""
        story = self.build_story()
        target, output = self.work / "target.mp4", self.work / "reserved.mp4"
        output.symlink_to(target)
        result = self.run_python(self.skill / "scripts/render_story.py", self.topic / "story.json",
                                 self.scenes(story["duration"]), output, code=1)
        self.assertIn("refusing to overwrite", result.stderr)
        self.assertTrue(output.is_symlink())
        self.assertFalse(target.exists())

    def test_silent_draft_cannot_be_delivered_as_narration(self):
        """Draft audio is visibly labeled and rejected by the delivery renderer."""
        self.run_python(self.skill / "scripts/story.py", self.topic, "--dry", cwd=self.work)
        story = json.loads((self.topic / "story.json").read_text())
        self.assertTrue(story["draft"])
        self.assertEqual(story["timing"], "draft")
        output = self.work / "draft.mp4"
        result = self.run_python(self.skill / "scripts/render_story.py", self.topic / "story.json",
                                 self.scenes(story["duration"]), output, code=1)
        self.assertIn("silent story drafts", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
