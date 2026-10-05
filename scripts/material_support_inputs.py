"""Study033 bound evidence inventory, without material classification."""
from pathlib import Path
from scripts.north_opportunity_inputs import bindings as prior, read, save, digest, source_cases

NAMES=('metadata.json','records.json','summary.json','independent-verification.json')
NEW_FILES=('experiments/v4/study-033.md','scripts/material_support_inputs.py',
           'scripts/analyze_v4_material_support.py','scripts/verify_v4_material_support.py')


def input_paths(errors=None):
    if errors is None:errors={}
    paths=set(NEW_FILES)
    for n in NAMES:paths.update(('data/v4-study-026/'+n,'docs/research/results/v4-study-026-'+n))
    for path in (Path('data/v4-study-026/metadata.json'),Path('docs/research/results/v4-study-026-metadata.json')):
        try:
            inventory=read(path)['input_sha256']
            if not isinstance(inventory,dict) or len(inventory)!=389 or not all(isinstance(k,str) for k in inventory):
                raise ValueError('prior389 inventory')
            paths.update(inventory);break
        except Exception as error:errors[str(path)]=repr(error)
    return sorted(paths)


def bindings():
    result=prior();assert len(result)==389
    root=Path('data/v4-study-026');assert {p.name for p in root.iterdir()}==set(NAMES)
    meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and meta['completed_cases']==meta['planned_cases']==240
    assert meta['saved_steps']==7680 and meta['new_simulation_steps']==0
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert meta['output_sha256']=={n:digest(root/n) for n in ('records.json','summary.json')}
    assert proof['status']=='verified' and proof['input_files']==389 and proof['cases']==240
    assert proof['saved_steps']==7680 and proof['new_simulation_steps']==0
    # Study026 proof binds the metadata hash; its before/after inputs live in metadata.
    assert proof['verifier_sha256']==result['scripts/verify_v4_north_opportunities.py']
    assert proof['files_sha256']=={n:digest(root/n) for n in NAMES[:-1]}
    for n in NAMES:
        path=root/n;archive=Path('docs/research/results/v4-study-026-'+n)
        assert path.read_bytes()==archive.read_bytes()
        for p in (path,archive):result[str(p)]=digest(p)
    for p in NEW_FILES:result[p]=digest(p)
    assert len(result)==401 and set(result)==set(input_paths())
    return dict(sorted(result.items()))
