#!/usr/bin/env python3
"""Conservative static asset preflight; browser capture remains authoritative.

Checks literal HTML src/href, CSS url(), ES imports, fetch/load calls and glTF
buffers/images. Dynamic expressions are reported, never assumed to be valid.
"""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

SOURCE_EXT = {'.html', '.css', '.js', '.mjs', '.gltf'}
ASSET_EXT = {'.js', '.mjs', '.css', '.json', '.ttf', '.otf', '.woff', '.woff2', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif', '.hdr', '.exr', '.gltf', '.glb', '.bin', '.wav', '.mp3', '.mp4', '.wasm'}

def inspect(root, library):
    root, library = root.resolve(), library.resolve()
    references, missing, dynamic, external = [], [], [], []
    for file in sorted(root.rglob('*')):
        if not file.is_file() or file.suffix not in SOURCE_EXT or 'node_modules' in file.parts:
            continue
        text = file.read_text(errors='replace')
        items = []
        for m in re.finditer(r'''url\(\s*(['"]?)([^)'"\s]+)\1\s*\)''', text):
            items.append((m.group(2), 'css'))
        if file.suffix == '.html':
            items += [(m.group(2), 'html') for m in re.finditer(r'''(?:src|href)\s*=\s*(['"])(.*?)\1''', text)]
        for m in re.finditer(r'''(?:\bfrom\s*|\bimport\s*\(?\s*)(['"])([^'"\n]+)\1''', text):
            items.append((m.group(2), 'import'))
        for m in re.finditer(r'''(?:\bfetch|\.loadAsync|\.load)\s*\(\s*(['"`])([^'"`\n]+)\1''', text):
            items.append((m.group(2), 'document'))
        if file.suffix == '.gltf':
            try:
                data = json.loads(text)
                items += [(x['uri'], 'gltf') for k in ['images', 'buffers'] for x in data.get(k, []) if 'uri' in x]
            except ValueError:
                pass
        for value, kind in items:
            record = {'source': str(file.relative_to(root)), 'url': value, 'kind': kind}
            if '${' in value or '{{' in value:
                dynamic.append(record); continue
            if value.startswith(('data:', 'blob:', '#')):
                continue
            if urlsplit(value).scheme or value.startswith('//'):
                external.append(record); continue
            value = unquote(urlsplit(value).path)
            if Path(value).suffix.lower() not in ASSET_EXT:
                continue
            # Bare module imports are resolved by browser import maps/dependencies.
            if kind == 'import' and not value.startswith(('.', '/')):
                dynamic.append(record); continue
            if value.startswith('/'):
                target = library / value.lstrip('/')
            else:
                base = file.parent
                if kind == 'document':
                    # Fetch strings are document-relative. Find the nearest demo/page.
                    while base != root and not (base / 'index.html').is_file():
                        base = base.parent
                target = base / value
            record['resolved'] = str(target.resolve())
            references.append(record)
            if not target.is_file():
                missing.append(record)
    return {'root': str(root), 'literal_references': len(references), 'missing': missing,
            'dynamic_or_bare_imports': dynamic, 'external': external,
            'limitations': 'Literal static checks only. JS-generated paths, import maps, media readiness, glyph coverage and document-relative paths after module reuse require browser validation.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--library', type=Path, default=Path(__file__).resolve().parents[1] / 'assets/lemo')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--strict', action='store_true', help='Exit nonzero for missing literal assets')
    args = parser.parse_args()
    if not args.directory.is_dir():
        parser.error('Directory does not exist')
    result = inspect(args.directory, args.library)
    serialized = json.dumps(result, indent=2) + '\n'
    if args.report:
        args.report.write_text(serialized)
        print(json.dumps({'references': result['literal_references'], 'missing': len(result['missing']), 'dynamic': len(result['dynamic_or_bare_imports']), 'report': str(args.report)}))
    else:
        print(serialized)
    raise SystemExit(1 if args.strict and result['missing'] else 0)

if __name__ == '__main__':
    main()
