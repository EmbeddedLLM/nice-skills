"""Local media contracts for optional-provider presenter and explainer skills."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from skill_scripts import SKILLS, ScriptCase, require_binary


@require_binary('bash')
@require_binary('ffmpeg')
@require_binary('ffprobe')
@require_binary('jq')
class PresenterSkillTests(ScriptCase):
    def setUp(self):
        super().setUp()
        # An allowlist avoids inheriting provider credentials from developer machines.
        # Use the active test interpreter for Python commands inside the shell smoke.
        self.local_env = {
            'PATH': str(Path(sys.executable).parent) + os.pathsep + os.environ['PATH'],
            'TMPDIR': str(self.work),
            'LC_ALL': 'C.UTF-8',
        }

    def local_run(self, *args, code=0, timeout=180, env=None):
        result = subprocess.run([str(arg) for arg in args], cwd=self.work, env={**self.local_env, **(env or {})},
                                capture_output=True, text=True, timeout=timeout)
        self.assertEqual(result.returncode, code, result.stdout[-4000:] + result.stderr[-4000:])
        return result

    def source_video(self, name='source.mp4', audio='sine=frequency=330:sample_rate=48000', channels=2):
        source = self.work / name
        args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-n',
                '-f', 'lavfi', '-i', 'testsrc2=size=256x320:rate=12']
        if audio:
            args.extend(['-f', 'lavfi', '-i', audio])
        args.extend(['-t', '4', '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p'])
        if audio:
            args.extend(['-c:a', 'aac', '-ac', str(channels)])
        self.local_run(*args, source)
        return source

    def finalizer(self, skill):
        return SKILLS / skill / 'scripts/finalize_delivery.sh'

    def test_standalone_presenter_edits_supplied_footage_without_provider_credentials(self):
        """A copied skill trims local recording streams and delivers checked files without a job schema."""
        installed = self.work / 'installed' / 'presenter-video'
        shutil.copytree(SKILLS / 'presenter-video', installed,
                        ignore=shutil.ignore_patterns('__pycache__'))
        source = self.source_video(channels=1)
        original = source.read_bytes()
        edited = self.work / 'edited.mp4'
        self.local_run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-n', '-i', source,
                       '-ss', '0.5', '-t', '3', '-map', '0:v:0', '-map', '0:a:0',
                       '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                       '-movflags', '+faststart', edited)
        delivery = self.work / 'delivery'
        self.local_run('bash', installed / 'scripts/finalize_delivery.sh', edited, delivery, 'local')
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual({p.name for p in delivery.iterdir()}, {
            'local-master.mp4', 'local-share.mp4', 'local-contact-sheet.png',
            'local-delivery-report.json',
        })
        report_text = (delivery / 'local-delivery-report.json').read_text()
        report = json.loads(report_text)
        self.assertEqual(report['status'], 'verified')
        self.assertTrue(report['full_decode_passed'])
        self.assertTrue(report['loudness_passed'])
        self.assertAlmostEqual(report['duration_s'], 3, delta=0.15)
        self.assertNotIn(str(self.work), report_text)
        for variant in ('master', 'share'):
            output = delivery / f'local-{variant}.mp4'
            self.local_run('ffmpeg', '-hide_banner', '-v', 'error', '-xerror', '-i', output,
                           '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-')
            probe = json.loads(self.local_run('ffprobe', '-v', 'error', '-show_streams',
                                             '-of', 'json', output).stdout)
            self.assertEqual({s['codec_type'] for s in probe['streams']}, {'video', 'audio'})
            self.assertAlmostEqual(float(report[f'{variant}_loudness']['input_i']), -16, delta=0.5)
        self.assertFalse((self.work / 'job.json').exists())

    def test_finalizers_preserve_every_existing_named_output(self):
        """Both standalone finalizers reject each output collision before publishing anything."""
        source = self.source_video()
        original = source.read_bytes()
        for skill in ('presenter-video', 'explainer-video'):
            for suffix in ('master.mp4', 'share.mp4', 'contact-sheet.png', 'delivery-report.json'):
                with self.subTest(skill=skill, suffix=suffix):
                    output = self.work / skill / suffix
                    output.mkdir(parents=True)
                    sentinel = output / f'keep-{suffix}'
                    sentinel.write_bytes(b'pre-existing user output')
                    result = self.local_run('bash', self.finalizer(skill), source, output, 'keep', code=1)
                    self.assertIn('refusing to overwrite', result.stderr)
                    self.assertEqual(list(output.iterdir()), [sentinel])
                    self.assertEqual(sentinel.read_bytes(), b'pre-existing user output')
        self.assertEqual(source.read_bytes(), original)

    def test_finalizers_preserve_dangling_output_symlinks(self):
        """Broken output symlinks count as existing user paths and must remain unchanged."""
        source = self.source_video()
        for skill in ('presenter-video', 'explainer-video'):
            with self.subTest(skill=skill):
                output = self.work / skill
                output.mkdir()
                sentinel = output / 'keep-master.mp4'
                sentinel.symlink_to('missing-user-file')
                result = self.local_run('bash', self.finalizer(skill), source, output, 'keep', code=1)
                self.assertIn('refusing to overwrite', result.stderr)
                self.assertTrue(sentinel.is_symlink())
                self.assertEqual(os.readlink(sentinel), 'missing-user-file')
                self.assertEqual(list(output.iterdir()), [sentinel])

    def test_finalizers_preserve_outputs_created_during_encoding(self):
        """A late output collision preserves that file and withholds the completion report."""
        source = self.source_video()
        real_ffmpeg = shutil.which('ffmpeg')
        for skill in ('presenter-video', 'explainer-video'):
            with self.subTest(skill=skill):
                output = self.work / skill / 'delivery'
                sentinel = output / 'race-share.mp4'
                wrapper_dir = self.work / skill / 'bin'
                wrapper_dir.mkdir(parents=True)
                wrapper = wrapper_dir / 'ffmpeg'
                wrapper.write_text(f'''#!{sys.executable}
import pathlib, subprocess, sys
if '-c:v' in sys.argv and pathlib.Path(sys.argv[-1]).name == 'master.mp4':
    pathlib.Path({str(sentinel)!r}).write_bytes(b'created by another writer')
raise SystemExit(subprocess.call([{real_ffmpeg!r}, *sys.argv[1:]]))
''')
                wrapper.chmod(0o755)
                self.local_run('bash', self.finalizer(skill), source, output, 'race', code=1,
                               env={'PATH': str(wrapper_dir) + os.pathsep + self.local_env['PATH']})
                self.assertEqual(sentinel.read_bytes(), b'created by another writer')
                self.assertTrue((output / 'race-master.mp4').is_file())
                self.assertEqual({path.name for path in output.iterdir()},
                                 {'race-master.mp4', 'race-share.mp4'})

    def test_finalizers_reject_silent_and_missing_audio_without_publication(self):
        """Silent and absent audio cannot produce a misleading verified delivery from either skill."""
        fixtures = [('silent', self.source_video('silent.mp4', 'anullsrc=r=48000:cl=stereo')),
                    ('missing', self.source_video('missing.mp4', audio=None))]
        for skill in ('presenter-video', 'explainer-video'):
            for kind, source in fixtures:
                with self.subTest(skill=skill, kind=kind):
                    original = source.read_bytes()
                    output = self.work / skill / kind
                    result = self.local_run('bash', self.finalizer(skill), source, output, 'invalid', code=1)
                    self.assertIn('silent or unmeasurable' if kind == 'silent' else 'video and audio streams',
                                  result.stderr)
                    self.assertEqual(list(output.iterdir()), [])
                    self.assertEqual(source.read_bytes(), original)

    def test_generated_job_smoke_uses_synthetic_media_without_a_provider(self):
        """The optional generation-job helpers advance only on local evidence; no generation occurs."""
        result = self.local_run('bash', SKILLS / 'presenter-video/tests/smoke.sh')
        self.assertIn('ok - job reaches verified', result.stdout)
