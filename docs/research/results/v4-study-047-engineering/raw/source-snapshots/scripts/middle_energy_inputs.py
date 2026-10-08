"""Study042 full-audit source inventory; no lifetime calculations."""
from pathlib import Path
from scripts.lineage_route_inputs import bindings as prior,sources,read,save,digest,capture
from scripts.founder_removal_inputs import validate_manifest
MANIFEST=Path('docs/research/results/v4-study-042-design-sources.json')
NEW=('scripts/middle_energy_inputs.py','scripts/analyze_v4_middle_energy.py','scripts/verify_v4_middle_energy.py')
EXTRA=tuple(f'docs/research/results/v4-study-042-design-{n}.json' for n in ('sources','census','proof','review'))+('docs/design/v4-middle-energy-windows.zh-CN.md',)

def input_paths():return sorted(set(read(MANIFEST)['files_sha256'])|set(NEW)|set(EXTRA))

def bindings():
    old=prior();expected=read(MANIFEST)['files_sha256'];assert len(expected)==812 and set(old)<=set(expected)
    validate_manifest(expected)
    review=read('docs/research/results/v4-study-042-design-review.json');assert review['verdict']=='APPROVED' and review['task']=='1.1'
    validate_manifest(review['files_sha256'])
    return {p:digest(p) for p in input_paths()}
