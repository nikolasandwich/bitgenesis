"""Frozen posthoc case selection and complete upstream provenance."""
from pathlib import Path
from scripts.horizon_fate_inputs import read,digest,bindings as previous_bindings

def cases():
    return [dict(exchange=e,directory=f'data/v4-study-016/branches/history-false-seed-112000-mutation-0-exchange-{str(e).lower()}',source='data/v4-study-015/baselines/seed-112000-drive-250-mutation-0') for e in (True,False)]

def validate_cases(rows):
    assert len(rows)==2 and all(type(r['exchange']) is bool for r in rows)
    assert rows==cases()

def bindings():
    paths=previous_bindings();assert len(paths)==1613
    root=Path('data/v4-study-016-fates');meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and proof['status']=='verified' and proof['branches']==40
    assert meta['input_sha256']==meta['input_sha256_after']==paths
    names=('metadata.json','records.json','results.json','summary.json','independent-verification.json')
    assert {p.name for p in root.iterdir()}==set(names)
    for name in names:
        p=root/name;archive=Path('docs/research/results')/('v4-study-016-fates-'+name)
        assert p.is_file() and not p.is_symlink() and p.read_bytes()==archive.read_bytes()
        if name!='independent-verification.json':assert digest(p)==proof['files_sha256'][name]
        paths[str(p)]=digest(p);paths[str(archive)]=digest(archive)
    assert meta['output_sha256']=={n:digest(root/n) for n in ('records.json','results.json','summary.json')}
    selected=[(b['history'],b['seed'],b['mutation'],b['exchange'],c['component'],c['anchor_members'],c['first_complete_replacement_tick'],c['first_break_tick']) for b in read(root/'records.json') for c in b['components'] if c['order']=='replacement_first']
    assert selected==[(False,112000,0,True,7,[8,9],21,22)]
    rows=cases();validate_cases(rows)
    initial=[]
    for row in rows:
        directory=Path(row['directory']);m=read(directory/'metadata.json');i=read(directory/'initial.json')
        assert m['exchange'] is row['exchange'] and m['source_exchange'] is False and m['anchor']==100 and m['horizon']==400 and m['status']=='complete'
        assert Path(m['source']).resolve()==Path(row['source']).resolve()
        assert i['observation']['components']['material'][7]==[8,9];initial.append(i)
    assert initial[0]==initial[1]
    for p in ('docs/design/v4-transient-case.zh-CN.md','scripts/transient_case_inputs.py','scripts/analyze_v4_transient_case.py','scripts/verify_v4_transient_case.py'):paths[p]=digest(p)
    return dict(sorted(paths.items()))
