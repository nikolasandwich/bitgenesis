"""Independent saved-record recount and complete prospective cohort binding."""
import json
from pathlib import Path
from fractions import Fraction
from itertools import product
from hashlib import sha256
from bitgenesis.v4.hereditary_audit import audit as audit_baseline
from scripts.verify_v4_study012_summary import recount,check_coverage,verify_bindings

METRICS=('occupied','continuous','replacement','endpoint_closed','lineage_survival','original_retention','descendants')
read=lambda p:json.loads(Path(p).read_text())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()


def avg(values):
    good=[Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(good)/len(good)) if good else None,available=len(good),missing=len(values)-len(good))


def aggregate_saved(rows):
    check_coverage(rows,('seed','mutation','anchor','exchange'),set(product(range(112000,112005),(0,100),(100,200,300,400),(True,False))))
    index={(r['seed'],r['mutation'],r['anchor'],r['exchange']):r for r in rows};pairs=[];sources=[]
    for seed,mutation in product(range(112000,112005),(0,100)):
        selected=[]
        for anchor in (100,200,300,400):
            a,b=[index[seed,mutation,anchor,flag] for flag in (True,False)]
            assert a['status']==b['status']=='complete' and all(a['components'][k]==b['components'][k] for k in ('eligible_components','initial_components'))
            metrics={}
            for k in METRICS:
                av=str(a['occupied']) if k=='occupied' else a['components']['fractions'][k]
                bv=str(b['occupied']) if k=='occupied' else b['components']['fractions'][k]
                assert (av is None)==(bv is None)
                metrics[k]=dict(on=av,off=bv,difference=str(Fraction(av)-Fraction(bv)) if av is not None else None)
            row=dict(seed=seed,mutation=mutation,anchor=anchor,metrics=metrics);pairs.append(row);selected.append(row)
        sources.append(dict(seed=seed,mutation=mutation,metrics={k:avg([p['metrics'][k]['difference'] for p in selected]) for k in METRICS}))
    groups=[dict(mutation=m,metrics={k:avg([s['metrics'][k]['mean'] for s in sources if s['mutation']==m]) for k in METRICS}) for m in (0,100)]
    return dict(pairs=pairs,sources=sources,groups=groups)


def required_code():
    return set(Path('src/bitgenesis/v4').glob('*.py'))|{Path(p) for p in ('experiments/v4/study-014.md','scripts/run_v4_study014.py','scripts/verify_v4_study014_summary.py','scripts/run_v4_study012.py','scripts/run_v4_study011.py','scripts/run_v4_study010.py','scripts/run_v4_study009.py','scripts/verify_v4_study012_summary.py')}


def verify_files(directory,recorded,expected):
    assert set(recorded)==set(expected)
    assert {p.name for p in directory.iterdir() if p.is_file()}==set(expected)
    verify_bindings({str(directory/k):v for k,v in recorded.items()},{directory/k for k in expected})


def main():
    root=Path('data/v4-study-014');meta=read(root/'metadata.json');sources=read(root/'baseline-results.json');rows=read(root/'results.json')
    assert meta['status']=='complete' and meta['planned_sources']==meta['completed_sources']==10 and meta['planned_branches']==meta['completed_branches']==80 and meta['new_independent_sources']==5
    assert meta['storage_limit_bytes']==2*1024**3 and meta['time_limit_seconds']==2700 and meta['elapsed_seconds']<2700
    assert meta['output_sha256']=={f:digest(root/f) for f in ('baseline-results.json','results.json','summary.json')}
    verify_bindings(meta['code_sha256'],required_code())
    check_coverage(sources,('seed','mutation'),set(product(range(112000,112005),(0,100))))
    check_coverage(rows,('seed','mutation','anchor','exchange'),set(product(range(112000,112005),(0,100),(100,200,300,400),(True,False))))
    assert {p.name for p in (root/'baselines').iterdir()}=={Path(r['directory']).name for r in sources}
    assert {p.name for p in (root/'branches').iterdir()}=={Path(r['directory']).name for r in rows}
    config=dict(steps=500,width=16,height=16,occupancy=250,max_energy=64,initial_raw=1,program_mode='random',capacity=64,drive_per_thousand=250,drive_amount=8,leak=1,bond_cost=1,exchange=True,threshold=16,construction_cost=4,copy_cost=1,max_site_records=128256)
    base={};histories={};initials={};finals={};components=0
    source_files={'metadata.json','initial.json','steps.jsonl','final.json','summary.json','audit.json'}
    branch_files=source_files|{'continuity.json'}
    for r in sources:
        name=f"baselines/seed-{r['seed']}-drive-250-mutation-{r['mutation']}";assert r['directory']==name
        directory=root/name;verify_files(directory,r['files_sha256'],source_files)
        sm=read(directory/'metadata.json');assert sm['status']=='complete' and sm['seed']==r['seed'] and sm['mutation_per_thousand']==r['mutation']
        assert all(sm[k]==v for k,v in config.items()) and sm['git_commit']==meta['git_commit'] and sm['git_dirty'] is False
        assert sm['source_sha256']=={p.name:digest(p) for p in Path('src/bitgenesis/v4').glob('*.py')}
        assert sm['output_sha256']=={f:digest(directory/f) for f in ('initial.json','steps.jsonl','final.json','summary.json')}
        assert read(directory/'audit.json')==audit_baseline(directory)
        key=r['seed'],r['mutation'];base[key]=r;histories[key]=[json.loads(line) for line in (directory/'steps.jsonl').open()]
        assert len(histories[key])==500 and [h['tick'] for h in histories[key]]==list(range(1,501))
        initials[key]=read(directory/'initial.json');finals[key]=read(directory/'final.json')
        if r['mutation']==0:
            programs={tuple(u['program']) for u in initials[key]['units'] if u is not None}
            assert all(u is None or tuple(u['program']) in programs for h in histories[key] for u in h['units'])
    for seed in range(112000,112005):
        assert initials[seed,0]==initials[seed,100]
        for k in ('drive_rng','mutation_rng','direction_rng'):assert finals[seed,0][k]==finals[seed,100][k]
    branch_initials={};firsts={};checked=[]
    for r in rows:
        assert type(r['exchange']) is bool and r['status']=='complete'
        name=f"branches/seed-{r['seed']}-drive-250-mutation-{r['mutation']}-anchor-{r['anchor']}-exchange-{str(r['exchange']).lower()}";assert r['directory']==name
        directory=root/name;verify_files(directory,r['files_sha256'],branch_files)
        sm=read(directory/'metadata.json');audit=read(directory/'audit.json');key=r['seed'],r['mutation'];source=root/base[key]['directory']
        assert sm['status']=='complete' and sm['anchor']==r['anchor'] and sm['horizon']==100 and sm['exchange'] is r['exchange'] and Path(sm['source']).resolve()==source.resolve()
        assert sm['source_sha256']==sm['source_sha256_after']==audit['input_sha256']==base[key]['files_sha256']
        assert sm['source_audit']==read(source/'audit.json')
        assert sm['code_sha256']=={p.name:digest(p) for p in Path('src/bitgenesis/v4').glob('*.py')}
        assert sm['output_sha256']==audit['output_sha256']=={f:digest(directory/f) for f in ('initial.json','steps.jsonl','final.json','summary.json','continuity.json')}
        assert audit['ticks']==100 and audit['auditor_sha256']==digest('src/bitgenesis/v4/exchange_branch_audit.py')
        initial=read(directory/'initial.json');final=read(directory/'final.json');origin=histories[key][r['anchor']-1]
        assert initial['units']==origin['units'] and initial['raw']==origin['raw'] and initial['source_tick']==r['anchor'] and initial['tick']==0
        pairkey=key+(r['anchor'],);branch_initials[pairkey,r['exchange']]=initial
        steps=[json.loads(line) for line in (directory/'steps.jsonl').open()];assert len(steps)==100
        for t,row in enumerate(steps,1):
            assert row['tick']==t and row['source_tick']==r['anchor']+t
            physical=row['physical'];tape=histories[key][r['anchor']+t-1]
            assert physical['directions']==tape['directions'] and physical['mutation_tickets']==tape['mutation_tickets']
            assert [p['proposed'] for p in physical['driven']['inputs']]==[p['proposed'] for p in tape['driven']['inputs']]
            if r['exchange']:assert physical==tape
            else:assert not physical['driven']['interaction']['transfers']
        firsts[pairkey,r['exchange']]=steps[0]['physical']
        assert final['site_ids']==steps[-1]['site_ids'] and final['units']==steps[-1]['physical']['units']
        ids=[i for i in final['site_ids'] if i is not None];assert len(ids)==len(set(ids))
        assert [i is not None for i in final['site_ids']]==[u is not None for u in final['units']]
        assert r['occupied']==len(ids)
        records=read(directory/'continuity.json');counts=recount(records);assert counts==r['components'];components+=len(records)
        checked.append(dict(r,occupied=len(ids),components=counts))
    for key in product(range(112000,112005),(0,100),(100,200,300,400)):
        assert branch_initials[key,True]==branch_initials[key,False]
        a,b=firsts[key,True]['driven'],firsts[key,False]['driven']
        assert {k:v for k,v in a.items() if k!='interaction'}=={k:v for k,v in b.items() if k!='interaction'}
        assert a['interaction']['bonds']==b['interaction']['bonds'] and a['interaction']['spent']==b['interaction']['spent']
    assert read(root/'summary.json')==aggregate_saved(checked)
    verify_bindings(meta['code_sha256'],required_code())
    for r in sources:verify_files(root/r['directory'],r['files_sha256'],source_files)
    for r in rows:verify_files(root/r['directory'],r['files_sha256'],branch_files)
    assert meta['output_sha256']=={f:digest(root/f) for f in ('baseline-results.json','results.json','summary.json')}
    proof=dict(status='verified',new_independent_sources=5,baselines=10,branches=80,pairs=40,component_records=components,baseline_steps=5000,branch_steps=8000,replayed_on_steps=4000,
        metadata_sha256=digest(root/'metadata.json'),baseline_results_sha256=digest(root/'baseline-results.json'),results_sha256=digest(root/'results.json'),summary_sha256=digest(root/'summary.json'),verifier_sha256=digest(Path(__file__)),
        scope='fresh baseline audit; all saved branch audit/output bindings; complete initial/tape/first-step isolation; independent primary identity count, component recount and exact source means')
    with (root/'aggregation-verification.json').open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':
    try:main()
    except BaseException as e:
        p=Path('data/v4-study-014/verification-failure.json')
        if p.parent.is_dir() and not p.exists():
            with p.open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(e).__name__}: {e}'))+'\n')
        raise
