"""Immutable artificial-control provenance, without new tape or analysis logic."""
from pathlib import Path
import hashlib,json
from scripts.run_v4_copy_control import bindings as prior_bindings

def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bindings():
    result=prior_bindings();assert len(result)==45
    root=Path('data/v4-copy-control');meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and meta['completed_cases']==3 and proof['status']=='verified'
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert proof['verifier_sha256']==result['scripts/verify_v4_copy_control.py']
    names=('metadata.json','cases.json','summary.json','independent-verification.json')
    assert {p.name for p in root.iterdir()}==set(names)
    assert meta['output_sha256']=={n:digest(root/n) for n in names[1:3]}
    assert proof['files_sha256']=={n:digest(root/n) for n in names[:3]}
    for n in names:
        archive=Path('docs/research/results')/('v4-copy-control-'+n)
        assert archive.read_bytes()==(root/n).read_bytes()
        for p in (archive,root/n):result[str(p)]=digest(p)
    for p in ('experiments/v4/study-019.md','scripts/copy_ablation_inputs.py','scripts/run_v4_copy_ablation.py','scripts/verify_v4_copy_ablation.py'):result[p]=digest(p)
    assert len(result)==57
    return dict(sorted(result.items()))
