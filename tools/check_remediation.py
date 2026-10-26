#!/usr/bin/env python3
"""Check the issue 6 replacement scope against an explicit source corpus.

This is a regression signal, not a license detector. Exact-content exceptions
require a written review reason; changing an excepted file reopens the review.
Use --corpus for a locally available external corpus. CI runs synthetic tests only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import measure_similarity as similarity

ROOT = Path(__file__).resolve().parents[1]


def audit(local: Path, corpora: list[Path], manifest: dict) -> dict:
    local = local.resolve()
    thresholds = manifest['thresholds']
    for key in ('difflib', 'shingle'):
        value = thresholds[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f'{key} threshold must be a finite number between 0 and 1')
    paths = manifest['files'] + manifest.get('supporting_files', [])
    if not paths or len(set(paths)) != len(paths):
        raise ValueError('audit paths must be nonempty and unique')
    selected = set()
    for name in paths:
        path = (local / name).resolve()
        if Path(name).is_absolute() or not path.is_relative_to(local) or not path.is_file():
            raise ValueError(f'not a file inside the skill root: {name}')
        selected.add(path)
    reviews = manifest.get('reviewed_matches', {})
    if set(reviews) - set(paths):
        raise ValueError('reviewed matches must belong to the audit scope')
    for name, review in reviews.items():
        if not review.get('reason', '').strip():
            raise ValueError(f'missing review reason: {name}')
        if hashlib.sha256((local / name).read_bytes()).hexdigest() != review['sha256']:
            raise ValueError(f'reviewed content changed; re-review required: {name}')
    corpus = []
    if not corpora:
        raise ValueError('at least one corpus is required')
    for root in corpora:
        if not root.is_dir():
            raise ValueError(f'not a corpus directory: {root}')
        entries = similarity.collect_files(root.resolve())
        if not entries:
            raise ValueError(f'empty corpus: {root}')
        corpus.extend(entries)
    corpus = [entry for entry in corpus if entry.path not in selected]
    if not corpus:
        raise ValueError('empty effective corpus after excluding audited files')
    files = [entry for entry in similarity.collect_files(local) if entry.path in selected]
    if len(files) != len(selected):
        raise ValueError('one or more audited files could not be read')
    matches = similarity.scan(
        files, corpus, min_difflib=thresholds['difflib'],
        min_shingle=thresholds['shingle'], candidate_shingle=0.15,
        include_noise=True,
    )
    rows = []
    for match in matches:
        name = match.entry.path.relative_to(local).as_posix()
        review = reviews.get(name)
        rows.append({'path': name, 'identical': match.identical is not None,
                     'difflib': round(match.difflib, 4), 'shingle': round(match.shingle, 4),
                     'reviewed': review is not None, 'reason': review['reason'] if review else None})
    return {'files_checked': len(files), 'corpus_files': len(corpus), 'matches': rows,
            'unreviewed_matches': sum(not r['reviewed'] for r in rows)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', type=Path, default=ROOT / 'skills')
    parser.add_argument('--corpus', type=Path, action='append', required=True)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'tools/remediation.json')
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text())
        result = audit(args.local, args.corpus, manifest)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 1 if result['unreviewed_matches'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
