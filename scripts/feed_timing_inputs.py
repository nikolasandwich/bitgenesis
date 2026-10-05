"""Study030 source inventory and byte bindings; no timing computation."""
from pathlib import Path
from scripts.child_energy_inputs import bindings as prior, source_cases, read, save, digest

NAMES=('metadata.json','records.json','summary.json','independent-verification.json')
NEW_FILES=('experiments/v4/study-030.md','scripts/feed_timing_inputs.py',
           'scripts/analyze_v4_feed_timing.py','scripts/verify_v4_feed_timing.py')


def input_paths(errors=None):
    if errors is None:errors={}
    paths=set(NEW_FILES)|{str(p) for p in source_cases()}
    for n in NAMES:paths.update(('data/v4-study-029/'+n,'docs/research/results/v4-study-029-'+n))
    for path in (Path('data/v4-study-029/metadata.json'),Path('docs/research/results/v4-study-029-metadata.json')):
        try:
            inventory=read(path)['input_sha256']
            if not isinstance(inventory,dict) or len(inventory)!=479 or not all(isinstance(k,str) for k in inventory):
                raise ValueError('prior479 inventory')
            paths.update(inventory);break
        except Exception as error:errors[str(path)]=repr(error)
    return sorted(paths)


def bindings():
    result=prior();assert len(result)==479
    root=Path('data/v4-study-029');assert {p.name for p in root.iterdir()}==set(NAMES)
    meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and meta['completed_branches']==meta['planned_branches']==52
    assert meta['saved_world_steps']==996 and meta['child_steps']==268 and meta['new_full_world_steps']==meta['new_phase_transitions']==0
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert meta['output_sha256']=={n:digest(root/n) for n in ('records.json','summary.json')}
    assert proof['status']=='verified' and proof['input_files']==479 and proof['branches']==52 and proof['pairs']==26
    assert proof['saved_world_steps']==996 and proof['child_steps']==268
    assert proof['input_sha256']==proof['input_sha256_after']==result
    assert proof['verifier_sha256']==result['scripts/verify_v4_child_energy.py']
    assert proof['files_sha256']=={n:digest(root/n) for n in NAMES[:-1]}
    for n in NAMES:
        path=root/n;archive=Path('docs/research/results/v4-study-029-'+n)
        assert path.read_bytes()==archive.read_bytes()
        for p in (path,archive):result[str(p)]=digest(p)
    for p in NEW_FILES:result[p]=digest(p)
    assert len(result)==491 and set(result)==set(input_paths())
    return dict(sorted(result.items()))
