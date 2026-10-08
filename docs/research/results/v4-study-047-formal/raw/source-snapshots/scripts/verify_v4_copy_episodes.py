"""Independent identity-difference reconstruction and translated component matching."""
import json
import math
from pathlib import Path
from itertools import product
from time import monotonic
from scripts.verify_v4_structure_copies import translated_equal

MODES=('random-direction','random-feed','random-both')
GRID=tuple(product(range(120000,120020),MODES,(False,True)))
OUTPUT=Path('data/v4-study-020')
FLAGS=('dissolution_up','dissolution_down','formation_up','formation_down')


def require(value,message):
    if not value:raise ValueError(message)


def same(actual,expected,message):
    require(json.dumps(actual,sort_keys=True,separators=(',',':'))==json.dumps(expected,sort_keys=True,separators=(',',':')),message)


def snapshot(ids,units,width,height):
    require(len(ids)==len(units)==width*height,'snapshot dimensions')
    result={}
    for site,(identity,unit) in enumerate(zip(ids,units)):
        require((identity is None)==(unit is None),'occupied identity and unit')
        if identity is None:continue
        require(type(identity) is int and identity>=0 and identity not in result,'unique integer identity')
        require(type(unit['material']) is int and isinstance(unit['program'],list) and all(type(v) is int for v in unit['program']),'material and complete program')
        result[identity]=(site,unit)
    return result


def matches(state,owners,target,width,height):
    at={site:identity for identity,(site,_) in state.items()};remaining=set(at);groups=[]
    while remaining:
        origin=min(remaining);remaining.remove(origin);pending=[origin];sites=[]
        material=state[at[origin]][1]['material']
        while pending:
            site=pending.pop();sites.append(site);x,y=site%width,site//width
            for neighbor in (y*width+(x+1)%width,y*width+(x-1)%width,((y+1)%height)*width+x,((y-1)%height)*width+x):
                if neighbor in remaining and state[at[neighbor]][1]['material']==material:
                    remaining.remove(neighbor);pending.append(neighbor)
        identities=sorted(at[s] for s in sites)
        if not all(owners[i] in (0,1) for i in identities):continue
        points=tuple((s%width,s//width,state[at[s]][1]['material'],tuple(state[at[s]][1]['program'])) for s in sorted(sites))
        if translated_equal(target,points,width,height):groups.append(identities)
    return sorted(groups)


def episodes(steps):
    result=[];start=None
    for index in range(len(steps)+1):
        doubled=index<len(steps) and len(steps[index]['final'])>=2
        if doubled and start is None:start=index
        if not doubled and start is not None:
            result.append(dict(start=start+1,end=index,length=index-start,right_censored=index==len(steps),
                               start_step=steps[start],exit_step=steps[index] if index<len(steps) else None))
            start=None
    return result


def recount(case):
    width,height=case['config']['width'],case['config']['height']
    require(type(width) is int and type(height) is int and width>0 and height>0,'positive geometry')
    initial=case['initial'];previous=snapshot(initial['site_ids'],initial['units'],width,height)
    parents=case['final']['parents'];owners={}
    for identity,parent in enumerate(parents):
        if identity in previous:
            require(parent is None,'founder parent');owners[identity]=identity
        else:
            require(type(parent) is int and 0<=parent<identity,'ordered ancestry');owners[identity]=owners[parent]
    require({0,1}.issubset(previous),'target founders')
    target=tuple((previous[i][0]%width,previous[i][0]//width,previous[i][1]['material'],tuple(previous[i][1]['program'])) for i in (0,1))
    previous_groups=matches(previous,owners,target,width,height)
    require(previous_groups==[[0,1]],'single initial target')
    steps=[];seen=set(previous)
    for tick,row in enumerate(case['rows'],1):
        require(type(row['tick']) is int and row['tick']==tick,'consecutive saved steps')
        final=snapshot(row['site_ids'],row['physical']['units'],width,height)
        require(set(final)<=set(owners),'ancestry coverage')
        births=set(final)-set(previous);deaths=set(previous)-set(final)
        require(not births&seen,'identity never reused')
        seen.update(births)
        for identity in set(previous)&set(final):
            p,f=previous[identity],final[identity]
            require(p[0]==f[0] and p[1]['material']==f[1]['material'] and p[1]['program']==f[1]['program'],'survivor geometry material program unchanged')
        material=row['physical']['material'];dead_sites=material['dissolved']
        require(all(type(s) is int and 0<=s<width*height for s in dead_sites) and len(set(dead_sites))==len(dead_sites),'unique dissolution sites')
        prior_sites={site:identity for identity,(site,_) in previous.items()}
        require(all(s in prior_sites for s in dead_sites),'dissolved prior occupant')
        require({prior_sites[s] for s in dead_sites}==deaths,'death events match identity differences')
        formed=[p for p in material['proposals'] if p['reason']=='formed'];new_sites={site:identity for identity,(site,_) in final.items()}
        targets=[p['target'] for p in formed]
        require(all(type(s) is int and 0<=s<width*height for s in targets) and len(targets)==len(set(targets)),'unique formation sites')
        require(all(s in new_sites for s in targets) and {new_sites[s] for s in targets}==births,'birth events match identity differences')
        for proposal in formed:
            source=proposal['source'];identity=new_sites[proposal['target']]
            require(type(source) is int and source in prior_sites and prior_sites[source] not in deaths and parents[identity]==prior_sites[source],'surviving formation source ancestry')
        # This reconstruction deliberately starts at F and removes births.
        dissolved={i:value for i,value in final.items() if i not in births}
        dg=matches(dissolved,owners,target,width,height);fg=matches(final,owners,target,width,height)
        p,d,f=(len(g)>=2 for g in (previous_groups,dg,fg))
        steps.append(dict(tick=tick,previous=previous_groups,dissolved=dg,final=fg,births=sorted(births),deaths=sorted(deaths),
                          crossings=[not p and d,p and not d,not d and f,d and not f],hidden=p==f and p!=d))
        previous,previous_groups=final,fg
    same(snapshot(case['final']['site_ids'],case['final']['units'],width,height),previous,'last saved snapshot')
    runs=episodes(steps)
    same([len(s['final']) for s in steps],case['summary']['genetic_counts'],'019 complete copy-count sequence')
    same([[r['start'],r['end']] for r in runs],case['summary']['episodes'],'019 all intervals')
    return dict(seed=case['seed'],mode=case['mode'],exchange=case['exchange'],steps=steps,episodes=runs)


def aggregate(records):
    require(len(records)==120,'all 120 cases')
    index={}
    for record in records:
        key=(record['seed'],record['mode'],record['exchange'])
        require(type(record['seed']) is int and type(record['exchange']) is bool and key in GRID and key not in index,'unique strict grid')
        index[key]=record
        same(record['episodes'],episodes(record['steps']),'record episodes and exact boundary steps')
        previous=None
        for tick,s in enumerate(record['steps'],1):
            require(type(s['tick']) is int and s['tick']==tick,'ledger ticks')
            for name in ('previous','dissolved','final'):
                groups=s[name];require(groups==sorted(groups) and all(g==sorted(set(g)) and len(g)==2 and all(type(i) is int and i>=0 for i in g) for g in groups),'matching groups')
                flat=[i for g in groups for i in g];require(len(flat)==len(set(flat)),'disjoint matching groups')
            if previous is not None:same(s['previous'],previous,'continuous stage sequence')
            previous=s['final']
            p,d,f=(len(s[k])>=2 for k in ('previous','dissolved','final'))
            same(s['crossings'],[not p and d,p and not d,not d and f,d and not f],'four threshold flags')
            same(s['hidden'],p==f and p!=d,'hidden phase flag')
    cells=[]
    for mode,exchange in product(MODES,(False,True)):
        selected=[index[seed,mode,exchange] for seed in range(120000,120020)];steps=[s for r in selected for s in r['steps']]
        cell=dict(mode=mode,exchange=exchange,cases=len(selected),episodes=sum(len(r['episodes']) for r in selected),double_steps=sum(len(s['final'])>=2 for s in steps))
        cell.update({name:sum(s['crossings'][i] for s in steps) for i,name in enumerate(FLAGS)})
        cell['hidden']=sum(s['hidden'] for s in steps);cells.append(cell)
    return cells


def main():
    from scripts.copy_episode_inputs import bindings,read,digest
    from scripts.copy_episode_inputs import source_cases
    started=monotonic();root=OUTPUT;names=('metadata.json','records.json','summary.json')
    before={n:digest(root/n) for n in names};meta=read(root/'metadata.json');bound=bindings()
    expected=dict(status='complete',planned_cases=120,completed_cases=120,saved_steps=3840,
                  new_simulation_steps=0,new_environment_sources=0,reused_environment_sources=20,
                  new_independent_initial_worlds=0,time_limit_seconds=300,storage_limit_bytes=33554432)
    for key,value in expected.items():same(meta[key],value,'metadata '+key)
    require(type(meta['git_commit']) is str and len(meta['git_commit'])==40 and all(c in '0123456789abcdef' for c in meta['git_commit']),'recorded commit')
    require(type(meta['elapsed_seconds']) in (int,float) and math.isfinite(meta['elapsed_seconds']) and 0<=meta['elapsed_seconds']<300,'analysis time budget')
    same(meta['input_sha256'],bound,'before bindings');same(meta['input_sha256_after'],bound,'after bindings')
    verifier_key='scripts/verify_v4_copy_episodes.py'
    same(bound[verifier_key],digest(Path(__file__)),'verifier identity binding')
    same(meta['output_sha256'],{n:before[n] for n in names[1:]},'exact output hashes')
    saved=read(root/'records.json');require(len(saved)==120,'all saved records')
    paths=list(source_cases());require(len(paths)==120,'all source cases');records=[]
    for index,(key,path) in enumerate(zip(GRID,paths)):
        require(monotonic()-started<300,'verification time budget')
        require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<33554432,'storage budget')
        case=read(path);same([case['seed'],case['mode'],case['exchange']],list(key),'source identity order')
        require(len(case['rows'])==32,'32 complete source rows')
        record=recount(case);same(saved[index],record,'all independently reconstructed stage and episode fields')
        records.append(record)
    summary=aggregate(records);same(summary,read(root/'summary.json'),'all six cells')
    same(bindings(),bound,'inputs unchanged during independent verification')
    same({n:digest(root/n) for n in names},before,'outputs unchanged during independent verification')
    proof=dict(status='verified',cases=120,saved_steps=3840,episodes=sum(len(r['episodes']) for r in records),
               new_simulation_steps=0,new_environment_sources=0,reused_environment_sources=20,new_independent_initial_worlds=0,
               input_files=len(bound),files_sha256=before,verifier_sha256=digest(Path(__file__)),
               elapsed_seconds=monotonic()-started,
               scope='independent F-minus-birth identity reconstruction, same-material torus traversal, direct translated complete-program matching, all stage groups, crossings, intervals and six cells')
    require(proof['elapsed_seconds']<300,'verification time budget')
    payload=json.dumps(proof,indent=2)+'\n'
    require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file())+len(payload.encode())<33554432,'proof storage budget')
    with (root/'independent-verification.json').open('x') as stream:stream.write(payload)
    print('verified all 120 cases and 3840 saved phase ledgers')


if __name__=='__main__':
    try:main()
    except BaseException as error:
        path=OUTPUT/'verification-failure.json'
        if path.parent.is_dir() and not path.exists():
            with path.open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise
