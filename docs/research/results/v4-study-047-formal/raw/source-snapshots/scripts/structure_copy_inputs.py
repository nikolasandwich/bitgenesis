"""Reuse the authenticated horizon cohort; add only this observer's provenance."""
from scripts.horizon_fate_inputs import bindings as prior_bindings,source_rows as prior_rows,read,digest

def source_rows():
    return [{k:v for k,v in row.items() if k!='records'} for row in prior_rows()]

def bindings():
    result=prior_bindings();assert len(result)==1613
    for path in ('experiments/v4/study-017.md','scripts/structure_copy_inputs.py','scripts/analyze_v4_structure_copies.py','scripts/verify_v4_structure_copies.py'):result[path]=digest(path)
    return dict(sorted(result.items()))
