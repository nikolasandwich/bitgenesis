"""Study044 immutable input inventory; no scientific observation."""
from pathlib import Path
from scripts.middle_north_policy_inputs import bindings as prior,read,save,digest
from scripts.founder_removal_inputs import validate_manifest
BASE=Path('docs/research/results/v4-study-044-design-sources.json')
NEW=('scripts/policy_component_timing_inputs.py','scripts/analyze_v4_policy_component_timing.py','scripts/verify_v4_policy_component_timing.py')
EXTRA=tuple(f'docs/research/results/v4-study-044-design-{n}.json' for n in ('sources','census','review'))
def input_paths(errors=None):
    errors={} if errors is None else errors
    paths=set(NEW)|set(EXTRA)
    try:paths.update(read(BASE)['files_sha256'])
    except Exception as exc:errors[str(BASE)]=repr(exc)
    return sorted(paths)
def capture(paths):
    hashes={};errors={}
    for p in paths:
        try:hashes[p]=digest(p)
        except Exception as exc:errors[p]=repr(exc)
    return hashes,errors
def bindings():
    expected=read(BASE)['files_sha256'];assert len(expected)==886 and set(prior())<=set(expected)
    validate_manifest(expected)
    review=read(EXTRA[-1]);assert review['verdict']=='APPROVED' and review['task']=='1.1'
    validate_manifest(review['files_sha256'])
    errors={};paths=input_paths(errors);assert not errors
    return {p:digest(p) for p in paths}
