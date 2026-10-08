"""All saved population paths, event-led accounting and exact history effects."""
import json
import subprocess
import time
from fractions import Fraction
from pathlib import Path
from itertools import product
from scripts.history_population_inputs import bindings,read,digest,grid

METRICS=('occupied','births','deaths','original_survivors','new_survivors')
OUTPUT=Path('data/v4-study-015-population-paths')
SECONDS=1200
STORAGE=200*1024**2


def census(initial,rows,final):
    ids=list(initial['site_ids']);original={i for i in ids if i is not None};seen=set(original);born=dead=0
    if len(original)!=sum(i is not None for i in ids):raise ValueError('duplicate initial identity')
    path=[dict(tick=0,occupied=len(original),births=0,deaths=0,original_survivors=len(original),new_survivors=0)]
    for tick,row in enumerate(rows,1):
        if row['tick']!=tick:raise ValueError('tick coverage')
        previous=list(ids)
        for site in row['physical']['material']['dissolved']:
            if ids[site] is None:raise ValueError('death at empty position')
            ids[site]=None;dead+=1
        for p in row['physical']['material']['proposals']:
            if p['reason']!='formed':continue
            actor,target=p['source'],p['target'];child=row['site_ids'][target]
            if previous[actor] is None or ids[actor]!=previous[actor] or ids[target] is not None or child is None or child in seen or child>=len(final['parents']) or final['parents'][child]!=previous[actor]:raise ValueError('invalid birth identity')
            ids[target]=child;seen.add(child);born+=1
        if ids!=row['site_ids']:raise ValueError('event identity mismatch')
        if [i is not None for i in ids]!=[u is not None for u in row['physical']['units']]:raise ValueError('physical occupancy mismatch')
        alive={i for i in ids if i is not None}
        if len(alive)!=sum(i is not None for i in ids):raise ValueError('duplicate identity')
        originals=len(alive&original)
        if len(alive)!=len(original)+born-dead:raise ValueError('population ledger')
        path.append(dict(tick=tick,occupied=len(alive),births=born,deaths=dead,original_survivors=originals,new_survivors=len(alive)-originals))
    if ids!=final['site_ids']:raise ValueError('final identity mismatch')
    return path


def history_summary(branches):
    expected=set(product(range(112000,112005),(0,100),(100,200,300,400),(True,False)))
    keys=[(r['seed'],r['mutation'],r['anchor'],r['exchange']) for r in branches]
    if len(keys)!=80 or set(keys)!=expected:raise ValueError('complete unique branch grid')
    index=dict(zip(keys,branches));pairs=[]
    for seed,mut,anchor in product(range(112000,112005),(0,100),(100,200,300,400)):
        on=index[seed,mut,anchor,True]['path'];off=index[seed,mut,anchor,False]['path']
        if len(on)!=101 or len(off)!=101 or on[0]!=off[0]:raise ValueError('complete common population initial state')
        path=[]
        for t,(a,b) in enumerate(zip(on,off)):
            if a['tick']!=t or b['tick']!=t:raise ValueError('paired tick coverage')
            path.append(dict(tick=t,on={k:a[k] for k in METRICS},off={k:b[k] for k in METRICS},differences={k:a[k]-b[k] for k in METRICS}))
        pairs.append(dict(seed=seed,mutation=mut,anchor=anchor,path=path))
    sources=[]
    for seed,mut in product(range(112000,112005),(0,100)):
        chosen=[p for p in pairs if (p['seed'],p['mutation'])==(seed,mut)]
        path=[dict(tick=t,**{side:{k:str(Fraction(sum(p['path'][t][side][k] for p in chosen),4)) for k in METRICS} for side in ('on','off','differences')}) for t in range(101)]
        sources.append(dict(seed=seed,mutation=mut,path=path))
    groups=[]
    for mut in (0,100):
        chosen=[s for s in sources if s['mutation']==mut];ps=[p for p in pairs if p['mutation']==mut];path=[]
        for t in range(101):
            metrics={k:dict(on=str(sum(Fraction(s['path'][t]['on'][k]) for s in chosen)/5),off=str(sum(Fraction(s['path'][t]['off'][k]) for s in chosen)/5),difference=str(sum(Fraction(s['path'][t]['differences'][k]) for s in chosen)/5),positive=sum(p['path'][t]['differences'][k]>0 for p in ps),zero=sum(p['path'][t]['differences'][k]==0 for p in ps),negative=sum(p['path'][t]['differences'][k]<0 for p in ps)) for k in METRICS}
            path.append(dict(tick=t,metrics=metrics))
        groups.append(dict(mutation=mut,source_count=5,pair_count=20,path=path))
    return dict(pairs=pairs,sources=sources,groups=groups)


def validate_path(path):
    if len(path)!=101:raise ValueError('complete population horizon')
    previous=None
    for t,row in enumerate(path):
        if row['tick']!=t or any(type(row[k]) is not int or row[k]<0 for k in METRICS):raise ValueError('population counts')
        if row['occupied']>256 or row['occupied']!=path[0]['occupied']+row['births']-row['deaths'] or row['occupied']!=row['original_survivors']+row['new_survivors']:raise ValueError('population identities')
        if t==0 and (row['births'] or row['deaths'] or row['new_survivors']):raise ValueError('initial ledger')
        if previous and (row['births']<previous['births'] or row['deaths']<previous['deaths'] or row['original_survivors']>previous['original_survivors']):raise ValueError('invalid cumulative counts')
        previous=row


def aggregate(branches):
    keys=[(r['history'],r['seed'],r['mutation'],r['anchor'],r['exchange']) for r in branches]
    expected=set(product((True,False),range(112000,112005),(0,100),(100,200,300,400),(True,False)))
    if len(keys)!=160 or set(keys)!=expected or any(type(r['history']) is not bool or type(r['exchange']) is not bool for r in branches):raise ValueError('complete two-history branch grid')
    for r in branches:validate_path(r['path'])
    histories={name:history_summary([r for r in branches if r['history'] is flag]) for name,flag in (('on',True),('off',False))}
    on={(r['seed'],r['mutation'],r['anchor']):r for r in histories['on']['pairs']};pairs=[]
    for r in histories['off']['pairs']:
        key=r['seed'],r['mutation'],r['anchor'];path=[]
        for t in range(101):
            a=on[key]['path'][t]['differences'];b=r['path'][t]['differences']
            path.append(dict(tick=t,on_history=a,off_history=b,differences={k:b[k]-a[k] for k in METRICS}))
        pairs.append(dict(seed=r['seed'],mutation=r['mutation'],anchor=r['anchor'],path=path))
    sources=[]
    for seed,mut in product(range(112000,112005),(0,100)):
        ps=[p for p in pairs if (p['seed'],p['mutation'])==(seed,mut)]
        path=[dict(tick=t,**{side:{k:str(Fraction(sum(p['path'][t][side][k] for p in ps),4)) for k in METRICS} for side in ('on_history','off_history','differences')}) for t in range(101)]
        sources.append(dict(seed=seed,mutation=mut,path=path))
    groups=[]
    for mut in (0,100):
        ss=[a for a in sources if a['mutation']==mut];ps=[p for p in pairs if p['mutation']==mut];path=[]
        for t in range(101):
            metrics={k:dict(on_history=str(sum(Fraction(a['path'][t]['on_history'][k]) for a in ss)/5),off_history=str(sum(Fraction(a['path'][t]['off_history'][k]) for a in ss)/5),difference=str(sum(Fraction(a['path'][t]['differences'][k]) for a in ss)/5),positive=sum(p['path'][t]['differences'][k]>0 for p in ps),zero=sum(p['path'][t]['differences'][k]==0 for p in ps),negative=sum(p['path'][t]['differences'][k]<0 for p in ps)) for k in METRICS}
            path.append(dict(tick=t,metrics=metrics))
        groups.append(dict(mutation=mut,source_count=5,pair_count=20,path=path))
    return dict(histories=histories,interaction=dict(pairs=pairs,sources=sources,groups=groups))


def verify_endpoints(summary):
    original=read('data/v4-study-015/summary.json')
    for history in ('on','off'):
        index={(p['seed'],p['mutation'],p['anchor']):p for p in original['histories'][history]['pairs']}
        for pair in summary['histories'][history]['pairs']:
            actual=pair['path'][100];expected=index[pair['seed'],pair['mutation'],pair['anchor']]['metrics']['occupied']
            for k,field in (('on','on'),('off','off'),('differences','difference')):
                if Fraction(actual[k]['occupied'])!=Fraction(expected[field]):raise ValueError('published endpoint mismatch')
    index={(p['seed'],p['mutation'],p['anchor']):p for p in original['interaction']['pairs']}
    for pair in summary['interaction']['pairs']:
        expected=index[pair['seed'],pair['mutation'],pair['anchor']]['metrics']['occupied']
        for k,field in (('on_history','on_history'),('off_history','off_history'),('differences','difference')):
            if Fraction(pair['path'][100][k]['occupied'])!=Fraction(expected[field]):raise ValueError('published interaction mismatch')


def save(p,v):Path(p).write_text(json.dumps(v,separators=(',',':'))+'\n')


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():raise ValueError('clean launch required')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic()
    meta=dict(status='running',completed_branches=0,independent_new_samples=0,new_simulation_steps=0,time_limit_seconds=SECONDS,storage_limit_bytes=STORAGE)
    save(OUTPUT/'metadata.json',meta);results=[]
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();meta['input_sha256']=bindings();save(OUTPUT/'metadata.json',meta)
        for r in grid():
            if time.monotonic()-started>=SECONDS:meta['status']='time_limit';return
            if sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())>=STORAGE:meta['status']='storage_limit';return
            directory=Path(r['directory']);rows=[json.loads(line) for line in (directory/'steps.jsonl').open()]
            path=census(read(directory/'initial.json'),rows,read(directory/'final.json'));validate_path(path)
            results.append(dict(r,path=path));meta['completed_branches']=len(results)
            save(OUTPUT/'branches.json',results);save(OUTPUT/'metadata.json',meta)
        summary=aggregate(results);verify_endpoints(summary)
        save(OUTPUT/'summary.json',summary);meta['input_sha256_after']=bindings()
        if meta['input_sha256']!=meta['input_sha256_after']:raise ValueError('inputs changed')
        if time.monotonic()-started>=SECONDS:meta['status']='time_limit';return
        if sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())>=STORAGE:meta['status']='storage_limit';return
        meta.update(status='complete',output_sha256={n:digest(OUTPUT/n) for n in ('branches.json','summary.json')})
    except BaseException as e:
        meta.update(status='failed',error=f'{type(e).__name__}: {e}');raise
    finally:
        meta['elapsed_seconds']=time.monotonic()-started;save(OUTPUT/'metadata.json',meta)


if __name__=='__main__':main()
