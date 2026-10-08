"""Only immutable source binding and IO for the differentiated control."""
from pathlib import Path
import hashlib,json
from scripts.copy_member_inputs import bindings as prior_bindings

def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,separators=(',',':'))+'\n')
def bindings():
    result=prior_bindings();assert len(result)==203
    root=Path('data/v4-study-021');names=('metadata.json','records.json','summary.json','independent-verification.json')
    assert {p.name for p in root.iterdir()}==set(names)
    meta=read(root/names[0]);proof=read(root/names[3])
    assert meta['status']=='complete' and meta['completed_cases']==123 and meta['saved_steps']==3936
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert meta['output_sha256']=={n:digest(root/n) for n in names[1:3]}
    assert proof['status']=='verified' and proof['cases']==123 and proof['saved_steps']==3936
    assert proof['files_sha256']=={n:digest(root/n) for n in names[:3]}
    assert proof['verifier_sha256']==result['scripts/verify_v4_copy_members.py']
    for n in names:
        archive=Path('docs/research/results')/('v4-study-021-'+n)
        assert archive.read_bytes()==(root/n).read_bytes()
        for p in (archive,root/n):result[str(p)]=digest(p)
    for p in ('experiments/v4/study-022.md','scripts/copy_program_inputs.py','scripts/run_v4_copy_program.py','scripts/verify_v4_copy_program.py'):result[p]=digest(p)
    assert len(result)==215
    return dict(sorted(result.items()))
