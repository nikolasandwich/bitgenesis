"""Study040 immutable input inventory and cohort keys; no observation science."""
from pathlib import Path
from scripts.triggered_policy_inputs import bindings as prior,read,save,digest
from scripts.founder_removal_inputs import validate_manifest
ROOT=Path('data/v4-study-039')
NEW=('scripts/position_barrier_inputs.py','scripts/analyze_v4_position_barriers.py','scripts/verify_v4_position_barriers.py','experiments/v4/study-040.md')

def validate_key(encoding,seed):
    if encoding not in ('east','west') or type(seed) is not int or seed not in range(120000,120020):raise ValueError('fixed east/west source key')

def input_paths():
    paths=set(prior())|set(NEW)
    for name in ('metadata','records','summary','selection','independent-verification'):
        paths.update((f'data/v4-study-039/{name}.json',f'docs/research/results/v4-study-039-{name}.json'))
    paths.update(str(p) for p in (ROOT/'cases').glob('*.json'))
    paths.update(('docs/research/v4-study-039.zh-CN.md','docs/research/results/v4-study-039-review.json','docs/research/results/v4-study-039-preservation.json','docs/research/results/v4-study-039-cases.tar.gz'))
    return sorted(paths)

def bindings():
    old=prior();meta=read(ROOT/'metadata.json');proof=read(ROOT/'independent-verification.json')
    assert meta['status']=='complete' and proof['status']=='verified'
    assert meta['input_sha256']==meta['input_sha256_after']==proof['input_sha256']==proof['input_sha256_after']==old
    assert {n:digest(ROOT/n) for n in proof['files_sha256']}==proof['files_sha256']
    review=read('docs/research/results/v4-study-039-review.json');assert review['verdict']=='APPROVED'
    validate_manifest(review['files_sha256'])
    assert len(list((ROOT/'cases').glob('*.json')))==8
    return {p:digest(p) for p in input_paths()}

def sources():
    records=read(ROOT/'records.json')
    assert len(records)==100
    chosen=[r for r in records if r['encoding'] in ('east','west') and r['trigger']]
    assert len(chosen)==8 and sum(r['remaining'] for r in chosen)==116
    assert [sum(r['encoding']==e for r in chosen) for e in ('east','west')]==[5,3]
    assert sum(r['short_window'] for r in chosen)==2
    for r in chosen:
        validate_key(r['encoding'],r['seed'])
        path=ROOT/'cases'/f"{r['encoding']}-{r['seed']}.json"
        branch=read(path)
        assert branch['selection']==r['selection'] and branch['selection']['source']==r['source']
        assert branch['ablation']['episodes']==r['ablation_episodes']
        assert branch['ablation']['metrics']==r['ablation_future_metrics']
        yield r['encoding'],path,r['source']


def capture(paths):
    hashes={};errors={}
    for p in paths:
        try:hashes[p]=digest(p)
        except Exception as exc:errors[p]=repr(exc)
    return hashes,errors
