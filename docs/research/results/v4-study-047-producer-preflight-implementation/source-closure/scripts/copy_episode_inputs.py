"""Only immutable provenance and IO for the saved stage-boundary audit."""
import hashlib
from itertools import product
import json
from pathlib import Path
from scripts.copy_ablation_inputs import bindings as prior_bindings

ROOT=Path('data/v4-study-019')

def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,separators=(',',':'))+'\n')
def source_cases():
    for seed,mode,exchange in product(range(120000,120020),('random-direction','random-feed','random-both'),(False,True)):
        yield ROOT/'cases'/f'seed-{seed}-{mode}-exchange-{str(exchange).lower()}.json'

def bindings():
    result=prior_bindings();assert len(result)==57
    meta=read(ROOT/'metadata.json');proof=read(ROOT/'independent-verification.json')
    assert meta['status']=='complete' and meta['completed_cases']==120 and meta['new_simulation_steps']==3840
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert proof['status']=='verified' and proof['cases']==120 and proof['saved_steps']==3840
    assert proof['verifier_sha256']==result['scripts/verify_v4_copy_ablation.py']
    cases=list(source_cases());names=('metadata.json','results.json','summary.json','independent-verification.json')
    assert {p.name for p in ROOT.iterdir()}==set(names)|{'cases'}
    assert set((ROOT/'cases').iterdir())==set(cases)
    hashes={str(p.relative_to(ROOT)):digest(p) for p in cases}
    assert meta['output_sha256']==hashes|{n:digest(ROOT/n) for n in ('results.json','summary.json')}
    assert proof['files_sha256']==hashes|{n:digest(ROOT/n) for n in names[:3]}
    for p in cases:result[str(p)]=hashes[str(p.relative_to(ROOT))]
    for n in names:
        archive=Path('docs/research/results')/('v4-study-019-'+n)
        assert archive.read_bytes()==(ROOT/n).read_bytes()
        for p in (archive,ROOT/n):result[str(p)]=digest(p)
    manifest=Path('docs/research/results/v4-study-019-archive-verification.json')
    tar=Path('docs/research/results/v4-study-019-cases.tar.gz');m=read(manifest)
    assert m['status']=='verified' and m['case_files']==120 and m['archive_sha256']==digest(tar) and m['archive_bytes']==tar.stat().st_size
    assert m['files']=={str(p.relative_to(ROOT)):dict(size=p.stat().st_size,sha256=hashes[str(p.relative_to(ROOT))]) for p in cases}
    assert m['raw_bytes']==sum(p.stat().st_size for p in cases)
    for p in (manifest,tar):result[str(p)]=digest(p)
    for p in ('experiments/v4/study-020.md','scripts/copy_episode_inputs.py','scripts/analyze_v4_copy_episodes.py','scripts/verify_v4_copy_episodes.py'):result[p]=digest(p)
    assert len(result)==191
    return dict(sorted(result.items()))
