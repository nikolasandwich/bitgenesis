"""Frozen source paths and integrity only; no opportunity classification."""
from pathlib import Path
from scripts.program_feed_inputs import bindings as prior,read,digest,save

MODES=('random-direction','random-feed','random-both')
NEW_FILES=('experiments/v4/study-026.md','scripts/north_opportunity_inputs.py','scripts/analyze_v4_north_opportunities.py','scripts/verify_v4_north_opportunities.py')
NAMES=('metadata.json','results.json','summary.json','independent-verification.json')

def source_cases():
    for genotype in ('homogeneous','heterogeneous'):
        for mode in MODES:
            study='019' if genotype=='homogeneous' else '023' if mode=='random-direction' else '025'
            for exchange in (False,True):
                for seed in range(120000,120020):
                    yield genotype,Path(f'data/v4-study-{study}/cases/seed-{seed}-{mode}-exchange-{str(exchange).lower()}.json')

def input_paths(errors=None):
    if errors is None:errors={}
    paths=set(NEW_FILES)
    paths.update(str(p) for _,p in source_cases())
    for n in NAMES:
        paths.add('data/v4-study-025/'+n);paths.add('docs/research/results/v4-study-025-'+n)
    paths.update(('docs/research/results/v4-study-025-cases.tar.gz','docs/research/results/v4-study-025-archive-verification.json'))
    for p in (Path('data/v4-study-025/metadata.json'),Path('docs/research/results/v4-study-025-metadata.json')):
        try:
            inventory=read(p)['input_sha256']
            if not isinstance(inventory,dict) or len(inventory)!=295 or not all(isinstance(k,str) for k in inventory):raise ValueError('prior295 inventory')
            paths.update(inventory);break
        except Exception as exc:errors[str(p)]=repr(exc)
    return sorted(paths)

def bindings():
    result=prior();assert len(result)==295
    root=Path('data/v4-study-025');meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert {p.name for p in root.iterdir()}==set(NAMES)|{'cases'}
    assert meta['status']=='complete' and meta['completed_cases']==80 and meta['new_simulation_steps']==2560
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert proof['status']=='verified' and proof['cases']==80 and proof['saved_steps']==2560 and proof['input_files']==295
    assert proof['verifier_sha256']==result['scripts/verify_v4_program_feed.py']
    cases=[p for _,p in source_cases() if p.parent==root/'cases'];assert len(cases)==80 and set(cases)==set((root/'cases').iterdir())
    output={str(p.relative_to(root)):digest(p) for p in cases}
    output.update({n:digest(root/n) for n in ('results.json','summary.json')})
    assert meta['output_sha256']==output
    assert proof['files_sha256']==dict(output,**{'metadata.json':digest(root/'metadata.json')})
    for p in cases:result[str(p)]=digest(p)
    for n in NAMES:
        p=root/n;a=Path('docs/research/results/v4-study-025-'+n);assert p.read_bytes()==a.read_bytes()
        for f in (p,a):result[str(f)]=digest(f)
    for p in ('docs/research/results/v4-study-025-cases.tar.gz','docs/research/results/v4-study-025-archive-verification.json',*NEW_FILES):result[p]=digest(p)
    assert len(result)==389 and set(result)==set(input_paths())
    return dict(sorted(result.items()))
