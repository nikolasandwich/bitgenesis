"""Study032 bound evidence inventory, without probability computation."""
from pathlib import Path
from scripts.energy_probability_inputs import bindings as prior, read, save, digest

NAMES=('metadata.json','records.json','summary.json','independent-verification.json')
NEW_FILES=('experiments/v4/study-032.md','scripts/energy_absorption_inputs.py',
           'scripts/analyze_v4_energy_absorption.py','scripts/verify_v4_energy_absorption.py')


def input_paths(errors=None):
    if errors is None:errors={}
    paths=set(NEW_FILES)
    for n in NAMES:paths.update(('data/v4-study-031/'+n,'docs/research/results/v4-study-031-'+n))
    for path in (Path('data/v4-study-031/metadata.json'),Path('docs/research/results/v4-study-031-metadata.json')):
        try:
            inventory=read(path)['input_sha256']
            if not isinstance(inventory,dict) or len(inventory)!=503 or not all(isinstance(k,str) for k in inventory):
                raise ValueError('prior503 inventory')
            paths.update(inventory);break
        except Exception as error:errors[str(path)]=repr(error)
    return sorted(paths)


def bindings():
    result=prior();assert len(result)==503
    root=Path('data/v4-study-031');assert {p.name for p in root.iterdir()}==set(NAMES)
    meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and meta['completed_horizons']==meta['planned_horizons']==33
    assert meta['cohort_states']==52 and meta['max_horizon']==32
    assert meta['new_full_world_steps']==meta['new_phase_transitions']==0
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert meta['output_sha256']=={n:digest(root/n) for n in ('records.json','summary.json')}
    assert proof['status']=='verified' and proof['input_files']==503 and proof['completed_horizons']==proof['planned_horizons']==33
    assert proof['cohort_states']==52 and proof['summary_cells']==4 and proof['max_horizon']==32
    assert proof['input_sha256']==proof['input_sha256_after']==result
    assert proof['verifier_sha256']==result['scripts/verify_v4_energy_probability.py']
    assert proof['files_sha256']=={n:digest(root/n) for n in NAMES[:-1]}
    for n in NAMES:
        path=root/n;archive=Path('docs/research/results/v4-study-031-'+n)
        assert path.read_bytes()==archive.read_bytes()
        for p in (path,archive):result[str(p)]=digest(p)
    for p in NEW_FILES:result[p]=digest(p)
    assert len(result)==515 and set(result)==set(input_paths())
    return dict(sorted(result.items()))
