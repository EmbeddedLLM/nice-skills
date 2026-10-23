#!/usr/bin/env python3
"""Duplicate a slide or instantiate a layout, preserving package registration.

Packed inputs require -o NEW_FILE; unpacked working directories are edited in
place. Duplicates omit notes and share charts/media with the source slide.
Uses namespace-aware XML.
"""
import argparse
from pathlib import Path
import re
import tempfile
import zipfile
from lxml import etree as ET
from office.helpers import opc_target, safe_extract, rezip, SLIDE_REL_TYPE

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'


def read(path):
    tree = ET.parse(str(path), ET.XMLParser(resolve_entities=False, no_network=True))
    if tree.docinfo.doctype:
        raise ValueError(f'DTD is not supported: {path}')
    return tree


def write(tree, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(path), encoding='UTF-8', xml_declaration=True, standalone=True)


def add_slide(root, source, after=None):
    root = Path(root)
    if not re.fullmatch(r'slide(?:Layout)?[1-9][0-9]*\.xml', source):
        raise ValueError('Source must be slideN.xml or slideLayoutN.xml')
    layout = source.startswith('slideLayout')
    source_path = root/'ppt'/('slideLayouts' if layout else 'slides')/source
    slide = read(source_path)
    pres_path, rels_path, ct_path = (root/'ppt/presentation.xml', root/'ppt/_rels/presentation.xml.rels', root/'[Content_Types].xml')
    pres, rels, ct = read(pres_path), read(rels_path), read(ct_path)
    ids = pres.getroot().find(f'{{{P}}}sldIdLst')
    if ids is None:
        ids = ET.Element(f'{{{P}}}sldIdLst')
        masters = pres.getroot().find(f'{{{P}}}sldMasterIdLst')
        pres.getroot().insert(list(pres.getroot()).index(masters)+1 if masters is not None else 0, ids)
    slide_rels = {r.get('Id'): opc_target(r.get('Target',''), 'ppt/presentation.xml', r.get('TargetMode',''))
                  for r in rels.getroot() if r.get('Type') == SLIDE_REL_TYPE}
    position = len(ids)
    if after:
        matches = [i for i, e in enumerate(ids) if slide_rels.get(e.get(f'{{{R}}}id')) == f'ppt/slides/{after}']
        if len(matches) != 1:
            raise ValueError(f'--after slide is not listed exactly once: {after}')
        position = matches[0]+1
    occupied = {p.name for p in (root/'ppt/slides').glob('slide*.xml')}
    occupied |= {Path(r).name for r in slide_rels.values() if r}
    occupied |= {Path(e.get('PartName','')).name for e in ct.getroot()}
    n = 1
    while f'slide{n}.xml' in occupied:
        n += 1
    name = f'slide{n}.xml'
    used_ids = {int(e.get('id')) for e in ids}
    sid = max(used_ids | {255})+1
    if sid > 2147483647:
        raise ValueError('Slide ID range exhausted')
    used_rids = {e.get('Id') for e in rels.getroot()}
    i = 1
    while f'rId{i}' in used_rids:
        i += 1
    rid = f'rId{i}'
    new_rels = ET.ElementTree(ET.Element(f'{{{PKG}}}Relationships', nsmap={None: PKG}))
    if layout:
        # A minimal slide inherits its visual background from the selected layout.
        sld = ET.Element(f'{{{P}}}sld', nsmap={'p':P, 'a':A, 'r':R})
        tree = ET.SubElement(ET.SubElement(sld, f'{{{P}}}cSld'), f'{{{P}}}spTree')
        nv = ET.SubElement(tree, f'{{{P}}}nvGrpSpPr')
        ET.SubElement(nv, f'{{{P}}}cNvPr', id='1', name='')
        ET.SubElement(nv, f'{{{P}}}cNvGrpSpPr')
        ET.SubElement(nv, f'{{{P}}}nvPr')
        ET.SubElement(tree, f'{{{P}}}grpSpPr')
        ET.SubElement(ET.SubElement(sld, f'{{{P}}}clrMapOvr'), f'{{{A}}}masterClrMapping')
        slide = ET.ElementTree(sld)
        ET.SubElement(new_rels.getroot(), f'{{{PKG}}}Relationship', Id='rId1',
                      Type=R+'/slideLayout', Target='../slideLayouts/'+source)
    else:
        original_rels = root/'ppt/slides/_rels'/f'{source}.rels'
        if original_rels.exists():
            new_rels = read(original_rels)
            for rel in list(new_rels.getroot()):
                if rel.get('Type','').endswith('/notesSlide'):
                    new_rels.getroot().remove(rel)
            shared = [r.get('Type','').rsplit('/',1)[-1] for r in new_rels.getroot()
                      if r.get('Type','').rsplit('/',1)[-1] in ('chart','diagramData','oleObject','package')]
            if shared:
                print('Shared parts (editing affects both slides): '+', '.join(sorted(set(shared))))
    ET.SubElement(ct.getroot(), f'{{{CT}}}Override', PartName='/ppt/slides/'+name,
                  ContentType='application/vnd.openxmlformats-officedocument.presentationml.slide+xml')
    ET.SubElement(rels.getroot(), f'{{{PKG}}}Relationship', Id=rid, Type=SLIDE_REL_TYPE, Target='slides/'+name)
    elem = ET.Element(f'{{{P}}}sldId', id=str(sid)); elem.set(f'{{{R}}}id', rid)
    ids.insert(position, elem)
    # All parsing and preflight complete before the first write.
    for tree, path in [(slide,root/'ppt/slides'/name), (new_rels,root/'ppt/slides/_rels'/f'{name}.rels'),
                       (ct,ct_path),(rels,rels_path),(pres,pres_path)]:
        write(tree,path)
    return name


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('target', type=Path); p.add_argument('source')
    p.add_argument('--after'); p.add_argument('-o','--output',type=Path)
    a = p.parse_args()
    try:
        if a.target.is_dir():
            if a.output:
                p.error('Directory input is edited in place; omit --output')
            if any(x.is_symlink() for x in a.target.rglob('*')):
                raise ValueError('Unpacked inputs must not contain symlinks')
            name = add_slide(a.target,a.source,a.after)
        else:
            if not a.output or a.output.exists() or a.output.is_symlink():
                p.error('Packed input requires --output with a new path')
            with tempfile.TemporaryDirectory() as tmp:
                with zipfile.ZipFile(a.target) as z:
                    safe_extract(z,Path(tmp))
                name = add_slide(Path(tmp),a.source,a.after)
                rezip(Path(tmp),a.output)
        print(f'Created ppt/slides/{name}')
    except Exception as exc:
        p.exit(1,f'Error: {exc}\n')


if __name__ == '__main__':
    main()
