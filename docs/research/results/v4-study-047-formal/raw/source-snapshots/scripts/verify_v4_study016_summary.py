"""Independent fixed-horizon ancestry recount, prefix recovery and cohort means."""
from pathlib import Path
from fractions import Fraction
from itertools import product
import json
from scripts.history_population_inputs import bindings as prior_bindings,read,digest
from scripts.verify_v4_study014_summary import verify_files
from scripts.verify_v4_study012_summary import recount,check_coverage
from scripts.history_exchange_audit import audit as branch_audit
from bitgenesis.v4.exchange_branch_audit import continuity

METRICS=('occupied','continuous','replacement','endpoint_closed','lineage_survival','original_retention','descendants')
TICKS=(100,200,300,400)


def inputs():
    result=prior_bindings()
    for name in ('experiments/v4/study-016.md','scripts/run_v4_study016.py','scripts/verify_v4_study016_summary.py'):result[name]=digest(name)
    return dict(sorted(result.items()))


def average(values):
    present=[Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(present)/len(present)) if present else None,available=len(present),missing=len(values)-len(present))


def checkpoint_recount(initial,rows,final,checkpoints=TICKS):
    assert checkpoints and all(type(t) is int and 0<t<=len(rows) for t in checkpoints)
    assert len(set(checkpoints))==len(checkpoints)
    series={0:initial['observation']['components']['material']}
    for t,row in enumerate(rows,1):
        assert row['tick']==t;series[t]=row['observation']['components']['material']
    return {str(t):continuity({i:series[i] for i in range(t+1)},final['parents']) for t in checkpoints}


def aggregate_saved(rows):
    check_coverage(rows,('history','seed','mutation','exchange'),set(product((True,False),range(112000,112005),(0,100),(True,False))))
    for r in rows:
        assert type(r['history']) is bool and type(r['exchange']) is bool and r['status']=='complete' and r['anchor']==100 and r['horizon']==400
        assert set(r['checkpoints'])=={str(t) for t in TICKS}
        for value in r['checkpoints'].values():assert type(value['occupied']) is int and 0<=value['occupied']<=256
    index={(r['history'],r['seed'],r['mutation'],r['exchange']):r for r in rows}
    def scalar(row,t,k):return str(row['checkpoints'][str(t)]['occupied']) if k=='occupied' else row['checkpoints'][str(t)]['components']['fractions'][k]
    cells=[]
    for h,m,e,t in product((True,False),(0,100),(True,False),TICKS):
        cells.append(dict(history=h,mutation=m,exchange=e,tick=t,metrics={k:average([scalar(index[h,seed,m,e],t,k) for seed in range(112000,112005)]) for k in METRICS}))
    pairs=[]
    for h,seed,m in product((True,False),range(112000,112005),(0,100)):
        a,b=index[h,seed,m,True],index[h,seed,m,False];checkpoints={}
        for t in TICKS:
            ac,bc=a['checkpoints'][str(t)]['components'],b['checkpoints'][str(t)]['components']
            assert all(ac[k]==bc[k] for k in ('eligible_components','initial_components'))
            metrics={}
            for k in METRICS:
                av,bv=scalar(a,t,k),scalar(b,t,k);assert (av is None)==(bv is None)
                metrics[k]=dict(on=av,off=bv,difference=str(Fraction(av)-Fraction(bv)) if av is not None else None)
            checkpoints[str(t)]=metrics
        pairs.append(dict(history=h,seed=seed,mutation=m,checkpoints=checkpoints))
    groups=[]
    for h,m,t in product((True,False),(0,100),TICKS):
        selected=[p for p in pairs if p['history'] is h and p['mutation']==m]
        groups.append(dict(history=h,mutation=m,tick=t,metrics={k:average([p['checkpoints'][str(t)][k]['difference'] for p in selected]) for k in METRICS}))
    return dict(cells=cells,pairs=pairs,groups=groups)


def checkpoint_index(saved):
    assert all(type(r['history']) is bool and type(r['exchange']) is bool for r in saved)
    check_coverage(saved,('history','seed','mutation','exchange'),set(product((True,False),range(112000,112005),(0,100),(True,False))))
    return {(r['history'],r['seed'],r['mutation'],r['exchange']):r['records'] for r in saved}


def main():
    root=Path('data/v4-study-016');names=('metadata.json','results.json','checkpoints.json','summary.json');before={n:digest(root/n) for n in names}
    meta=read(root/'metadata.json');rows=read(root/'results.json');saved=read(root/'checkpoints.json')
    assert meta['status']=='complete' and meta['planned_branches']==meta['completed_branches']==40 and meta['new_independent_sources']==0 and meta['reused_independent_sources']==5
    assert meta['time_limit_seconds']==2700 and meta['storage_limit_bytes']==4*1024**3 and meta['elapsed_seconds']<2700
    assert sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<4*1024**3
    assert meta['input_sha256']==meta['input_sha256_after']==inputs()
    assert meta['output_sha256']=={n:digest(root/n) for n in names[1:]}
    grid=set(product((True,False),range(112000,112005),(0,100),(True,False)))
    check_coverage(rows,('history','seed','mutation','exchange'),grid);check_coverage(saved,('history','seed','mutation','exchange'),grid)
    assert {p.name for p in (root/'branches').iterdir()}=={Path(r['directory']).name for r in rows}
    records_index=checkpoint_index(saved)
    files={'metadata.json','initial.json','steps.jsonl','final.json','continuity.json','summary.json','audit.json'}
    checked=[];initials={};record_count=0
    for r in rows:
        h,seed,m,e=r['history'],r['seed'],r['mutation'],r['exchange']
        assert type(h) is bool and type(e) is bool and r['status']=='complete' and r['anchor']==100 and r['horizon']==400
        name=f"branches/history-{str(h).lower()}-seed-{seed}-mutation-{m}-exchange-{str(e).lower()}";assert r['directory']==name
        directory=root/name;verify_files(directory,r['files_sha256'],files)
        prior=Path('data/v4-study-014' if h else 'data/v4-study-015');source=prior/f'baselines/seed-{seed}-drive-250-mutation-{m}'
        old=prior/f'branches/seed-{seed}-drive-250-mutation-{m}-anchor-100-exchange-{str(e).lower()}'
        bm=read(directory/'metadata.json');assert bm['schema']=='v4-history-exchange-branch-1' and bm['source_exchange'] is h and bm['exchange'] is e and bm['anchor']==100 and bm['horizon']==400 and bm['status']=='complete'
        assert Path(bm['source']).resolve()==source.resolve() and read(source/'metadata.json')['exchange'] is h
        audit=branch_audit(directory,source);assert read(directory/'audit.json')==audit and audit['ticks']==400
        assert (directory/'initial.json').read_bytes()==(old/'initial.json').read_bytes()
        lines=(directory/'steps.jsonl').read_bytes().splitlines(keepends=True);assert len(lines)==400
        assert b''.join(lines[:100])==(old/'steps.jsonl').read_bytes()
        initial=read(directory/'initial.json');steps=[json.loads(line) for line in lines];final=read(directory/'final.json');old_final=read(old/'final.json')
        assert steps[99]['site_ids']==old_final['site_ids'] and steps[99]['physical']['units']==old_final['units'] and steps[99]['physical']['raw']==old_final['raw']
        n=len(old_final['parents']);assert final['parents'][:n]==old_final['parents']
        assert [t if t is not None and t<=100 else None for t in final['death_ticks'][:n]]==old_final['death_ticks']
        records=checkpoint_recount(initial,steps,final)
        assert records==records_index[h,seed,m,e] and records['100']==read(old/'continuity.json') and records['400']==read(directory/'continuity.json')
        snapshots={}
        for t in TICKS:
            ids=[i for i in steps[t-1]['site_ids'] if i is not None];assert len(ids)==len(set(ids))
            snapshots[str(t)]=dict(occupied=len(ids),components=recount(records[str(t)]));record_count+=len(records[str(t)])
        assert snapshots==r['checkpoints']
        for earlier,later in zip(TICKS,TICKS[1:]):
            for a,b in zip(records[str(earlier)],records[str(later)]):
                assert a['anchor_members']==b['anchor_members'] and (not b['continuous_closed_multi'] or a['continuous_closed_multi'])
        initials[h,seed,m,e]=initial;checked.append(dict(r,checkpoints=snapshots))
    for h,seed,m in product((True,False),range(112000,112005),(0,100)):assert initials[h,seed,m,True]==initials[h,seed,m,False]
    assert read(root/'summary.json')==aggregate_saved(checked)
    assert meta['input_sha256']==inputs() and before=={n:digest(root/n) for n in names}
    for r in rows:verify_files(root/r['directory'],r['files_sha256'],files)
    proof=dict(status='verified',branches=40,pairs=20,checkpoints=4,component_records=record_count,generated_branch_steps=16000,same_history_replayed_steps=8000,opposite_history_replayed_prefix_steps=2000,new_intervention_suffix_steps=6000,new_independent_sources=0,reused_independent_sources=5,
        metadata_sha256=digest(root/'metadata.json'),results_sha256=digest(root/'results.json'),checkpoints_sha256=digest(root/'checkpoints.json'),summary_sha256=digest(root/'summary.json'),verifier_sha256=digest(Path(__file__)),input_files=len(meta['input_sha256']),scope='fresh 400-step physics/ancestry audits; exact old 100-step prefixes; independent four original-cohort continuity checkpoints and single-anchor source means')
    with (root/'aggregation-verification.json').open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':
    try:main()
    except BaseException as error:
        p=Path('data/v4-study-016/verification-failure.json')
        if p.parent.is_dir() and not p.exists():
            with p.open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise
