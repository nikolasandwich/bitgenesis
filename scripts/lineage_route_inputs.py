"""Study041 immutable evidence chain; no route calculations."""
from pathlib import Path
from scripts.position_barrier_inputs import bindings as prior,sources,read,save,digest,capture
from scripts.founder_removal_inputs import validate_manifest
ROOT=Path('data/v4-study-040')
NEW=('scripts/lineage_route_inputs.py','scripts/analyze_v4_lineage_routes.py','scripts/verify_v4_lineage_routes.py','experiments/v4/study-041.md')

def input_paths():
    paths=set(read(ROOT/'metadata.json')['input_sha256'])|set(NEW)
    for n in ('metadata','records','summary','independent-verification'):
        paths.update((str(ROOT/f'{n}.json'),f'docs/research/results/v4-study-040-{n}.json'))
    paths.update(('docs/research/v4-study-040.zh-CN.md','docs/research/results/v4-study-040-review.json','docs/research/results/v4-study-040-preservation.json'))
    return sorted(paths)

def bindings():
    old=prior();meta=read(ROOT/'metadata.json');proof=read(ROOT/'independent-verification.json')
    assert meta['status']=='complete' and proof['status']=='verified'
    assert meta['input_sha256']==meta['input_sha256_after']==proof['input_sha256']==proof['input_sha256_after']==old
    assert {n:digest(ROOT/n) for n in proof['files_sha256']}==proof['files_sha256']
    review=read('docs/research/results/v4-study-040-review.json');assert review['verdict']=='APPROVED'
    validate_manifest(review['files_sha256'])
    return {p:digest(p) for p in input_paths()}
