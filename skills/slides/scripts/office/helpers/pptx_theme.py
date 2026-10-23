"""Detect shared master themes using the supplied compatibility checks."""
import re
from defusedxml import ElementTree as ET
from . import opc_target

P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
THEME_REL_TYPE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme'
_NOTES_MASTERS = 'ppt/notesMasters/'
_MASTER = re.compile(r'ppt/(slideMasters|notesMasters|handoutMasters)/[^/]+\.xml')


def _shares(files):
    owners = {}
    order = {'slideMasters':0,'notesMasters':1,'handoutMasters':2}
    masters = sorted((n for n in files if _MASTER.fullmatch(n)),key=lambda n:(order[n.split('/')[1]],n))
    for master in masters:
        directory,name = master.rsplit('/',1)
        rels = files.get(f'{directory}/_rels/{name}.rels')
        if rels is None:
            continue
        for rel in ET.fromstring(rels):
            if rel.get('Type') != THEME_REL_TYPE:
                continue
            target = opc_target(rel.get('Target',''),master,rel.get('TargetMode',''))
            if target not in files:
                continue
            if target in owners:
                yield master, f'{master} shares {target} with {owners[target]}'
            else:
                owners[target] = master


def find_shared_master_themes(files):
    return [message for _,message in _shares(files)]


def live_shared_master_themes(files):
    data = files.get('ppt/presentation.xml')
    children = list(ET.fromstring(data)) if data else []
    inert_notes = any(a.tag==P+'sldIdLst' and b.tag==P+'notesMasterIdLst' for a,b in zip(children,children[1:]))
    return [message for master,message in _shares(files) if not (inert_notes and master.startswith(_NOTES_MASTERS))]
