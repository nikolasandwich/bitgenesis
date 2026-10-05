"""IO and immutable source binding for the preselected phase intervention."""
from pathlib import Path
from scripts.north_opportunity_inputs import bindings as prior,source_cases,read,digest,save

NAMES=('metadata.json','records.json','summary.json','independent-verification.json')
NEW_FILES=('experiments/v4/study-027.md','scripts/north_energy_inputs.py','scripts/run_v4_north_energy.py','scripts/verify_v4_north_energy.py')

def input_paths(errors=None):
    if errors is None:errors={}
    paths=set(NEW_FILES)|{str(p) for _,p in source_cases()}
    for n in NAMES:paths.update(('data/v4-study-026/'+n,'docs/research/results/v4-study-026-'+n))
    for p in (Path('data/v4-study-026/metadata.json'),Path('docs/research/results/v4-study-026-metadata.json')):
        try:
            inventory=read(p)['input_sha256']
            if not isinstance(inventory,dict) or len(inventory)!=389 or not all(isinstance(k,str) for k in inventory):raise ValueError('prior389 inventory')
            paths.update(inventory);break
        except Exception as exc:errors[str(p)]=repr(exc)
    return sorted(paths)

def bindings():
    result=prior();assert len(result)==389
    root=Path('data/v4-study-026');assert {p.name for p in root.iterdir()}==set(NAMES)
    meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and meta['completed_cases']==240 and meta['saved_steps']==7680
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert meta['output_sha256']=={n:digest(root/n) for n in ('records.json','summary.json')}
    assert proof['status']=='verified' and proof['cases']==240 and proof['saved_steps']==7680 and proof['input_files']==389
    assert proof['verifier_sha256']==result['scripts/verify_v4_north_opportunities.py']
    assert proof['files_sha256']=={n:digest(root/n) for n in NAMES[:-1]}
    for n in NAMES:
        p=root/n;a=Path('docs/research/results/v4-study-026-'+n);assert p.read_bytes()==a.read_bytes()
        for f in (p,a):result[str(f)]=digest(f)
    for p in NEW_FILES:result[p]=digest(p)
    assert len(result)==401 and set(result)==set(input_paths())
    return dict(sorted(result.items()))
