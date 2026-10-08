"""Stage-local matching of saved artificial copy trajectories; no physics run."""
import json
from pathlib import Path
import subprocess
import time
from itertools import product
from bitgenesis.v4.structure import snapshot
from scripts.analyze_v4_structure_copies import canonical, episodes

MODES=('random-direction','random-feed','random-both')
GRID=tuple(product(range(120000,120020),MODES,(False,True)))
CROSSINGS=('dissolution_up','dissolution_down','formation_up','formation_down')
OUTPUT=Path('data/v4-study-020')


def require(condition,message):
    if not condition:raise ValueError(message)


def phase_step(tick,p,d,f,births,deaths):
    a,b,c=(len(v)>=2 for v in (p,d,f))
    return dict(tick=tick,previous=p,dissolved=d,final=f,births=births,deaths=deaths,
                crossings=[not a and b,a and not b,not b and c,b and not c],hidden=a==c and a!=b)


def spans(steps):
    return [dict(start=a,end=b,length=b-a+1,right_censored=b==len(steps),
                 start_step=steps[a-1],exit_step=steps[b] if b<len(steps) else None)
            for a,b in episodes([len(s['final']) for s in steps])]


def analyze_case(case):
    require(type(case['seed']) is int and type(case['exchange']) is bool and
            (case['seed'],case['mode'],case['exchange']) in GRID,'case identity')
    initial=case['initial'];parents=case['final']['parents'];roots=[]
    for i,parent in enumerate(parents):
        require(parent is None or type(parent) is int and 0<=parent<i,'ordered parent chain')
        roots.append(i if parent is None else roots[parent])
    def indexed(ids,units):
        require(len(ids)==len(units)==256,'full sites')
        found={}
        for site,i in enumerate(ids):
            require((i is None)==(units[site] is None),'unit identity occupancy')
            if i is not None:
                require(type(i) is int and 0<=i<len(parents) and i not in found,'unique valid identity')
                found[i]=site
        return found
    init_sites=indexed(initial['site_ids'],initial['units'])
    require(set(init_sites)=={0,1,2},'fixed initial identities')
    def points(group,sites,units):
        return tuple((sites[i]%16,sites[i]//16,units[sites[i]]['material'],tuple(units[sites[i]]['program'])) for i in group)
    target=canonical(points([0,1],init_sites,initial['units']))
    def matches(ids,units):
        sites=indexed(ids,units)
        groups=snapshot(units,ids,16,16,phase='final')['components']['material']
        return sorted(sorted(g) for g in groups if len(g)==2 and all(roots[i] in (0,1) for i in g)
                      and canonical(points(g,sites,units))==target)
    prev_ids=initial['site_ids'];prev_units=initial['units'];p=matches(prev_ids,prev_units)
    require(len(p)==1,'one initial match');steps=[];seen=set(init_sites)
    require(len(case['rows'])==32,'thirty-two source steps')
    for tick,row in enumerate(case['rows'],1):
        require(type(row['tick']) is int and row['tick']==tick,'ordered ticks')
        physical=row['physical'];units=physical['units'];ids=row['site_ids'];material=physical['material']
        before=indexed(prev_ids,prev_units);after=indexed(ids,units)
        dead_sites=material['dissolved'];formed=[x for x in material['proposals'] if x['reason']=='formed']
        require(len(set(dead_sites))==len(dead_sites) and all(type(s) is int and 0<=s<256 and prev_ids[s] is not None for s in dead_sites),'valid dissolution sites')
        deaths=sorted(prev_ids[s] for s in dead_sites)
        require(set(deaths)==set(before)-set(after),'death event identity coverage')
        targets=[v['target'] for v in formed]
        require(len(targets)==len(set(targets)) and all(type(s) is int and 0<=s<256 and ids[s] is not None for s in targets),'unique formation sites')
        births=sorted(ids[s] for s in targets)
        require(set(births)==set(after)-set(before) and not set(births)&seen,'birth event identity coverage')
        for event in formed:
            source=event['source'];child=ids[event['target']]
            require(type(source) is int and 0<=source<256 and prev_ids[source] in set(before)-set(deaths),'old surviving parent')
            require(parents[child]==prev_ids[source],'birth parent identity')
        d_ids=list(prev_ids);d_units=list(prev_units)
        for site in dead_sites:d_ids[site]=None;d_units[site]=None
        for i in set(before)&set(after):
            a,b=before[i],after[i]
            require(a==b and all(prev_units[a][k]==units[b][k] for k in ('material','program')),'stationary surviving genotype')
        d=matches(d_ids,d_units);f=matches(ids,units)
        steps.append(phase_step(tick,p,d,f,births,deaths));seen.update(births)
        prev_ids,prev_units,p=ids,units,f
    require(prev_ids==case['final']['site_ids'],'final identities')
    require([len(s['final']) for s in steps]==case['summary']['genetic_counts'],'019 exact final counts')
    intervals=spans(steps)
    require([[e['start'],e['end']] for e in intervals]==case['summary']['episodes'],'019 exact episodes')
    return dict(seed=case['seed'],mode=case['mode'],exchange=case['exchange'],steps=steps,episodes=intervals)


def summarize(records):
    keys=[(r['seed'],r['mode'],r['exchange']) for r in records]
    require(len(keys)==120 and set(keys)==set(GRID),'complete unique grid')
    for r in records:
        require(type(r['seed']) is int and type(r['exchange']) is bool and len(r['steps'])==32,'strict identity and length')
        require(r['episodes']==spans(r['steps']),'canonical intervals')
        for t,s in enumerate(r['steps'],1):
            require(s==phase_step(t,s['previous'],s['dissolved'],s['final'],s['births'],s['deaths']),'phase flags')
    output=[]
    for mode,exchange in product(MODES,(False,True)):
        rows=[r for r in records if r['mode']==mode and r['exchange'] is exchange];steps=[s for r in rows for s in r['steps']]
        output.append(dict(mode=mode,exchange=exchange,cases=len(rows),episodes=sum(len(r['episodes']) for r in rows),
                           double_steps=sum(len(s['final'])>=2 for s in steps),
                           **{k:sum(s['crossings'][i] for s in steps) for i,k in enumerate(CROSSINGS)},hidden=sum(s['hidden'] for s in steps)))
    return output


def main():
    from scripts.copy_episode_inputs import bindings,source_cases,read,digest,save
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();records=[]
    meta=dict(status='running',planned_cases=120,completed_cases=0,saved_steps=0,new_simulation_steps=0,new_environment_sources=0,
              reused_environment_sources=20,new_independent_initial_worlds=0,time_limit_seconds=300,storage_limit_bytes=33554432,
              git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    try:
        before=bindings();meta['input_sha256']=before;save(OUTPUT/'metadata.json',meta)
        for path in source_cases():
            records.append(analyze_case(read(path)))
            meta.update(completed_cases=len(records),saved_steps=32*len(records),elapsed_seconds=time.monotonic()-started)
            save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta)
            require(meta['elapsed_seconds']<=300 and sum(p.stat().st_size for p in OUTPUT.iterdir())<=33554432,'bounded run')
        save(OUTPUT/'summary.json',summarize(records))
        meta['input_sha256_after']=bindings();require(meta['input_sha256_after']==before,'unchanged sources')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256={n:digest(OUTPUT/n) for n in ('records.json','summary.json')})
        require(meta['elapsed_seconds']<=300 and sum(p.stat().st_size for p in OUTPUT.iterdir())<=33554432,'bounded complete run')
        save(OUTPUT/'metadata.json',meta);print(json.dumps({k:v for k,v in meta.items() if 'sha256' not in k}))
    except Exception as exc:
        meta.update(status='failed',error=repr(exc),elapsed_seconds=time.monotonic()-started);save(OUTPUT/'metadata.json',meta);raise

if __name__=='__main__':main()
