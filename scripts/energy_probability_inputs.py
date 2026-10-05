"""Study031 bound evidence inventory, without probability computation."""
from pathlib import Path
from scripts.feed_timing_inputs import bindings as prior, read, save, digest

NAMES=('metadata.json','records.json','summary.json','independent-verification.json')
NEW_FILES=('experiments/v4/study-031.md','scripts/energy_probability_inputs.py',
           'scripts/analyze_v4_energy_probability.py','scripts/verify_v4_energy_probability.py')


def input_paths(errors=None):
    if errors is None:errors={}
    paths=set(NEW_FILES)
    for n in NAMES:paths.update(('data/v4-study-030/'+n,'docs/research/results/v4-study-030-'+n))
    for path in (Path('data/v4-study-030/metadata.json'),Path('docs/research/results/v4-study-030-metadata.json')):
        try:
            inventory=read(path)['input_sha256']
            if not isinstance(inventory,dict) or len(inventory)!=491 or not all(isinstance(k,str) for k in inventory):
                raise ValueError('prior491 inventory')
            paths.update(inventory);break
        except Exception as error:errors[str(path)]=repr(error)
    return sorted(paths)


def bindings():
    result=prior();assert len(result)==491
    root=Path('data/v4-study-030');assert {p.name for p in root.iterdir()}==set(NAMES)
    meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and meta['completed_branches']==meta['planned_branches']==52
    assert meta['saved_world_steps']==meta['site_steps']==996 and meta['live_start_steps']==268
    assert meta['new_full_world_steps']==meta['new_phase_transitions']==0
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert meta['output_sha256']=={n:digest(root/n) for n in ('records.json','summary.json')}
    assert proof['status']=='verified' and proof['input_files']==491 and proof['branches']==52 and proof['pairs']==26
    assert proof['saved_world_steps']==proof['site_steps']==996 and proof['live_start_steps']==268
    assert proof['input_sha256']==proof['input_sha256_after']==result
    assert proof['verifier_sha256']==result['scripts/verify_v4_feed_timing.py']
    assert proof['files_sha256']=={n:digest(root/n) for n in NAMES[:-1]}
    for n in NAMES:
        path=root/n;archive=Path('docs/research/results/v4-study-030-'+n)
        assert path.read_bytes()==archive.read_bytes()
        for p in (path,archive):result[str(p)]=digest(p)
    for p in NEW_FILES:result[p]=digest(p)
    assert len(result)==503 and set(result)==set(input_paths())
    return dict(sorted(result.items()))
