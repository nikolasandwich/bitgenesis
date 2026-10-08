"""Study043 source inventory, no scientific calculations."""
from pathlib import Path
from scripts.middle_energy_inputs import bindings as prior, read, save, digest
from scripts.founder_removal_inputs import validate_manifest
BASE=Path('docs/research/results/v4-study-043-design-sources.json')
NEW=('scripts/middle_north_policy_inputs.py','scripts/run_v4_middle_north_policy.py','scripts/verify_v4_middle_north_policy.py')
EXTRA=tuple(f'docs/research/results/v4-study-043-design-{n}.json' for n in ('sources','census','review'))
def input_paths(errors=None):
    errors={} if errors is None else errors
    paths=set(NEW)|set(EXTRA)
    try:paths.update(read(BASE)['files_sha256'])
    except Exception as exc:errors[str(BASE)]=repr(exc)
    return sorted(paths)
def bindings():
    expected=read(BASE)['files_sha256'];assert len(expected)==834 and set(prior())<=set(expected)
    validate_manifest(expected)
    review=read(EXTRA[-1]);assert review['verdict']=='APPROVED' and review['task']=='1.1'
    validate_manifest(review['files_sha256'])
    errors={};paths=input_paths(errors);assert not errors
    return {p:digest(p) for p in paths}
