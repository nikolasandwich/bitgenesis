"""Independent torus traversal, ancestor-chain and component identity audit."""
import json
import math
from itertools import combinations, product
from pathlib import Path
from time import monotonic
from scripts.verify_v4_structure_copies import translated_equal

MODES=('random-direction','random-feed','random-both')
GRID=tuple(product(range(120000,120020),MODES,(False,True)))
CONTROLS=('constructed-off','constructed-on','no-raw-off')
LABELS=tuple(f'seed-{seed}-{mode}-exchange-{str(exchange).lower()}' for seed,mode,exchange in GRID)+tuple('control-'+name for name in CONTROLS)
OUTPUT=Path('data/v4-study-021')


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


def matching_groups(state,roots,target,width,height):
    sites={site:identity for identity,(site,_) in state.items()};unseen=set(sites);groups=[]
    while unseen:
        first=min(unseen);unseen.remove(first);queue=[first];component=[]
        material=state[sites[first]][1]['material']
        while queue:
            site=queue.pop();component.append(site);x,y=site%width,site//width
            for neighbor in (y*width+(x-1)%width,y*width+(x+1)%width,((y-1)%height)*width+x,((y+1)%height)*width+x):
                if neighbor in unseen and state[sites[neighbor]][1]['material']==material:
                    unseen.remove(neighbor);queue.append(neighbor)
        members=sorted(sites[s] for s in component)
        if any(roots[i] not in (0,1) for i in members):continue
        points=tuple((s%width,s//width,state[sites[s]][1]['material'],tuple(state[sites[s]][1]['program'])) for s in component)
        if translated_equal(target,points,width,height):groups.append(members)
    return sorted(groups)


def intervals(flags):
    runs=[];begin=None
    for position in range(len(flags)+1):
        active=position<len(flags) and flags[position]
        if active and begin is None:begin=position
        if not active and begin is not None:
            runs.append([begin+1,position]);begin=None
    return runs


def identity_episodes(steps):
    result=[]
    for begin,end in intervals([len(s['copies'])>=2 for s in steps]):
        common=None;streak={};longest=0
        for step in steps[begin-1:end]:
            present={tuple(group['members']) for group in step['copies']}
            common=present if common is None else common&present
            pairs=set(combinations(sorted(present),2))
            streak={pair:streak.get(pair,0)+1 for pair in pairs}
            longest=max(longest,max(streak.values(),default=0))
        result.append(dict(start=begin,end=end,length=end-begin+1,right_censored=end==len(steps),
            stable_groups=[list(g) for g in sorted(common)],stable_pair=len(common)>=2,max_same_pair_run=longest))
    return result


def recount(case,label):
    width,height=case['config']['width'],case['config']['height']
    require(type(width) is int and type(height) is int and width>0 and height>0,'positive geometry')
    initial=snapshot(case['initial']['site_ids'],case['initial']['units'],width,height)
    require({0,1}<=set(initial),'target founders')
    parents=case['final']['parents'];require(type(parents) is list,'parent list')
    require(set(initial)<=set(range(len(parents))),'initial ancestry coverage')
    roots={};depths={}
    # Walk every chain explicitly, independently of production's ancestry pass.
    for identity in range(len(parents)):
        cursor=identity;depth=0
        while cursor not in initial:
            parent=parents[cursor]
            require(type(parent) is int and 0<=parent<cursor,'ordered ancestry')
            cursor=parent;depth+=1
        require(parents[cursor] is None,'founder parent')
        roots[identity]=cursor;depths[identity]=depth
    target=tuple((initial[i][0]%width,initial[i][0]//width,initial[i][1]['material'],tuple(initial[i][1]['program'])) for i in (0,1))
    same(matching_groups(initial,roots,target,width,height),[[0,1]],'single initial target')
    steps=[]
    for tick,row in enumerate(case['rows'],1):
        require(type(row['tick']) is int and row['tick']==tick,'consecutive saved steps')
        state=snapshot(row['site_ids'],row['physical']['units'],width,height)
        require(set(state)<=set(roots),'ancestry coverage')
        groups=matching_groups(state,roots,target,width,height);copies=[]
        for members in groups:
            original=[i for i in members if i in (0,1)]
            copies.append(dict(members=members,original_members=original,depths=[depths[i] for i in members],
                founder_roots=sorted({roots[i] for i in members}),all_new=not original))
        new_count=sum(c['all_new'] for c in copies)
        steps.append(dict(tick=tick,copies=copies,new_only_count=new_count,founder_containing_count=len(copies)-new_count))
    require(bool(steps),'saved steps exist')
    same(snapshot(case['final']['site_ids'],case['final']['units'],width,height),state,'last saved snapshot')
    episodes=identity_episodes(steps)
    same([len(s['copies']) for s in steps],case['summary']['genetic_counts'],'old complete genetic counts')
    same([[e['start'],e['end']] for e in episodes],case['summary']['episodes'],'old complete intervals')
    new_episodes=intervals([s['new_only_count']>=2 for s in steps])
    longest=max((end-start+1 for start,end in new_episodes),default=0)
    return dict(label=label,steps=steps,episodes=episodes,new_episodes=new_episodes,new_longest=longest,new_persistent10=longest>=10)


def aggregate(records):
    same([r['label'] for r in records],list(LABELS),'complete ordered record labels')
    def row(label,selected):
        steps=[s for r in selected for s in r['steps']];episodes=[e for r in selected for e in r['episodes']]
        return dict(label=label,cases=len(selected),episodes=len(episodes),double_steps=sum(len(s['copies'])>=2 for s in steps),
            all_new_double_steps=sum(s['new_only_count']>=2 for s in steps),ever_two_new=sum(bool(r['new_episodes']) for r in selected),
            persistent_two_new=sum(r['new_persistent10'] for r in selected),stable_pair_episodes=sum(e['stable_pair'] for e in episodes),
            max_same_pair_run=max((e['max_same_pair_run'] for e in episodes),default=0))
    cells=[]
    for mode,exchange in product(MODES,(False,True)):
        suffix=f'{mode}-exchange-{str(exchange).lower()}'
        cells.append(row(suffix,[records[index] for index,key in enumerate(GRID) if key[1:]==(mode,exchange)]))
    return dict(cells=cells,controls=[row('control-'+name,[records[120+i]]) for i,name in enumerate(CONTROLS)])


def main():
    from scripts.copy_member_inputs import bindings,read,digest,source_cases
    root=OUTPUT;proof_path=root/'independent-verification.json'
    if proof_path.exists():raise FileExistsError(proof_path)
    started=monotonic()
    try:
        names=('metadata.json','records.json','summary.json');before={n:digest(root/n) for n in names}
        meta=read(root/'metadata.json');bound=bindings();require(len(bound)==203,'203 source bindings')
        expected=dict(status='complete',planned_cases=123,completed_cases=123,saved_steps=3936,new_simulation_steps=0,
            new_environment_sources=0,reused_environment_sources=20,reused_deterministic_controls=3,new_independent_initial_worlds=0,
            time_limit_seconds=300,storage_limit_bytes=33554432)
        for key,value in expected.items():same(meta[key],value,'metadata '+key)
        require(type(meta['git_commit']) is str and len(meta['git_commit'])==40 and all(c in '0123456789abcdef' for c in meta['git_commit']),'recorded commit')
        require(type(meta['elapsed_seconds']) in (int,float) and math.isfinite(meta['elapsed_seconds']) and 0<=meta['elapsed_seconds']<300,'analysis time budget')
        same(meta['input_sha256'],bound,'before bindings');same(meta['input_sha256_after'],bound,'after bindings')
        same(bound['scripts/verify_v4_copy_members.py'],digest(Path(__file__)),'verifier identity binding')
        same(meta['output_sha256'],{n:before[n] for n in names[1:]},'exact output hashes')
        saved=read(root/'records.json');require(type(saved) is list and len(saved)==123,'123 saved records')
        sources=list(source_cases());same([label for label,_ in sources],list(LABELS),'complete source label order')
        records=[]
        for index,(label,case) in enumerate(sources):
            require(monotonic()-started<300,'verification time budget')
            require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<33554432,'storage budget')
            if index<120:same([case['seed'],case['mode'],case['exchange']],list(GRID[index]),'source identity order')
            else:
                name=CONTROLS[index-120];same(case['name'],name,'control identity order')
                same(case['exchange'],name=='constructed-on','control exchange')
                same(case['raw_tokens'],0 if name=='no-raw-off' else 4,'control raw tokens')
            require(len(case['rows'])==32,'32 complete source rows')
            record=recount(case,label);same(saved[index],record,'all independently reconstructed member fields');records.append(record)
        same(aggregate(records),read(root/'summary.json'),'all six cells and three controls')
        same(bindings(),bound,'inputs unchanged during verification')
        same({n:digest(root/n) for n in names},before,'outputs unchanged during verification')
        proof=dict(status='verified',cases=123,saved_steps=3936,episodes=sum(len(r['episodes']) for r in records),new_simulation_steps=0,
            new_environment_sources=0,reused_environment_sources=20,reused_deterministic_controls=3,new_independent_initial_worlds=0,
            input_files=len(bound),files_sha256=before,verifier_sha256=digest(Path(__file__)),elapsed_seconds=monotonic()-started,
            scope='independent torus components and translated full-program matching, ancestor chains, all member attributes, interval identity intersection and every unordered pair streak, all six cells and three controls')
        require(proof['elapsed_seconds']<300,'verification time budget');payload=json.dumps(proof,indent=2)+'\n'
        require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file())+len(payload.encode())<33554432,'proof storage budget')
        with proof_path.open('x') as stream:stream.write(payload)
        print('verified all 123 cases and 3936 saved member ledgers')
    except BaseException as error:
        failure=root/'verification-failure.json'
        if root.is_dir() and not failure.exists():
            with failure.open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise


if __name__=='__main__':main()
