"""Authenticated copy records and frozen horizon inputs; no classification."""
from pathlib import Path
from scripts.structure_copy_inputs import bindings as prior_bindings,source_rows,read,digest

def bindings():
    result=prior_bindings();assert len(result)==1617
    root=Path('data/v4-study-017');meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and meta['completed_branches']==40 and proof['status']=='verified'
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert proof['verifier_sha256']==result['scripts/verify_v4_structure_copies.py']
    names=('metadata.json','records.json','results.json','summary.json','independent-verification.json')
    assert {p.name for p in root.iterdir()}==set(names)
    assert meta['output_sha256']=={n:digest(root/n) for n in names[1:4]}
    assert proof['files_sha256']=={n:digest(root/n) for n in names[:4]}
    for name in names:
        archive=Path('docs/research/results')/('v4-study-017-'+name)
        assert archive.read_bytes()==(root/name).read_bytes()
        for p in (archive,root/name):result[str(p)]=digest(p)
    for p in ('experiments/v4/study-018.md','scripts/copy_bottleneck_inputs.py','scripts/analyze_v4_copy_bottlenecks.py','scripts/verify_v4_copy_bottlenecks.py'):result[p]=digest(p)
    assert len(result)==1631
    return dict(sorted(result.items()))
