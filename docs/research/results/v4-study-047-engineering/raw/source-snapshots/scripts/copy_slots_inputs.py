"""Study034 bound evidence inventory, without slot classification."""
from pathlib import Path
from scripts.material_support_inputs import bindings as prior, read, save, digest, source_cases

NAMES=('metadata.json','records.json','summary.json','independent-verification.json')
NEW_FILES=('experiments/v4/study-034.md','scripts/copy_slots_inputs.py',
           'scripts/analyze_v4_copy_slots.py','scripts/verify_v4_copy_slots.py')


def input_paths(errors=None):
    if errors is None:errors={}
    paths=set(NEW_FILES)
    for n in NAMES:paths.update(('data/v4-study-033/'+n,'docs/research/results/v4-study-033-'+n))
    for path in (Path('data/v4-study-033/metadata.json'),Path('docs/research/results/v4-study-033-metadata.json')):
        try:
            inventory=read(path)['input_sha256']
            if not isinstance(inventory,dict) or len(inventory)!=401 or not all(isinstance(k,str) for k in inventory):
                raise ValueError('prior401 inventory')
            paths.update(inventory);break
        except Exception as error:errors[str(path)]=repr(error)
    return sorted(paths)


def bindings():
    result=prior();assert len(result)==401
    root=Path('data/v4-study-033');assert {p.name for p in root.iterdir()}==set(NAMES)
    meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and meta['completed_cases']==meta['planned_cases']==240
    assert meta['saved_steps']==7680 and meta['new_simulation_steps']==0
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert meta['output_sha256']=={n:digest(root/n) for n in ('records.json','summary.json')}
    assert proof['status']=='verified' and proof['input_files']==401 and proof['cases']==240
    assert proof['saved_steps']==7680 and proof['new_simulation_steps']==0
    assert proof['input_sha256']==proof['input_sha256_after']==result
    assert meta['checked_snapshots']==proof['checked_snapshots']==7920
    assert meta['checked_sites']==proof['checked_sites']==2027520
    assert proof['verifier_sha256']==result['scripts/verify_v4_material_support.py']
    assert proof['files_sha256']=={n:digest(root/n) for n in NAMES[:-1]}
    for n in NAMES:
        path=root/n;archive=Path('docs/research/results/v4-study-033-'+n)
        assert path.read_bytes()==archive.read_bytes()
        for p in (path,archive):result[str(p)]=digest(p)
    for p in NEW_FILES:result[p]=digest(p)
    assert len(result)==413 and set(result)==set(input_paths())
    return dict(sorted(result.items()))
