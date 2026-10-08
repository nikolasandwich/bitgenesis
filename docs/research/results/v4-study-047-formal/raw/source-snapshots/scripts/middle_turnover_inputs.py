"""Study045 immutable input inventory, no scientific computation."""
from pathlib import Path
from scripts.policy_component_timing_inputs import bindings as prior,read,save,digest,capture
from scripts.founder_removal_inputs import validate_manifest
BASE=Path('docs/research/results/v4-study-045-design-sources.json')
REVIEW=Path('docs/research/results/v4-study-045-design-review.json')
NEW=('scripts/middle_turnover_inputs.py','scripts/analyze_v4_middle_turnover.py','scripts/verify_v4_middle_turnover.py')
def input_paths(errors=None):
    errors={} if errors is None else errors
    paths=set(NEW)|{str(BASE),str(REVIEW),'docs/research/results/v4-study-045-design-census.json'}
    for path,key in ((BASE,'files_sha256'),(REVIEW,'files_sha256')):
        try:paths.update(read(path)[key])
        except Exception as exc:errors[str(path)]=repr(exc)
    return sorted(paths)
def bindings():
    expected=read(BASE)['files_sha256'];assert len(expected)==907 and set(prior())<=set(expected)
    assert expected==read(BASE)['files_sha256_after'];validate_manifest(expected)
    review=read(REVIEW);assert review['verdict']=='APPROVED' and review['task']=='1.1'
    validate_manifest(review['files_sha256'])
    errors={};paths=input_paths(errors);assert not errors
    return {p:digest(p) for p in paths}
