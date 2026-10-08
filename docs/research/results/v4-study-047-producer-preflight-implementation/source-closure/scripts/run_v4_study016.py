"""One fixed four-hundred-step continuity window, preserving original anchors."""
import json
import subprocess
import time
from fractions import Fraction
from itertools import product
from pathlib import Path
from bitgenesis.v4.hereditary_runner import save
from bitgenesis.v4.structure_continuity import follow
from scripts.history_exchange_branch import run as branch_run
from scripts.history_population_inputs import bindings as upstream_bindings,read,digest
from scripts.run_v4_study012 import summarize

ROOT=Path('data/v4-study-016')
SEEDS=range(112000,112005)
CHECKPOINTS=(100,200,300,400)
COMPONENT_METRICS=('continuous','replacement','endpoint_closed','lineage_survival','original_retention','descendants')
METRICS=('occupied',)+COMPONENT_METRICS
SECONDS=2700
STORAGE=4*1024**3


def require(ok,message):
    if not ok:raise ValueError(message)


def bindings():
    result=upstream_bindings()
    for name in ('experiments/v4/study-016.md','scripts/run_v4_study016.py','scripts/verify_v4_study016_summary.py'):
        result[name]=digest(name)
    return dict(sorted(result.items()))


def average(values):
    present=[Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(present)/len(present)) if present else None,available=len(present),missing=len(values)-len(present))


def checkpoint_records(initial,rows,final,checkpoints=CHECKPOINTS):
    require(all(type(t) is int and 0<t<=len(rows) for t in checkpoints) and len(set(checkpoints))==len(checkpoints),'checkpoint horizon')
    series={0:initial['observation']['components']['material']}
    for tick,row in enumerate(rows,1):
        require(row['tick']==tick,'complete original-anchor series')
        series[tick]=row['observation']['components']['material']
    records=follow(series,final['parents'],0,list(checkpoints))
    previous=None
    for tick in sorted(checkpoints):
        closed={r['component'] for r in records[tick] if r['continuous_closed_multi']}
        require(previous is None or closed<=previous,'continuous closure cannot recover')
        previous=closed
    return {str(t):records[t] for t in checkpoints}


def verify_prefix(output,old,records):
    output,old=Path(output),Path(old)
    require((output/'initial.json').read_bytes()==(old/'initial.json').read_bytes(),'old initial bytes')
    prefix=b''.join((output/'steps.jsonl').read_bytes().splitlines(keepends=True)[:100])
    require(prefix==(old/'steps.jsonl').read_bytes(),'old first100 step bytes')
    require(records['100']==read(old/'continuity.json'),'old first100 component records')


def aggregate(results):
    keys=[(r['history'],r['seed'],r['mutation'],r['exchange']) for r in results]
    require(len(keys)==40 and set(keys)==set(product((True,False),SEEDS,(0,100),(True,False))),'complete unique horizon grid')
    for r in results:
        require(type(r['history']) is bool and type(r['exchange']) is bool and r['status']=='complete' and r['anchor']==100 and r['horizon']==400,'complete boolean fixed horizon')
        require(set(r['checkpoints'])=={str(t) for t in CHECKPOINTS},'all checkpoints')
        original=None
        for tick in CHECKPOINTS:
            value=r['checkpoints'][str(tick)];components=value['components']
            require(type(value['occupied']) is int and 0<=value['occupied']<=256,'world count')
            denominator=(components['initial_components'],components['eligible_components'])
            require(original is None or original==denominator,'unchanged original component eligibility')
            original=denominator
            require(set(components['fractions'])==set(COMPONENT_METRICS),'all component metrics')
            require(all((v is None)==(components['eligible_components']==0) for v in components['fractions'].values()),'component denominator missingness')
    lookup=dict(zip(keys,results));pairs=[];cells=[];groups=[]
    for history,seed,mutation in product((True,False),SEEDS,(0,100)):
        a,b=lookup[history,seed,mutation,True],lookup[history,seed,mutation,False];checkpoints={}
        for tick in CHECKPOINTS:
            on,off=a['checkpoints'][str(tick)],b['checkpoints'][str(tick)]
            require(all(on['components'][k]==off['components'][k] for k in ('initial_components','eligible_components')),'paired original eligibility')
            metrics={}
            for k in METRICS:
                av=str(on['occupied']) if k=='occupied' else on['components']['fractions'][k]
                bv=str(off['occupied']) if k=='occupied' else off['components']['fractions'][k]
                require((av is None)==(bv is None),'paired missingness')
                metrics[k]=dict(on=av,off=bv,difference=str(Fraction(av)-Fraction(bv)) if av is not None else None)
            checkpoints[str(tick)]=metrics
        pairs.append(dict(history=history,seed=seed,mutation=mutation,checkpoints=checkpoints))
    for history,mutation,exchange,tick in product((True,False),(0,100),(True,False),CHECKPOINTS):
        values=[lookup[history,seed,mutation,exchange]['checkpoints'][str(tick)] for seed in SEEDS]
        metrics={k:average([str(v['occupied']) if k=='occupied' else v['components']['fractions'][k] for v in values]) for k in METRICS}
        cells.append(dict(history=history,mutation=mutation,exchange=exchange,tick=tick,metrics=metrics))
    for history,mutation,tick in product((True,False),(0,100),CHECKPOINTS):
        chosen=[p for p in pairs if p['history'] is history and p['mutation']==mutation]
        groups.append(dict(history=history,mutation=mutation,tick=tick,metrics={k:average([p['checkpoints'][str(tick)][k]['difference'] for p in chosen]) for k in METRICS}))
    return dict(cells=cells,pairs=pairs,groups=groups)


def main():
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch required')
    ROOT.mkdir(exist_ok=False);started=time.monotonic()
    meta=dict(status='running',planned_branches=40,completed_branches=0,new_independent_sources=0,reused_independent_sources=5,time_limit_seconds=SECONDS,storage_limit_bytes=STORAGE)
    save(ROOT/'metadata.json',meta);results=[];checkpoints=[]
    def check():
        require(meta['input_sha256']==bindings(),'inputs changed')
        if time.monotonic()-started>=SECONDS:return 'time_limit'
        if sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())>=STORAGE:return 'storage_limit'
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();meta['input_sha256']=bindings()
        save(ROOT/'metadata.json',meta);save(ROOT/'results.json',results);save(ROOT/'checkpoints.json',checkpoints)
        for history,seed,mutation,exchange in product((True,False),SEEDS,(0,100),(True,False)):
            limit=check()
            if limit:meta['status']=limit;return
            upstream=Path('data/v4-study-014' if history else 'data/v4-study-015')
            source=upstream/f'baselines/seed-{seed}-drive-250-mutation-{mutation}'
            old=upstream/f'branches/seed-{seed}-drive-250-mutation-{mutation}-anchor-100-exchange-{str(exchange).lower()}'
            relative=f'branches/history-{str(history).lower()}-seed-{seed}-mutation-{mutation}-exchange-{str(exchange).lower()}';directory=ROOT/relative
            branch_run(directory,source,100,400,exchange)
            require(read(directory/'metadata.json')['status']=='complete','audited complete branch')
            rows=[json.loads(line) for line in (directory/'steps.jsonl').open()]
            require(len(rows)==400,'complete branch horizon')
            records=checkpoint_records(read(directory/'initial.json'),rows,read(directory/'final.json'))
            verify_prefix(directory,old,records)
            require(records['400']==read(directory/'continuity.json'),'full-window component records')
            values={str(t):dict(occupied=sum(u is not None for u in rows[t-1]['physical']['units']),components=summarize(records[str(t)])) for t in CHECKPOINTS}
            results.append(dict(history=history,seed=seed,mutation=mutation,exchange=exchange,anchor=100,horizon=400,status='complete',directory=relative,checkpoints=values,files_sha256={p.name:digest(p) for p in directory.iterdir() if p.is_file()}))
            checkpoints.append(dict(history=history,seed=seed,mutation=mutation,exchange=exchange,records=records))
            meta['completed_branches']=len(results);save(ROOT/'results.json',results);save(ROOT/'checkpoints.json',checkpoints);save(ROOT/'metadata.json',meta)
            print(f'{len(results)}/40 audited horizon branches: {directory.name}',flush=True)
        save(ROOT/'summary.json',aggregate(results))
        meta['input_sha256_after']=bindings();require(meta['input_sha256']==meta['input_sha256_after'],'inputs changed')
        limit=check()
        if limit:meta['status']=limit;return
        meta.update(status='complete',output_sha256={name:digest(ROOT/name) for name in ('results.json','checkpoints.json','summary.json')})
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}');raise
    finally:
        meta['elapsed_seconds']=time.monotonic()-started;save(ROOT/'metadata.json',meta)


if __name__=='__main__':main()
