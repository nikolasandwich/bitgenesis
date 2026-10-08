"""Fixed paired history comparison; no new independent random sources."""
import json
import subprocess
import time
from pathlib import Path
from fractions import Fraction
from itertools import product
from hashlib import sha256
from bitgenesis.v4.hereditary_runner import run as baseline_run,save
from bitgenesis.v4.hereditary_audit import audit as baseline_audit
from scripts.history_exchange_branch import run as branch_run
from scripts.study015_inputs import OLD_ROOT,code_paths,old_bindings,verify_old
from scripts.run_v4_study014 import aggregate as within_history
from scripts.run_v4_study012 import summarize

ROOT=Path('data/v4-study-015')
SEEDS=range(112000,112005)
ANCHORS=(100,200,300,400)
COMPONENT_METRICS=('continuous','replacement','endpoint_closed','lineage_survival','original_retention','descendants')
METRICS=('occupied',)+COMPONENT_METRICS
BASE=dict(steps=500,width=16,height=16,occupancy=250,max_energy=64,initial_raw=1,program_mode='random',capacity=64,drive_per_thousand=250,drive_amount=8,leak=1,bond_cost=1,exchange=False,threshold=16,construction_cost=4,copy_cost=1,max_site_records=128256)
STORAGE=2*1024**3
SECONDS=45*60
read=lambda p:json.loads(Path(p).read_text())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()


def require(ok,msg):
    if not ok:raise ValueError(msg)


def hashes(root):return {p.name:digest(p) for p in Path(root).iterdir() if p.is_file()}


def average(values):
    good=[Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(good)/len(good)) if good else None,available=len(good),missing=len(values)-len(good))


def aggregate(results,old_results):
    histories=dict(on=within_history(old_results),off=within_history(results))
    old={(p['seed'],p['mutation'],p['anchor']):p for p in histories['on']['pairs']}
    pairs=[]
    for p in histories['off']['pairs']:
        key=p['seed'],p['mutation'],p['anchor'];metrics={}
        for k in METRICS:
            a=old[key]['metrics'][k]['difference'];b=p['metrics'][k]['difference']
            metrics[k]=dict(on_history=a,off_history=b,difference=str(Fraction(b)-Fraction(a)) if a is not None and b is not None else None)
        pairs.append(dict(seed=p['seed'],mutation=p['mutation'],anchor=p['anchor'],metrics=metrics))
    sources=[dict(seed=seed,mutation=m,metrics={k:average([p['metrics'][k]['difference'] for p in pairs if (p['seed'],p['mutation'])==(seed,m)]) for k in METRICS}) for seed,m in product(SEEDS,(0,100))]
    groups=[dict(mutation=m,metrics={k:average([s['metrics'][k]['mean'] for s in sources if s['mutation']==m]) for k in METRICS}) for m in (0,100)]
    return dict(histories=histories,interaction=dict(pairs=pairs,sources=sources,groups=groups))


def main():
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch required')
    ROOT.mkdir(exist_ok=False);started=time.monotonic()
    meta=dict(status='running',planned_sources=10,completed_sources=0,new_independent_sources=0,reused_independent_sources=5,planned_branches=80,completed_branches=0,storage_limit_bytes=STORAGE,time_limit_seconds=SECONDS)
    save(ROOT/'metadata.json',meta);sources=[];results=[]
    def check():
        require(meta['code_sha256']=={str(p):digest(p) for p in code_paths()},'code changed')
        verify_old(meta['old_sha256'])
        for source in sources:require(source['files_sha256']==hashes(ROOT/source['directory']),'baseline changed')
        if time.monotonic()-started>=SECONDS:return 'time_limit'
        if sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())>=STORAGE:return 'storage_limit'
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();meta['code_sha256']={str(p):digest(p) for p in code_paths()}
        meta['old_sha256']=old_bindings()
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
            new=ROOT/source['directory'];old=OLD_ROOT/source['directory']
            require(read(new/'initial.json')==read(old/'initial.json'),'history initial pairing')
            for k in ('mutation_rng','drive_rng','direction_rng'):require(read(new/'final.json')[k]==read(old/'final.json')[k],'history stream pairing')
            ns=[json.loads(line) for line in (new/'steps.jsonl').open()];os=[json.loads(line) for line in (old/'steps.jsonl').open()]
            require(len(ns)==len(os)==500,'complete paired history')
            if source['mutation']==0:
                programs={tuple(u['program']) for u in read(new/'initial.json')['units'] if u is not None}
                require(all(u is None or tuple(u['program']) in programs for row in ns for u in row['units']),'all-step mutation-zero control')
            for n,o in zip(ns,os):
                require(n['directions']==o['directions'] and n['mutation_tickets']==o['mutation_tickets'],'history random tape')
                require([i['proposed'] for i in n['driven']['inputs']]==[i['proposed'] for i in o['driven']['inputs']],'history drive tape')
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
        save(ROOT/'summary.json',aggregate(results,read(OLD_ROOT/'results.json')));meta['status']='complete'
        meta['output_sha256']={name:digest(ROOT/name) for name in ('baseline-results.json','results.json','summary.json')}
    except BaseException as e:
        meta.update(status='failed',error=f'{type(e).__name__}: {e}');raise
    finally:
        meta['elapsed_seconds']=time.monotonic()-started;save(ROOT/'metadata.json',meta)


if __name__=='__main__':main()
