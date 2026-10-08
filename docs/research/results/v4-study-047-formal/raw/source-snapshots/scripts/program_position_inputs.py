"""Study038 immutable source inventory and paired environment locations."""
from pathlib import Path
from scripts.reformation_barrier_inputs import bindings as prior,read,save,digest
from scripts.founder_removal_inputs import validate_manifest

MANIFEST=Path('docs/research/results/v4-study-038-design-sources.json')
REVIEW=Path('docs/research/results/v4-study-038-design-review.json')
NEW=('scripts/program_position_inputs.py','scripts/run_v4_program_position.py','scripts/verify_v4_program_position.py')
EXTRA=(str(MANIFEST),str(REVIEW),'docs/research/results/v4-study-038-design-census.json','docs/design/v4-program-position.zh-CN.md')


def source_path(seed,encoding):
    if type(seed) is not int or seed not in range(120000,120020) or encoding not in ('east','west','south','north','homogeneous'):
        raise ValueError('fixed source identity')
    number='023' if encoding=='north' else '019'
    return Path(f'data/v4-study-{number}/cases/seed-{seed}-random-direction-exchange-false.json')


def input_paths(errors=None):
    if errors is None:errors={}
    paths=set(NEW)|set(EXTRA)
    try:
        expected=read(MANIFEST)['files_sha256'];assert isinstance(expected,dict) and len(expected)==671
        paths.update(expected)
    except Exception as error:errors[str(MANIFEST)]=repr(error)
    return sorted(paths)


def bindings():
    old=prior();assert len(old)==660
    expected=read(MANIFEST)['files_sha256'];assert len(expected)==671 and set(old)<=set(expected)
    validate_manifest(expected)
    root=Path('data/v4-study-037');meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and proof['status']=='verified'
    assert meta['input_sha256']==meta['input_sha256_after']==proof['input_sha256']==proof['input_sha256_after']==old
    assert meta['output_sha256']=={n:digest(root/n) for n in ('records.json','summary.json')}
    assert proof['files_sha256']=={n:digest(root/n) for n in ('metadata.json','records.json','summary.json')}
    review=read(REVIEW);assert review['verdict']=='APPROVED' and review['task']=='1.1'
    validate_manifest(review['files_sha256'])
    errors={};paths=input_paths(errors);assert not errors
    return {p:digest(p) for p in paths}
