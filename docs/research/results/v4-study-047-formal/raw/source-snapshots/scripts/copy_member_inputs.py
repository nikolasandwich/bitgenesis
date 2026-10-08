"""Read-only source binding for copy member dependence; no scientific logic."""
from pathlib import Path
import hashlib,json
from scripts.copy_episode_inputs import bindings as prior_bindings,source_cases as prior_cases

def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,separators=(',',':'))+'\n')
def source_cases():
    for path in prior_cases():yield path.stem,read(path)
    cases=read('data/v4-copy-control/cases.json')
    assert [c['name'] for c in cases]==['constructed-off','constructed-on','no-raw-off']
    for case in cases:yield 'control-'+case['name'],case

def bindings():
    result=prior_bindings();assert len(result)==191
    root=Path('data/v4-study-020');names=('metadata.json','records.json','summary.json','independent-verification.json')
    meta=read(root/names[0]);proof=read(root/names[3])
    assert {p.name for p in root.iterdir()}==set(names)
    assert meta['status']=='complete' and meta['completed_cases']==120 and meta['saved_steps']==3840
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert meta['output_sha256']=={n:digest(root/n) for n in names[1:3]}
    assert proof['status']=='verified' and proof['cases']==120 and proof['saved_steps']==3840
    assert proof['files_sha256']=={n:digest(root/n) for n in names[:3]}
    assert proof['verifier_sha256']==result['scripts/verify_v4_copy_episodes.py']
    for n in names:
        archive=Path('docs/research/results')/('v4-study-020-'+n)
        assert archive.read_bytes()==(root/n).read_bytes()
        for p in (archive,root/n):result[str(p)]=digest(p)
    for p in ('experiments/v4/study-021.md','scripts/copy_member_inputs.py','scripts/analyze_v4_copy_members.py','scripts/verify_v4_copy_members.py'):result[p]=digest(p)
    assert len(result)==203
    return dict(sorted(result.items()))
