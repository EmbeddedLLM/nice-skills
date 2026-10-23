#!/usr/bin/env python3
"""Search the bundled prompt libraries for code-rendered video styles and briefs.

Two libraries ship with this skill, both under assets/prompt-library/:

  opus55-videos   community prompts for HTML/Canvas/SVG/WebGL video, each attributed to its creator
  mg-styles-15    fifteen motion-design style prompts written around a fixed 10-second output spec

Run without arguments for the usage summary. Standard library only; no network access.
"""
import argparse
import json
from pathlib import Path
import sys

SKILL = Path(__file__).resolve().parents[1]
LIBRARY_DIR = SKILL / 'assets' / 'prompt-library'
LIBRARIES = ('opus55-videos', 'mg-styles-15')


def load(name):
    path = LIBRARY_DIR / f'{name}.json'
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        raise SystemExit(f'Missing prompt library: {path}. Copy the whole skill directory.')
    except json.JSONDecodeError as error:
        raise SystemExit(f'Unreadable prompt library {path}: {error}')
    if data.get('library') != name or not data.get('items'):
        raise SystemExit(f'Prompt library {path} is not a {name} record set.')
    return data


def haystack(name, item):
    fields = ('id', 'title', 'author', 'category', 'reference_film', 'prompt')
    if name == 'opus55-videos':
        fields += ('techniques',)
    parts = [item.get(k, '') for k in fields]
    return ' '.join(p if isinstance(p, str) else ' '.join(p) for p in parts).casefold()


def summary(name, item):
    if name == 'mg-styles-15':
        head = f"{item['id']:<16} {item.get('title', '')}"
        note = item.get('reference_film', '')
        return f'{head}\n{"":16} {note}'.rstrip() if note else head
    tags = ','.join(item.get('techniques', []))
    flag = '' if item.get('prompt_complete', True) else '  [original post only]'
    preview = ' '.join(item['prompt'].split())[:110]
    return f"{item['id']:<26} {item['category']:<11} {tags:<26} @{item['author']}{flag}\n{'':26} {preview}…"


def show(name, item):
    lines = [f"{item['id']} — {item.get('title') or item.get('category', '')}".strip()]
    if name == 'opus55-videos':
        lines.append(f"Author: @{item['author']} ({item['author_url']})")
        lines.append(f"Original post: {item['post_url']}")
        lines.append(f"Category: {item['category']} · Techniques: {', '.join(item.get('techniques', [])) or 'none recorded'}")
        if not item.get('prompt_complete', True):
            lines.append('Note: the author published no full prompt; the text below is their original post.')
    else:
        if item.get('reference_film'):
            lines.append(f'Reference film: {item["reference_film"]}')
        lines.append('Spec: the prompt fixes resolution, frame rate, duration, audio and a self-review step; keep them unless the brief says otherwise.')
    return '\n'.join(lines) + '\n\n```text\n' + item['prompt'].rstrip() + '\n```'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command')

    listing = sub.add_parser('list', help='List prompts; filter by library, category, technique or text')
    listing.add_argument('--library', choices=LIBRARIES, action='append', default=[])
    listing.add_argument('--category', default='', help='opus55-videos category: motion, 3d, explainer, interactive')
    listing.add_argument('--technique', default='', help='opus55-videos technique, e.g. shader, threejs, gsap, audio')
    listing.add_argument('--query', default='', help='case-insensitive text match over id, author, title and prompt')
    listing.add_argument('--complete-only', action='store_true', help='skip entries that carry only the original post')
    listing.add_argument('--limit', type=int, default=0, help='print at most N results')
    listing.add_argument('--json', action='store_true')

    one = sub.add_parser('show', help='Print one prompt in full')
    one.add_argument('id')
    one.add_argument('--json', action='store_true')

    sub.add_parser('libraries', help='Report what each library holds')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    if args.command == 'libraries':
        for name in LIBRARIES:
            data = load(name)
            categories = {}
            for item in data['items']:
                if item.get('category'):
                    categories[item['category']] = categories.get(item['category'], 0) + 1
            detail = ', '.join(f'{k} {v}' for k, v in sorted(categories.items())) or 'style prompts'
            print(f'{name}: {len(data["items"])} entries ({detail})')
            print(f'  {data["about"]}')
            print(f'  source: {data["source"]["repository"]} @ {data["source"]["commit"][:12]} ({data["source"]["license"]})')
        return 0

    if args.command == 'show':
        for name in LIBRARIES:
            match = next((item for item in load(name)['items'] if item['id'] == args.id), None)
            if match:
                print(json.dumps(match, ensure_ascii=False, indent=1) if args.json else show(name, match))
                return 0
        print(f'No prompt with id {args.id!r}. Use "list" to find one.', file=sys.stderr)
        return 2

    names = args.library or list(LIBRARIES)
    rows = []
    for name in names:
        for item in load(name)['items']:
            if args.category and item.get('category') != args.category:
                continue
            if args.technique and args.technique.casefold() not in [t.casefold() for t in item.get('techniques', [])]:
                continue
            if args.complete_only and not item.get('prompt_complete', True):
                continue
            if args.query and args.query.casefold() not in haystack(name, item):
                continue
            rows.append((name, item))
    if args.limit:
        rows = rows[:max(args.limit, 0)]
    if args.json:
        print(json.dumps([dict(item, library=name) for name, item in rows], ensure_ascii=False, indent=1))
        return 0
    if not rows:
        print('No prompt matches those filters. Try a shorter query or drop --category/--technique.', file=sys.stderr)
        return 2
    for name, item in rows:
        print(summary(name, item))
        print()
    print(f'{len(rows)} prompt(s). Read one in full with: prompt_library.py show <id>')
    return 0


if __name__ == '__main__':
    sys.exit(main())
