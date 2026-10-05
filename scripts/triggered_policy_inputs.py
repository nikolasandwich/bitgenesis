"""Study039 source/code inventory; no scientific calculations."""
from pathlib import Path
from scripts.program_position_inputs import bindings as prior, read, save, digest
from scripts.founder_removal_inputs import validate_manifest

BASE=Path('docs/research/results/v4-study-039-design-sources.json')
NEW=('scripts/triggered_policy_inputs.py','scripts/run_v4_triggered_policy.py','scripts/verify_v4_triggered_policy.py')
EXTRA=('docs/design/v4-triggered-removal-policy.zh-CN.md',)+tuple(f'docs/research/results/v4-study-039-design-{n}.json' for n in ('sources','census','proof','review'))

def input_paths(errors=None):
    errors={} if errors is None else errors
    paths=set(NEW)|set(EXTRA)
    try:paths.update(read(BASE)['files_sha256'])
    except Exception as e:errors[str(BASE)]=repr(e)
    for root in ('data/v4-study-038','docs/research/results'):
        names=('metadata','records','summary','independent-verification')
        paths.update(f'{root}/{n}.json' if root.startswith('data') else f'{root}/v4-study-038-{n}.json' for n in names)
    paths.update(('docs/research/v4-study-038.zh-CN.md','docs/research/results/v4-study-038-review.json'))
    return sorted(paths)

def bindings():
    old=prior(); expected=read(BASE)['files_sha256']
    assert len(expected)==741 and set(old)<=set(expected)
    validate_manifest(expected)
    review=read('docs/research/results/v4-study-039-design-review.json')
    assert review['verdict']=='APPROVED' and review['task']=='1.1'
    validate_manifest(review['files_sha256'])
    root=Path('data/v4-study-038');meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and proof['status']=='verified'
    assert meta['input_sha256']==meta['input_sha256_after']==proof['input_sha256']==proof['input_sha256_after']==old
    errors={};paths=input_paths(errors);assert not errors
    return {p:digest(p) for p in paths}
