#!/usr/bin/env python3
"""Verify pinned source hashes and complete style coverage after an update."""
from pathlib import Path
import hashlib
import json
import sys
from audit_assets import inspect

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'references/upstream-manifest.json').read_text())
catalogue=json.loads((root/'references/catalogue.json').read_text())
errors=[]
for f in manifest['included']:
    p=root/'assets/lemo'/f['path']
    if not p.is_file(): errors.append('Missing source: '+f['path']); continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=f['sha256']: errors.append('Changed source: '+f['path'])
lemo=[x for x in catalogue['entries'] if x['collection']=='lemo']
actual={p.parent.name for p in (root/'assets/lemo/styles').glob('*/STYLE.md') if p.parent.name!='_template'}
if {x['slug'] for x in lemo}!=actual: errors.append('Main style catalogue coverage mismatch.')
if len(lemo)!=manifest['main_style_count']: errors.append('Main style count mismatch.')
opus=json.loads((root/'assets/lemo/styleboard/opuscar98_styles.json').read_text())['films']
entries=[x for x in catalogue['entries'] if x['collection']=='opuscar']
if len(opus)!=manifest['opuscar_reference_count']: errors.append('OPUSCAR count mismatch.')
if {x['number'] for x in entries}!={x['no'] for x in opus}: errors.append('OPUSCAR catalogue coverage mismatch.')
if any(not x.get('prompt_en') or not x.get('prompt_zh') for x in opus): errors.append('OPUSCAR language missing.')
if {x.get('variant') for x in catalogue['entries'] if x['collection']=='twoclipping'}!={'ui-morph','product-launch'}: errors.append('Twoclipping variants incomplete.')
ids=[x['id'] for x in catalogue['entries']]
if len(ids)!=len(set(ids)): errors.append('Duplicate catalogue IDs.')
for r in catalogue['entries']:
    for key in ['guide_path','source_path']:
        if r.get(key) and not (root/r[key]).is_file(): errors.append('Missing reference: '+r[key])
for name in ['SKILL.md','agents/openai.yaml','references/workflow.md','references/runtime.md','references/browser-renderer.md','references/style-index.md','references/opuscar98-index.md','references/twoclipping.md','references/sources-and-licenses.md','assets/lemo/LICENSE','assets/browser-starter/index.html','scripts/render.mjs']:
    if not (root/name).is_file(): errors.append('Required file absent: '+name)
# Check live font URLs and glTF external buffers/images, independently of hashes.
asset_check = inspect(root/'assets/lemo', root/'assets/lemo')
critical_missing = [x for x in asset_check['missing'] if x['kind']=='gltf' or Path(x['url']).suffix.lower() in {'.ttf','.otf','.woff','.woff2'}]
for item in critical_missing:
    errors.append('Missing font/model dependency: '+item['source']+' -> '+item['url'])
for name in ['walnut_diff.jpg','walnut_nor.jpg','walnut_rough.jpg']:
    if not (root/'assets/lemo/core/assets/polyhaven'/name).is_file():
        errors.append('Missing shared runtime texture: '+name)
expected = {f['path'] for f in manifest['included']}
actual_files = {str(p.relative_to(root/'assets/lemo')) for p in (root/'assets/lemo').rglob('*') if p.is_file()}
if actual_files != expected:
    errors.append('Manifest file coverage mismatch: '+str(sorted(actual_files ^ expected)))
print(json.dumps({'upstream_commit':manifest['commit'],'source_files':len(manifest['included']),'lemo_styles':len(lemo),'opuscar_references':len(entries),'twoclipping_variants':2,'critical_missing_assets':len(critical_missing),'other_missing_literal_assets':len(asset_check['missing'])-len(critical_missing),'errors':errors},ensure_ascii=False,indent=2))
sys.exit(1 if errors else 0)
