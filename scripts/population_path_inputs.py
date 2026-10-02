"""Shared provenance checks; no population classification or aggregation."""
import json
from pathlib import Path
from hashlib import sha256
from itertools import product
from scripts.verify_v4_study012_summary import expected_bindings, verify_bindings, check_coverage
from scripts.verify_v4_formation_targets import checked_inputs as check_study013

read=lambda p:json.loads(Path(p).read_text())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()
ROOT=Path('data/v4-study-012')


def bindings():
    meta=read(ROOT/'metadata.json');rows=read(ROOT/'results.json');proof=read(ROOT/'aggregation-verification.json')
    assert meta['status']=='complete' and meta['completed_branches']==meta['planned_branches']==80
    code,sources=expected_bindings();verify_bindings(meta['bindings_sha256'],code);verify_bindings(meta['source_bindings_sha256'],sources)
    assert proof['status']=='verified' and (proof['branches'],proof['pairs'],proof['sources'])==(80,40,10)
    assert proof['results_sha256']==digest(ROOT/'results.json') and proof['summary_sha256']==digest(ROOT/'summary.json')
    assert proof['verifier_sha256']==digest('scripts/verify_v4_study012_summary.py')
    check_coverage(rows,('seed','drive','mutation','anchor','exchange'),set(product(range(96000,96005),(250,),(0,100),(100,200,300,400),(True,False))))
    paths=code|sources|{ROOT/p for p in ('metadata.json','results.json','summary.json','aggregation-verification.json')}
    files={'initial.json','steps.jsonl','final.json','summary.json','continuity.json'}
    for r in rows:
        name=f"seed-{r['seed']}-drive-250-mutation-{r['mutation']}-anchor-{r['anchor']}-exchange-{str(r['exchange']).lower()}"
        assert r['directory']==name and r['status']=='complete' and r['horizon']==100
        directory=ROOT/name;sm=read(directory/'metadata.json');audit=read(directory/'audit.json')
        assert sm['status']=='complete' and sm['horizon']==100 and sm['anchor']==r['anchor'] and sm['exchange'] is r['exchange']
        source=Path('data/v4-study-005')/f"seed-{r['seed']}-drive-250-mutation-{r['mutation']}"
        assert Path(sm['source']).resolve()==source.resolve()
        assert sm['source_sha256']==sm['source_sha256_after']=={p.name:digest(p) for p in source.iterdir() if p.is_file()}
        assert digest(directory/'metadata.json')==r['metadata_sha256'] and digest(directory/'audit.json')==r['audit_sha256']
        assert audit==r['audit'] and audit['ticks']==100
        assert audit['output_sha256']==sm['output_sha256']=={f:digest(directory/f) for f in files}
        assert r['continuity_sha256']==digest(directory/'continuity.json')
        paths.update(directory/f for f in files|{'metadata.json','audit.json'})
    r13,meta13=check_study013()
    paths.update(Path(p) for p in meta13['bindings_sha256']);paths.update(Path(p) for p in meta13['source_bindings_sha256'])
    p13=Path('data/v4-study-013');paths.update(p13/p for p in ('metadata.json','results.json','summary.json','aggregation-verification.json'))
    paths.update(p13/r['directory']/p for r in r13 for p in ('metadata.json','paired-steps.jsonl','summary.json'))
    paths.update(Path(p) for p in ('docs/design/v4-population-paths-supplement.md','scripts/population_path_inputs.py','scripts/analyze_v4_population_paths.py','scripts/verify_v4_population_paths.py','scripts/verify_v4_formation_targets.py'))
    return {str(p):digest(p) for p in sorted(paths)}


def reset_firsts():
    result={}
    for seed,mutation in product(range(96000,96005),(0,100)):
        p=Path('data/v4-study-013')/f'seed-{seed}-drive-250-mutation-{mutation}'/'paired-steps.jsonl'
        for line in p.open():
            row=json.loads(line)
            if row['tick'] in (101,201,301,401):result[seed,mutation,row['tick']-1]=row
    assert len(result)==40
    return result
