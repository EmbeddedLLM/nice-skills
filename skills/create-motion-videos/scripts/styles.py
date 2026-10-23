#!/usr/bin/env python3
"""Search bundled Lemo, twoclipping and OPUSCAR styles."""
import argparse
import json
from pathlib import Path
import sys

SKILL = Path(__file__).resolve().parents[1]

def haystack(r):
    return ' '.join(str(r.get(k,'')) for k in ['id','slug','title','title_zh','category','uses','aliases','description','film','year']).casefold()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    ls=sub.add_parser('list',help='List styles; main excludes the separate OPUSCAR references')
    ls.add_argument('--collection',choices=['main','lemo','twoclipping','opuscar','all'],default='main')
    ls.add_argument('--query',default='')
    ls.add_argument('--json',action='store_true')
    show=sub.add_parser('show',help='Read one guide or reusable OPUSCAR prompt')
    show.add_argument('style')
    show.add_argument('--language',choices=['en','zh'],default='en')
    show.add_argument('--json',action='store_true')
    args=parser.parse_args()
    entries=json.loads((SKILL/'references/catalogue.json').read_text())['entries']
    if args.command=='list':
        if args.collection=='main': entries=[r for r in entries if r['collection']!='opuscar']
        elif args.collection!='all': entries=[r for r in entries if r['collection']==args.collection]
        words=args.query.casefold().split()
        entries=[r for r in entries if all(w in haystack(r) for w in words)]
        if args.json: print(json.dumps(entries,ensure_ascii=False,indent=2))
        else:
            for r in entries:
                print(f"{r['id']}\t{r['title']}\t{r.get('title_zh','')}\t{r['category']}\t{'; '.join(r.get('uses',[]))}")
            print(f'{len(entries)} entries',file=sys.stderr)
        return
    query=args.style.casefold()
    if query.startswith('opuscar:') and query.split(':',1)[1].isdigit(): query='opuscar:'+query.split(':',1)[1].zfill(3)
    exact=[r for r in entries if query in [str(r.get(k,'')).casefold() for k in ['id','slug','title','title_zh']]+[str(a).casefold() for a in r.get('aliases',[])]]
    matches=exact or [r for r in entries if query in haystack(r)]
    if len(matches)!=1:
        parser.error(('No unique match. Use one of: '+', '.join(r['id'] for r in matches[:15])) if matches else 'No match. Try list --query.')
    r=matches[0]
    if args.json: print(json.dumps(r,ensure_ascii=False,indent=2)); return
    print(f"# {r['title']}\n\nID: {r['id']}\nSource: {r['source_url']}\n")
    if r['collection']=='opuscar':
        films=json.loads((SKILL/r['source_path']).read_text())['films']
        f=next(x for x in films if x['no']==r['number'])
        suffix=args.language
        print(f"Renderer: {f['render']}\nReference film: {f['title']} ({f['year']})\n")
        print(f.get('desc_'+suffix,''))
        print('\n## Reusable style prompt\n\n'+f['prompt_'+suffix])
        print('\nUse this grammar for the user\'s own story. Reference shots and compilation timings are not a new-film plan.')
    else:
        print((SKILL/r['guide_path']).read_text())
        if r['collection']=='twoclipping': print('\nSELECTED VARIANT: '+r['variant'])

if __name__=='__main__': main()
