"""Event-led population paths from the complete saved study012 branch grid."""
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from itertools import product
from scripts.population_path_inputs import bindings,read,digest,ROOT,reset_firsts

METRICS=('occupied','births','deaths','original_survivors','new_survivors')
OUTPUT=Path('data/v4-study-012-population-paths')


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


def aggregate(branches):
    expected=set(product(range(96000,96005),(0,100),(100,200,300,400),(True,False)))
    keys=[(r['seed'],r['mutation'],r['anchor'],r['exchange']) for r in branches]
    if len(keys)!=80 or set(keys)!=expected:raise ValueError('complete unique branch grid')
    index=dict(zip(keys,branches));pairs=[]
    for seed,mut,anchor in product(range(96000,96005),(0,100),(100,200,300,400)):
        on=index[seed,mut,anchor,True]['path'];off=index[seed,mut,anchor,False]['path']
        if len(on)!=101 or len(off)!=101 or on[0]!=off[0]:raise ValueError('complete common population initial state')
        path=[]
        for t,(a,b) in enumerate(zip(on,off)):
            if a['tick']!=t or b['tick']!=t:raise ValueError('paired tick coverage')
            path.append(dict(tick=t,on={k:a[k] for k in METRICS},off={k:b[k] for k in METRICS},differences={k:a[k]-b[k] for k in METRICS}))
        pairs.append(dict(seed=seed,mutation=mut,anchor=anchor,path=path))
    sources=[]
    for seed,mut in product(range(96000,96005),(0,100)):
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


def save(p,v):Path(p).write_text(json.dumps(v,separators=(',',':'))+'\n')


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():raise ValueError('clean launch required')
    OUTPUT.mkdir(exist_ok=False);meta=dict(status='running',completed_branches=0,independent_new_samples=0)
    save(OUTPUT/'metadata.json',meta)
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();meta['input_sha256']=bindings();save(OUTPUT/'metadata.json',meta)
        firsts=reset_firsts();results=[];history={}
        for r in read(ROOT/'results.json'):
            directory=ROOT/r['directory'];initial=read(directory/'initial.json');final=read(directory/'final.json')
            rows=[json.loads(line) for line in (directory/'steps.jsonl').open()]
            key=r['seed'],r['mutation']
            if key not in history:
                p=Path('data/v4-study-005')/f'seed-{key[0]}-drive-250-mutation-{key[1]}'/'steps.jsonl';history[key]=[json.loads(line) for line in p.open()]
            origin=history[key][r['anchor']-1]
            assert initial['units']==origin['units'] and initial['raw']==origin['raw']
            assert len(rows)==100
            path=census(initial,rows,final);arm='on' if r['exchange'] else 'off';first=firsts[r['seed'],r['mutation'],r['anchor']]
            assert rows[0]['physical']==first[arm]
            c=first['metrics']['counts'][arm]
            assert path[1]==dict(tick=1,occupied=c['occupied'],births=c['births'],deaths=c['deaths'],original_survivors=path[0]['occupied']-c['deaths'],new_survivors=c['births'])
            results.append(dict(seed=r['seed'],mutation=r['mutation'],anchor=r['anchor'],exchange=r['exchange'],directory=r['directory'],path=path))
            meta['completed_branches']=len(results)
        save(OUTPUT/'branches.json',results);save(OUTPUT/'summary.json',aggregate(results));meta['input_sha256_after']=bindings()
        assert meta['input_sha256']==meta['input_sha256_after']
        meta.update(status='complete',output_sha256={p:digest(OUTPUT/p) for p in ('branches.json','summary.json')})
    except BaseException as e:
        meta.update(status='failed',error=f'{type(e).__name__}: {e}');raise
    finally:save(OUTPUT/'metadata.json',meta)


if __name__=='__main__':main()
