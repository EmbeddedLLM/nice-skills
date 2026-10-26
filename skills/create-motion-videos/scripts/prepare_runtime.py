#!/usr/bin/env python3
"""Copy the pinned Lemo source into a writable runtime; optionally install local dependencies."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

SKILL = Path(__file__).resolve().parents[1]
SOURCE = SKILL / 'assets/lemo'
MANIFEST = SKILL / 'references/upstream-manifest.json'


def run(args: list[str], cwd: Path) -> None:
    print('+ ' + ' '.join(args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination', type=Path, help='New writable runtime directory outside this skill')
    p.add_argument('--reuse', action='store_true', help='Reuse a matching runtime created by this script')
    p.add_argument('--install', choices=['render', 'core', 'voice', 'music'],
                   help='Install only local project dependencies. Requires network and existing system tools.')
    p.add_argument('--skip-browser-download', action='store_true',
                   help='Use an existing Chromium set with PLAYWRIGHT_CHROME')
    p.add_argument('--python', default=sys.executable, help='Python 3.11+ interpreter for the runtime venv')
    args = p.parse_args()
    dest = args.destination.expanduser().resolve()
    if dest == SKILL or SKILL in dest.parents:
        p.error('Choose a runtime outside the installed skill; the bundled source stays read-only.')
    manifest = json.loads(MANIFEST.read_text())
    bundle_digest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    stamp = dest / '.motion-runtime.json'
    if dest.exists() and any(dest.iterdir()):
        if not args.reuse or not stamp.is_file():
            p.error('Destination is not empty. Choose a new directory, or use --reuse on a matching runtime.')
        old = json.loads(stamp.read_text())
        if old.get('upstream_commit') != manifest['commit'] or old.get('bundle_digest') != bundle_digest:
            p.error('Runtime has another source revision or bundle patch. Use a new directory; existing projects are preserved.')
        print('Reusing runtime: ' + str(dest))
    else:
        for item in manifest['included']:
            source_file = SOURCE / item['path']
            digest = hashlib.sha256(source_file.read_bytes()).hexdigest()
            if digest != item['sha256']:
                raise RuntimeError('Bundled source differs from its manifest: ' + item['path'])
        shutil.copytree(SOURCE, dest, dirs_exist_ok=True)
        stamp.write_text(json.dumps({'upstream_commit': manifest['commit'],
                                    'source': manifest['repository'], 'creator': 'create-motion-videos', 'bundle_digest': bundle_digest}, indent=2)+'\n')
        print('Prepared runtime: ' + str(dest))
    if args.install:
        for tool in ['node', 'npm', 'ffmpeg']:
            if not shutil.which(tool):
                raise RuntimeError(f'Missing system tool: {tool}. Install it through the host-approved mechanism.')
        major = int(subprocess.check_output(['node', '-p', 'process.versions.node.split(".")[0]'], text=True))
        if major < 20:
            raise RuntimeError('Node 20 or newer is required.')
        run(['npm', 'ci', '--no-audit', '--no-fund'], dest)
        if not args.skip_browser_download:
            run(['node', 'node_modules/playwright-core/cli.js', 'install', 'chromium-headless-shell'], dest)
        if args.install != 'render':
            version = json.loads(subprocess.check_output([args.python, '-c',
                'import json,sys;print(json.dumps(list(sys.version_info[:2])))'], text=True))
            if version < [3, 11] or (args.install == 'voice' and version >= [3, 14]):
                raise RuntimeError('Use Python 3.11+; the current Kokoro tier requires Python 3.11–3.13.')
            venv = dest / '.venv'
            if not venv.exists():
                run([args.python, '-m', 'venv', str(venv)], dest)
            py = venv / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
            # Keep the upstream snapshot immutable; the portable wrapper owns
            # installation pins and excludes the optional online TTS provider.
            reqs = [SKILL / 'requirements/core.txt']
            if args.install in {'voice', 'music'}:
                reqs.append(SKILL / f'requirements/{args.install}.txt')
            run([str(py), '-m', 'pip', 'install', '--disable-pip-version-check',
                 *[arg for name in reqs for arg in ['-r', str(name)]]], dest)
            if args.install == 'voice':
                run(['sh', 'tools/fetch.sh', 'voice'], dest)
    print(json.dumps({'runtime': str(dest), 'upstream_commit': manifest['commit'],
                      'installed_tier': args.install, 'next': 'Read references/runtime.md for render and audio commands.'}))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
