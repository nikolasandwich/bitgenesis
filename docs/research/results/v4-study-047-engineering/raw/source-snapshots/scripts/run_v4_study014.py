"""Prospective fixed five-source exchange replication, unchanged world rules."""
import json
import subprocess
import time
from pathlib import Path
from fractions import Fraction
from itertools import product
from hashlib import sha256
from bitgenesis.v4.hereditary_runner import run as baseline_run,save
from bitgenesis.v4.hereditary_audit import audit as baseline_audit
from bitgenesis.v4.exchange_branch import run as branch_run
from scripts.run_v4_study012 import summarize

ROOT=Path('data/v4-study-014')
SEEDS=range(112000,112005)
ANCHORS=(100,200,300,400)
COMPONENT_METRICS=('continuous','replacement','endpoint_closed','lineage_survival','original_retention','descendants')
METRICS=('occupied',)+COMPONENT_METRICS
BASE=dict(steps=500,width=16,height=16,occupancy=250,max_energy=64,initial_raw=1,program_mode='random',capacity=64,drive_per_thousand=250,drive_amount=8,leak=1,bond_cost=1,exchange=True,threshold=16,construction_cost=4,copy_cost=1,max_site_records=128256)
STORAGE=2*1024**3
SECONDS=45*60
read=lambda p:json.loads(Path(p).read_text())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()


def require(ok,msg):
    if not ok:raise ValueError(msg)


def hashes(root):return {p.name:digest(p) for p in Path(root).iterdir() if p.is_file()}


def code_paths():
    return sorted(set(Path('src/bitgenesis/v4').glob('*.py'))|{Path(p) for p in ('experiments/v4/study-014.md','scripts/run_v4_study014.py','scripts/verify_v4_study014_summary.py','scripts/run_v4_study012.py','scripts/run_v4_study011.py','scripts/run_v4_study010.py','scripts/run_v4_study009.py','scripts/verify_v4_study012_summary.py')})


def average(values):
    good=[Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(good)/len(good)) if good else None,available=len(good),missing=len(values)-len(good))


def aggregate(results):
    keys=[(r['seed'],r['mutation'],r['anchor'],r['exchange']) for r in results]
    require(len(keys)==80 and set(keys)==set(product(SEEDS,(0,100),ANCHORS,(True,False))),'complete unique branch grid')
    require(all(r['status']=='complete' and type(r['exchange']) is bool and type(r['occupied']) is int and 0<=r['occupied']<=256 for r in results),'complete finite population')
    index=dict(zip(keys,results));pairs=[]
    for seed,mutation,anchor in product(SEEDS,(0,100),ANCHORS):
        a,b=index[seed,mutation,anchor,True],index[seed,mutation,anchor,False]
        require(all(a['components'][k]==b['components'][k] for k in ('initial_components','eligible_components')),'paired initial denominators')
        metrics={}
        for k in METRICS:
            on=str(a['occupied']) if k=='occupied' else a['components']['fractions'][k]
            off=str(b['occupied']) if k=='occupied' else b['components']['fractions'][k]
            require((on is None)==(off is None),'paired missingness')
            metrics[k]=dict(on=on,off=off,difference=str(Fraction(on)-Fraction(off)) if on is not None else None)
        pairs.append(dict(seed=seed,mutation=mutation,anchor=anchor,metrics=metrics))
    sources=[dict(seed=seed,mutation=m,metrics={k:average([p['metrics'][k]['difference'] for p in pairs if (p['seed'],p['mutation'])==(seed,m)]) for k in METRICS}) for seed,m in product(SEEDS,(0,100))]
    groups=[dict(mutation=m,metrics={k:average([s['metrics'][k]['mean'] for s in sources if s['mutation']==m]) for k in METRICS}) for m in (0,100)]
    return dict(pairs=pairs,sources=sources,groups=groups)


def main():
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch required')
    ROOT.mkdir(exist_ok=False);started=time.monotonic()
    meta=dict(status='running',planned_sources=10,completed_sources=0,new_independent_sources=5,planned_branches=80,completed_branches=0,storage_limit_bytes=STORAGE,time_limit_seconds=SECONDS)
    save(ROOT/'metadata.json',meta);sources=[];results=[]
    def check():
        require(meta['code_sha256']=={str(p):digest(p) for p in code_paths()},'code changed')
        for source in sources:require(source['files_sha256']==hashes(ROOT/source['directory']),'baseline changed')
        if time.monotonic()-started>=SECONDS:return 'time_limit'
        if sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())>=STORAGE:return 'storage_limit'
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();meta['code_sha256']={str(p):digest(p) for p in code_paths()}
        save(ROOT/'metadata.json',meta);save(ROOT/'baseline-results.json',sources);save(ROOT/'results.json',results)
        for seed,mutation in product(SEEDS,(0,100)):
            limit=check()
            if limit:meta['status']=limit;return
            relative=f'baselines/seed-{seed}-drive-250-mutation-{mutation}';directory=ROOT/relative
            baseline_run(directory,seed,mutation_per_thousand=mutation,**BASE)
            checked=baseline_audit(directory);save(directory/'audit.json',checked)
            source=dict(seed=seed,mutation=mutation,directory=relative,files_sha256=hashes(directory));sources.append(source)
            meta['completed_sources']=len(sources);save(ROOT/'baseline-results.json',sources);save(ROOT/'metadata.json',meta)
            print(f'baseline {len(sources)}/10: {seed} mutation{mutation}',flush=True)
        for seed in SEEDS:
            a=ROOT/f'baselines/seed-{seed}-drive-250-mutation-0';b=ROOT/f'baselines/seed-{seed}-drive-250-mutation-100'
            require(read(a/'initial.json')==read(b/'initial.json'),'paired baseline initial state')
            for k in ('mutation_rng','drive_rng','direction_rng'):require(read(a/'final.json')[k]==read(b/'final.json')[k],'paired random stream')
            programs={tuple(u['program']) for u in read(a/'initial.json')['units'] if u is not None}
            require(all(u is None or tuple(u['program']) in programs for u in read(a/'final.json')['units']),'mutation-zero control')
        for source in sources:
            seed,mutation=source['seed'],source['mutation']
            for anchor,exchange in product(ANCHORS,(True,False)):
                limit=check()
                if limit:meta['status']=limit;return
                relative=f'branches/seed-{seed}-drive-250-mutation-{mutation}-anchor-{anchor}-exchange-{str(exchange).lower()}';directory=ROOT/relative
                value=branch_run(directory,ROOT/source['directory'],anchor,100,exchange)
                require(read(directory/'metadata.json')['status']=='complete','branch complete')
                occupied=sum(u is not None for u in read(directory/'final.json')['units'])
                results.append(dict(seed=seed,mutation=mutation,anchor=anchor,exchange=exchange,status='complete',directory=relative,occupied=occupied,components=summarize(value['records']),files_sha256=hashes(directory)))
                meta['completed_branches']=len(results);save(ROOT/'results.json',results);save(ROOT/'metadata.json',meta)
                print(f'branch {len(results)}/80: {directory.name}',flush=True)
        limit=check()
        if limit:meta['status']=limit;return
        save(ROOT/'summary.json',aggregate(results));meta['status']='complete'
        meta['output_sha256']={name:digest(ROOT/name) for name in ('baseline-results.json','results.json','summary.json')}
    except BaseException as e:
        meta.update(status='failed',error=f'{type(e).__name__}: {e}');raise
    finally:
        meta['elapsed_seconds']=time.monotonic()-started;save(ROOT/'metadata.json',meta)


if __name__=='__main__':main()
