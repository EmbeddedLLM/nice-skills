#!/usr/bin/env python3
"""Offline theme catalog, exports and exact-pair validation. Standard library only."""
import argparse
import collections
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'assets/theme-guide.html'
HEX = re.compile(r'^#[0-9A-Fa-f]{6}$')
SLOTS = ['dk1','lt1','dk2','lt2','accent1','accent2','accent3','accent4','accent5','accent6','hlink','folHlink']
LAVENDER = ['#E7DEFA','#DDF2E5','#FFE3D3','#FFF0BD','#FAF9F6','#FFFFFF','#202334','#676976','#E7E6E2']

def load():
    text = GUIDE.read_text(encoding='utf-8')
    def block(name):
        m = re.search(r'<script\b[^>]*\bid="'+name+r'"[^>]*>(.*?)</script>', text, re.S)
        if not m:
            raise ValueError('Missing guide data block: '+name)
        return json.loads(m[1])
    data, custom = block('theme-data'), block('lavender-ledger-data')
    return data, custom, data['palettes']+[custom['application']]

def luminosity(h):
    if not HEX.fullmatch(h):
        raise ValueError('Expected six-digit HEX: '+h)
    values = [int(h[i:i+2],16)/255 for i in (1,3,5)]
    linear = [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
    return sum(v*w for v,w in zip(linear,[.2126,.7152,.0722]))

def contrast(a,b):
    x,y=luminosity(a),luminosity(b)
    return (max(x,y)+.05)/(min(x,y)+.05)

def select(palettes,query):
    matches=[p for p in palettes if query.casefold() in [str(p[k]).casefold() for k in ('id','slug','display_name')]]
    if len(matches)!=1:
        raise ValueError('Unknown or ambiguous theme: '+query+'. Use list.')
    return matches[0]

def notice(p):
    return p['asset_notice']+'\nReference: '+p.get('source_url','User supplied')+'\n'

def css(p,custom):
    safe=notice(p).replace('*/','* /')
    lines=['/* '+safe+' */', '[data-palette="'+p['slug']+'"] {']
    for k,v in {**p['colors'],**p['web']['tokens']}.items():
        lines.append('  --mca-'+k+': '+v+';')
    if p.get('custom'):
        for c in custom['colours']:
            lines.extend(['  /* '+c['role'].replace('*/','* /')+' */','  --ll-'+c['key']+': '+c['hex']+';'])
    lines += ['}', '', '[data-palette="'+p['slug']+'"] .theme-primary {',
              '  background: var(--mca-action, var(--mca-primary));',
              '  color: var(--mca-on-action, var(--mca-on-primary));',
              '  border: 1px solid var(--mca-border-interactive);','}',
              '[data-palette="'+p['slug']+'"] .theme-primary:hover {',
              '  background: var(--mca-action-hover, var(--mca-primary-hover));',
              '  color: var(--mca-on-action-hover, var(--mca-on-primary-hover));','}',
              '[data-palette="'+p['slug']+'"] .theme-primary:focus-visible {',
              '  outline: 3px solid var(--mca-focus-ring);','  outline-offset: 3px;','}']
    return '\n'.join(lines)+'\n'

def write_all(files,overwrite=False):
    # Preflight every destination before writing any file.
    for path,content in files.items():
        if path.exists() and (not path.is_file() or (path.read_bytes()!=content and not overwrite)):
            raise ValueError('Refusing to overwrite differing file: '+str(path))
    for path,content in files.items():
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists() or path.read_bytes()!=content:
            path.write_bytes(content)

def verify(data,custom,palettes):
    errors=[]
    def check(condition,message):
        if not condition: errors.append(message)
    check(len(data['palettes'])==50 and len(palettes)==51,'Expected 50 themes plus Lavender')
    check(len({p['id'] for p in palettes})==51,'Duplicate IDs')
    check(len({p['slug'] for p in palettes})==51,'Duplicate slugs')
    check(collections.Counter(p['mood_id'] for p in data['palettes'])=={m['id']:5 for m in data['moods']},'Mood coverage')
    check([c['hex'] for c in custom['colours']]==LAVENDER,'Lavender values changed')
    for p in palettes:
        try:
            c,t=p['colors'],p['web']['tokens'];tag=p['id']+' '
            check(set(c)=={'background','surface','text','primary','secondary','accent'},tag+'core roles')
            for k,v in {**c,**t,**p['office']['slots']}.items():
                check(bool(HEX.fullmatch(v)),tag+'invalid HEX '+k)
            canv=[c['background'],c['surface']]
            for k,v in [('text',c['text'])]+[(k,t[k]) for k in ['text-muted','link','link-on-surface','link-hover','link-visited','link-visited-hover']]:
                check(min(contrast(v,b) for b in canv)>=4.5,tag+k+' below 4.5:1')
            for k in ['border-interactive','focus-ring']:
                check(min(contrast(t[k],b) for b in canv)>=3,tag+k+' below 3:1')
            check(contrast(t['on-selected'],t['selected-surface'])>=4.5,tag+'selected text')
            for role in ['primary','secondary','accent']:
                check(contrast(c[role],t['on-'+role])>=4.5,tag+role+' label')
                check(contrast(t[role+'-hover'],t['on-'+role+'-hover'])>=4.5,tag+role+' hover label')
            if 'action' in t:
                check(contrast(t['action'],t['on-action'])>=4.5,tag+'action label')
                check(contrast(t['action-hover'],t['on-action-hover'])>=4.5,tag+'action hover label')
            slots=p['office']['slots']; check(set(slots)==set(SLOTS),tag+'Office slots')
            root=ET.fromstring(p['office']['xml']);ns='{http://schemas.openxmlformats.org/drawingml/2006/main}'
            check(root.tag==ns+'clrScheme',tag+'XML root')
            actual={e.tag.split('}')[-1]:'#'+e.find(ns+'srgbClr').attrib['val'].upper() for e in root}
            check(actual=={k:v.upper() for k,v in slots.items()},tag+'XML/slot mismatch')
            if p.get('custom'):
                check(set([*c.values(),*t.values(),*slots.values()])<=set(LAVENDER),tag+'added custom shade')
        except (KeyError,ValueError,TypeError,ET.ParseError,AttributeError) as e:
            errors.append(p.get('id','unknown')+' malformed record: '+str(e))
    if errors:
        raise ValueError('\n'.join(errors))
    return {'themes':len(palettes),'moods':len(data['moods']),'status':'passed','scope':'Opaque colour pairs and XML structure; inspect rendered artifacts separately.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    q=commands.add_parser('list');q.add_argument('--mood');q.add_argument('--json',action='store_true')
    q=commands.add_parser('show');q.add_argument('theme')
    q=commands.add_parser('export');q.add_argument('theme',nargs='?');q.add_argument('--all',action='store_true');q.add_argument('--format',choices=['web','office','both','json'],default='both');q.add_argument('--out',type=Path,required=True);q.add_argument('--overwrite',action='store_true')
    q=commands.add_parser('guide');q.add_argument('--out',type=Path,required=True);q.add_argument('--overwrite',action='store_true')
    q=commands.add_parser('contrast');q.add_argument('foreground');q.add_argument('background')
    commands.add_parser('verify')
    args=parser.parse_args()
    if args.command=='contrast':
        v=contrast(args.foreground,args.background);print(json.dumps({'ratio':v,'normal_text_4_5':v>=4.5,'non_text_3':v>=3}));return
    data,custom,palettes=load()
    if args.command=='list':
        if args.mood and args.mood not in {m['id'] for m in data['moods']}:raise ValueError('Unknown mood: '+args.mood)
        rows=[dict(id=p['id'],name=p['display_name'],mood=p['mood_id'],primary_button=p['web']['tokens'].get('action',p['colors']['primary'])) for p in palettes if not args.mood or p['mood_id']==args.mood]
        if args.json:print(json.dumps(rows,indent=2))
        else:
            for r in rows:print('{id:7} {mood:12} {primary_button}  {name}'.format(**r))
    elif args.command=='show':
        p=dict(select(palettes,args.theme))
        if p.get('custom'):p['supplied_colours']=custom['colours']
        print(json.dumps(p,indent=2))
    elif args.command=='verify':print(json.dumps(verify(data,custom,palettes),indent=2))
    elif args.command=='guide':
        write_all({args.out:GUIDE.read_bytes()},args.overwrite);print(args.out.resolve())
    elif args.command=='export':
        if bool(args.theme)==bool(args.all):raise ValueError('Specify exactly one theme or --all')
        chosen=palettes if args.all else [select(palettes,args.theme)]
        files={}
        for p in chosen:
            base=args.out/(p['id']+'-'+p['slug']) if args.all else args.out
            record=dict(p)
            if p.get('custom'):record['supplied_colours']=custom['colours']
            files[base/'theme.json']=json.dumps(record,indent=2).encode()+b'\n'
            files[base/'SOURCE.txt']=notice(p).encode()
            if args.format in ['web','both']:files[base/'theme.css']=css(p,custom).encode()
            if args.format in ['office','both']:files[base/'theme.xml']=p['office']['xml'].encode()
        write_all(files,args.overwrite);print(json.dumps({'themes':len(chosen),'files':len(files),'directory':str(args.out.resolve())}))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError) as error:
        print('Error: '+str(error),file=sys.stderr);sys.exit(1)
