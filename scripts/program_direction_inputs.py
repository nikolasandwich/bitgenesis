"""Only source provenance and IO; no paired scientific algorithms."""
from pathlib import Path
from itertools import product
import hashlib,json
from scripts.copy_program_inputs import bindings as prior_bindings

def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,separators=(',',':'))+'\n')
def source_cases():
    for seed,exchange in product(range(120000,120020),(False,True)):
        yield Path('data/v4-study-019/cases')/f'seed-{seed}-random-direction-exchange-{str(exchange).lower()}.json'

def bindings():
    result=prior_bindings();assert len(result)==215
    root=Path('data/v4-study-022');names=('metadata.json','cases.json','probes.json','summary.json','independent-verification.json')
    assert {p.name for p in root.iterdir()}==set(names)
    meta=read(root/names[0]);proof=read(root/names[-1])
    assert meta['status']=='complete' and meta['completed_cases']==3 and meta['completed_probes']==2
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert meta['output_sha256']=={n:digest(root/n) for n in names[1:-1]}
    assert proof['status']=='verified' and proof['cases']==3 and proof['probes']==2
    assert proof['files_sha256']=={n:digest(root/n) for n in names[:-1]}
    assert proof['verifier_sha256']==result['scripts/verify_v4_copy_program.py']
    for n in names:
        archive=Path('docs/research/results')/('v4-study-022-'+n)
        assert archive.read_bytes()==(root/n).read_bytes()
        for p in (archive,root/n):result[str(p)]=digest(p)
    for p in ('experiments/v4/study-023.md','scripts/program_direction_inputs.py','scripts/run_v4_program_direction.py','scripts/verify_v4_program_direction.py'):result[p]=digest(p)
    assert len(result)==229
    return dict(sorted(result.items()))
