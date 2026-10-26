#!/usr/bin/env python3
"""Create an original-film starter with an intact selected style resource tree."""
import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--style', required=True, help='Lemo style slug, for example whiteboard')
    args = parser.parse_args()
    source = ROOT / 'assets/lemo/styles' / args.style
    if '/' in args.style or '\\' in args.style or not (source / 'STYLE.md').is_file():
        parser.error('Unknown Lemo style slug')
    dest = args.destination.expanduser().resolve()
    if dest == ROOT or ROOT in dest.parents:
        parser.error('Use a project directory outside the skill')
    if dest.exists() and (not dest.is_dir() or any(p.name != 'TREATMENT.md' or not p.is_file() for p in dest.iterdir())):
        parser.error('Destination must be empty or contain only TREATMENT.md; existing project files are never overwritten')
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / 'assets/browser-starter/index.html', dest / 'index.html')
    # Retain the browser resource tree (omit repository-bound build/tools): JS module imports, CSS URLs, fetch paths,
    # engines and stroke-font JSON must not be flattened or merged by basename.
    if (source / 'demo').is_dir():
        shutil.copytree(source / 'demo', dest / 'style', dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('tools', 'build.sh', '__pycache__'))
    shutil.copy2(source / 'STYLE.md', dest / 'STYLE.md')
    shutil.copy2(ROOT / 'assets/lemo/LICENSE', dest / 'LEMO-LICENSE')
    (dest / 'motion-project.json').write_text(json.dumps({
        'style': args.style, 'style_resources': 'style/',
        'runtime_required': True,
        'instructions': 'Author index.html for the new treatment. Import style modules from ./style/. Root-relative /core/ and /styles/ URLs require the Lemo server. Document-relative fetch URLs inside copied modules must be rebased to ./style/ or new URL(..., import.meta.url). The copied demo is reference code, not the new film. Run audit_assets.py on the project and render.mjs --check-only before export.'
    }, indent=2) + '\n')
    print(json.dumps({'project': str(dest), 'style': args.style, 'starter': 'index.html', 'resources': 'style/'}))

if __name__ == '__main__':
    main()
