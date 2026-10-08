"""Immutable study016 inputs shared only as provenance, never classification."""
from pathlib import Path
from itertools import product
import hashlib,json
SOURCE=Path('data/v4-study-016')

def read(path):return json.loads(Path(path).read_text())
def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def validate_grid(rows):
    assert len(rows)==40
    assert all(type(r['history']) is bool and type(r['exchange']) is bool and type(r['seed']) is int and type(r['mutation']) is int for r in rows)
    assert {(r['history'],r['seed'],r['mutation'],r['exchange']) for r in rows}==set(product((True,False),range(112000,112005),(0,100),(True,False)))

def source_rows():
    rows=read(SOURCE/'results.json');saved=read(SOURCE/'checkpoints.json')
    validate_grid(rows);validate_grid(saved)
    indexed={(r['history'],r['seed'],r['mutation'],r['exchange']):r['records'] for r in saved}
    for r in rows:
        assert r['status']=='complete' and r['anchor']==100 and r['horizon']==400
        records=indexed[r['history'],r['seed'],r['mutation'],r['exchange']]
        assert set(records)=={'100','200','300','400'}
        r['records']=records
    return rows

def bindings():
    meta=read(SOURCE/'metadata.json');proof=read(SOURCE/'aggregation-verification.json');rows=source_rows()
    assert meta['status']=='complete' and meta['completed_branches']==40 and proof['status']=='verified' and proof['branches']==40
    paths=dict(meta['input_sha256']);assert paths==meta['input_sha256_after']
    assert len(paths)==1319
    for path,sha in paths.items():assert digest(path)==sha,path
    rootfiles=('metadata.json','results.json','checkpoints.json','summary.json','aggregation-verification.json')
    expected={str(SOURCE/n) for n in rootfiles}
    for r in rows:
        expected_dir=f"branches/history-{str(r['history']).lower()}-seed-{r['seed']}-mutation-{r['mutation']}-exchange-{str(r['exchange']).lower()}"
        assert r['directory']==expected_dir
        assert set(r['files_sha256'])=={'metadata.json','initial.json','steps.jsonl','final.json','continuity.json','summary.json','audit.json'}
        for name,sha in r['files_sha256'].items():
            path=SOURCE/r['directory']/name;assert digest(path)==sha;expected.add(str(path))
    actual={str(p) for p in SOURCE.rglob('*') if p.is_file()}
    assert actual==expected and all(not p.is_symlink() for p in SOURCE.rglob('*'))
    for n in rootfiles:
        archive=Path('docs/research/results')/('v4-study-016-'+n)
        assert archive.read_bytes()==(SOURCE/n).read_bytes();paths[str(archive)]=digest(archive)
        if n!='aggregation-verification.json':assert proof[n.removesuffix('.json')+'_sha256']==digest(SOURCE/n)
    assert meta['output_sha256']=={n:digest(SOURCE/n) for n in rootfiles[1:4]}
    for p in expected:paths[p]=digest(p)
    for p in ('docs/design/v4-horizon-fates.zh-CN.md','scripts/horizon_fate_inputs.py','scripts/analyze_v4_horizon_fates.py','scripts/verify_v4_horizon_fates.py'):paths[p]=digest(p)
    return dict(sorted(paths.items()))
