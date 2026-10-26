#!/usr/bin/env python3
"""Prune unreachable PPTX parts after changing the presentation slide list.

Default: report planned removals. Use --apply on an unpacked working copy,
or --output NEW.pptx on a packed input. Walks package relationships, including
cycles and shared resources; refuses dangling live references before mutation.
"""
import argparse
from pathlib import Path, PurePosixPath
import tempfile
import zipfile
from lxml import etree as ET
from office.helpers import opc_target, safe_extract, rezip, SLIDE_REL_TYPE
from add_slide import read, write, P, R


def cleanup_plan(root):
    root = Path(root)
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('Unpacked inputs must not contain symlinks')
    pres = read(root/'ppt/presentation.xml')
    relpath = 'ppt/_rels/presentation.xml.rels'
    rels = read(root/relpath)
    ids = {e.get(f'{{{R}}}id') for e in pres.findall(f'{{{P}}}sldIdLst/{{{P}}}sldId')}
    available = {r.get('Id') for r in rels.getroot() if r.get('Type') == SLIDE_REL_TYPE}
    if not ids <= available:
        raise ValueError('Slide list has missing relationships')
    for r in list(rels.getroot()):
        if r.get('Type') == SLIDE_REL_TYPE and r.get('Id') not in ids:
            rels.getroot().remove(r)
    live = {'[Content_Types].xml'}
    pending = [('', '_rels/.rels')]
    while pending:
        owner, relationship_part = pending.pop()
        if relationship_part in live:
            continue
        path = root/relationship_part
        if not path.exists():
            if not owner:
                raise ValueError('Missing package relationships')
            continue
        live.add(relationship_part)
        tree = rels if relationship_part == relpath else read(path)
        seen = set()
        for rel in tree.getroot():
            rid = rel.get('Id')
            if not rid or rid in seen:
                raise ValueError(f'Duplicate/missing relationship ID in {relationship_part}')
            seen.add(rid)
            target = opc_target(rel.get('Target',''),owner,rel.get('TargetMode',''))
            if target is None:
                continue
            if not (root/target).is_file():
                raise ValueError(f'Dangling relationship: {owner} -> {target}')
            if target not in live:
                live.add(target)
                part = PurePosixPath(target)
                pending.append((target,str(part.parent/'_rels'/(part.name+'.rels'))))
    if 'ppt/presentation.xml' not in live:
        raise ValueError('Package relationships do not reach the presentation')
    removed = sorted(p.relative_to(root).as_posix() for p in root.rglob('*')
                     if p.is_file() and p.relative_to(root).as_posix() not in live)
    ct = read(root/'[Content_Types].xml')
    for e in list(ct.getroot()):
        if e.get('PartName','').lstrip('/') in removed:
            ct.getroot().remove(e)
    return removed, rels, ct


def clean_unused_files(root, apply=False):
    removed, rels, ct = cleanup_plan(root)
    if apply:
        write(rels,root/'ppt/_rels/presentation.xml.rels')
        write(ct,root/'[Content_Types].xml')
        for name in removed:
            (root/name).unlink()
    return removed


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('target',type=Path); p.add_argument('--apply',action='store_true')
    p.add_argument('-o','--output',type=Path)
    a = p.parse_args()
    try:
        if a.target.is_dir():
            if a.output:
                p.error('Use --apply for directory input')
            removed = clean_unused_files(a.target,a.apply)
        else:
            if a.apply:
                p.error('Use --output for packed input')
            if a.output and (a.output.exists() or a.output.is_symlink()):
                p.error('Choose a new output path')
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with zipfile.ZipFile(a.target) as z:
                    safe_extract(z,root)
                removed = clean_unused_files(root,bool(a.output))
                if a.output:
                    rezip(root,a.output)
        print(('Removed' if a.apply or a.output else 'Would remove')+f' {len(removed)} parts:')
        print('\n'.join(removed))
    except Exception as exc:
        p.exit(1,f'Error: {exc}\n')


if __name__ == '__main__':
    main()
