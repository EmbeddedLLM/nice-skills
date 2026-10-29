#!/usr/bin/env python3
"""List, render, or sequence bundled procedural sounds without models or network."""
import argparse
import importlib
import json
import math
import os
from pathlib import Path
import tempfile

import numpy as np
from scipy.io import wavfile

from earshot_forge import dsp

ROOT = Path(__file__).resolve().parents[1]
RATE = 48000


def bank():
    return json.loads((ROOT / 'assets/sounds.json').read_text())


def finite(value, label):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f'{label} must be finite')
    return value


def render(identifier, seed=None):
    entries = bank()
    if identifier not in entries:
        raise ValueError(f'Unknown sound: {identifier}; use list')
    entry = entries[identifier]
    module = importlib.import_module('earshot_forge.recipes.' + entry['recipe'])
    selected_seed = entry['seed'] if seed is None else int(seed)
    samples = getattr(module, entry['fn'])(dict(entry['params']), dsp.rng(selected_seed))
    samples = dsp.normalize(samples, entry['peak_db'])
    samples = np.asarray(samples * entry.get('gain', 10 ** (entry.get('gain_db', 0) / 20)), dtype=np.float32)
    if samples.ndim == 1:
        samples = np.column_stack((samples, samples))
    if samples.ndim != 2 or samples.shape[1] != 2 or not len(samples) or not np.isfinite(samples).all():
        raise ValueError('Recipe returned invalid audio')
    return samples, selected_seed


def mix(plan):
    duration = finite(plan['duration'], 'duration')
    if duration <= 0:
        raise ValueError('duration must be positive')
    cues = plan['cues']
    if not isinstance(cues, list) or not cues:
        raise ValueError('cues must be a nonempty list')
    output = np.zeros((round(duration * RATE), 2), dtype=np.float32)
    report = []
    for cue in cues:
        samples, seed = render(cue['id'], cue.get('seed'))
        align = cue.get('align', 'start')
        if align not in ('start', 'peak'):
            raise ValueError('align must be start or peak')
        # The actual rendered waveform is the alignment authority, including a changed seed.
        anchor = int(np.argmax(np.max(np.abs(samples), axis=1))) if align == 'peak' else 0
        at = finite(cue['at'], 'cue time')
        start = round(at * RATE) - anchor
        end = start + len(samples)
        if start < 0 or end > len(output):
            raise ValueError(f"Cue {cue['id']} extends outside the mix; add pre-roll or tail time")
        gain = finite(cue.get('gain_db', 0), 'gain_db')
        if not -120 <= gain <= 24:
            raise ValueError('gain_db must be between -120 and 24')
        output[start:end] += samples * (10 ** (gain / 20))
        report.append({'id': cue['id'], 'seed': seed, 'start': start / RATE,
                       'anchor': (start + anchor) / RATE, 'align': align})
    return output, report


def save(path, samples, force=False):
    if path.suffix.lower() != '.wav':
        raise ValueError('output must end in .wav')
    if path.exists() and not force:
        raise ValueError('output exists; use --force to replace it')
    peak = float(np.max(np.abs(samples)))
    if not np.isfinite(samples).all() or peak > 1:
        raise ValueError('audio is nonfinite or clips; lower cue gain_db')
    path.parent.mkdir(parents=True, exist_ok=True)
    # Complete encoding before publishing, so an encoder failure preserves prior output.
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix='.wav', delete=False) as temporary:
        staged = Path(temporary.name)
    try:
        wavfile.write(staged, RATE, np.round(samples * 32767).astype(np.int16))
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)
    return {'output': str(path), 'sample_rate': RATE, 'channels': 2,
            'frames': len(samples), 'duration': len(samples) / RATE, 'sample_peak': peak}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    listing = sub.add_parser('list')
    listing.add_argument('--query', default='')
    rendering = sub.add_parser('render')
    rendering.add_argument('id')
    rendering.add_argument('--seed', type=int)
    mixing = sub.add_parser('mix')
    mixing.add_argument('plan', type=Path)
    for command in (rendering, mixing):
        command.add_argument('output', type=Path)
        command.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'list':
            print(json.dumps([{'id': key, 'seconds': row['meta']['dur_s']}
                              for key, row in bank().items() if args.query.casefold() in key.casefold()], indent=2))
            return
        if args.command == 'render':
            samples, seed = render(args.id, args.seed)
            result = save(args.output, samples, args.force)
            result.update(id=args.id, seed=seed)
        else:
            if args.plan.resolve() == args.output.resolve():
                raise ValueError('output must differ from the plan')
            samples, cues = mix(json.loads(args.plan.read_text()))
            result = save(args.output, samples, args.force)
            result['cues'] = cues
        print(json.dumps(result, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f'error: {error}\n')


if __name__ == '__main__':
    main()
