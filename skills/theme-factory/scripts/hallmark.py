#!/usr/bin/env python3
"""Browse 48 Hallmark material recipes and export their CSS tokens locally."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / 'references/hallmark'


def catalog():
    result = []
    for path in sorted(THEMES.glob('*.md')):
        header = path.read_text().split('---', 2)[1]
        fields = dict(line.split(': ', 1) for line in header.splitlines() if ': ' in line)
        fields['file'] = path.name
        result.append(fields)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['list', 'show', 'css'])
    parser.add_argument('slug', nargs='?')
    parser.add_argument('--query', default='')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    entries = catalog()
    if args.command == 'list':
        if args.output:
            parser.error('--output is only supported by css')
        print(json.dumps([r for r in entries if args.query.casefold() in json.dumps(r).casefold()], indent=2))
        return
    selected = next((r for r in entries if r['slug'] == args.slug), None)
    if selected is None:
        parser.error('unknown theme; use list')
    body = (THEMES / selected['file']).read_text()
    if args.command == 'show':
        if args.output:
            parser.error('--output is only supported by css')
        print(body)
        return
    match = re.search(r'## Tokens\s+```css\s*(.*?)```', body, re.S)
    if not match:
        parser.error('theme has no CSS token block')
    css = '/* Adapted from Nutlope/hallmark. Retain LICENSE-hallmark.txt with this export. */\n' + match[1].strip() + '\n'
    if args.output:
        license_path = args.output.with_suffix(args.output.suffix + '.LICENSE.txt')
        if args.output.exists() or license_path.exists():
            parser.error('output or license exists; choose a new path')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(css)
        license_path.write_bytes((ROOT / 'LICENSE-hallmark.txt').read_bytes())
    else:
        print(css, end='')


if __name__ == '__main__':
    main()
