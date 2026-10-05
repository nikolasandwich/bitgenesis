"""Study037 source inventory and byte validation, without scientific analysis."""
from pathlib import Path
from scripts.founder_removal_inputs import bindings as prior, read, save, digest, validate_manifest

ROOT=Path('data/v4-study-036')
NAMES=('metadata.json','records.json','summary.json','selection.json','independent-verification.json')
NEW=('experiments/v4/study-037.md','scripts/reformation_barrier_inputs.py',
     'scripts/analyze_v4_reformation_barriers.py','scripts/verify_v4_reformation_barriers.py')
REVIEW=Path('docs/research/results/v4-study-036-review.json')


def source_branches():
    records=read(ROOT/'records.json')
    assert len(records)==58
    for i,r in enumerate(records):
        if r['selection']['mode']=='random-direction':
            yield ROOT/'cases'/f'branch-{i:03d}.json'


def input_paths(errors=None):
    if errors is None:errors={}
    paths=set(NEW)|{str(ROOT/n) for n in NAMES}
    paths.update(str(ROOT/'cases'/f'branch-{i:03d}.json') for i in range(58))
    paths.update('docs/research/results/v4-study-036-'+n for n in NAMES)
    paths.update((str(REVIEW),'docs/research/results/v4-study-036-preservation.json',
                  'docs/research/results/v4-study-036-cases.tar.gz','docs/research/v4-study-036.zh-CN.md'))
    for path,key in ((ROOT/'metadata.json','input_sha256'),(REVIEW,'files_sha256')):
        try:
            inventory=read(path)[key];assert isinstance(inventory,dict) and inventory
            paths.update(inventory)
        except Exception as error:errors[str(path)]=repr(error)
    return sorted(paths)


def bindings():
    old=prior();assert len(old)==581
    meta=read(ROOT/'metadata.json');proof=read(ROOT/'independent-verification.json')
    assert meta['status']=='complete' and proof['status']=='verified'
    assert meta['completed_cases']==58 and meta['treatment_steps']==meta['control_replay_steps']==1260
    assert meta['input_sha256']==meta['input_sha256_after']==old
    assert proof['input_sha256']==proof['input_sha256_after']==old
    expected={str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'cases').glob('*.json'))}
    assert len(expected)==58
    expected.update({n:digest(ROOT/n) for n in ('records.json','summary.json','selection.json')})
    assert meta['output_sha256']==expected
    expected['metadata.json']=digest(ROOT/'metadata.json')
    assert proof['files_sha256']==proof['files_sha256_after']==expected
    for name in NAMES:
        assert (ROOT/name).read_bytes()==Path('docs/research/results/v4-study-036-'+name).read_bytes()
    review=read(REVIEW);assert review['verdict']=='APPROVED'
    validate_manifest(review['files_sha256'])
    errors={};paths=input_paths(errors);assert not errors and set(old)<=set(paths)
    return {p:digest(p) for p in paths}
