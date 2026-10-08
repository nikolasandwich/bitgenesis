"""Original-member dependence and identical-pair persistence in saved copies."""
from itertools import combinations,product
from pathlib import Path
import subprocess,time,json
from bitgenesis.v4.structure import snapshot
from scripts.analyze_v4_structure_copies import canonical,episodes

MODES=('random-direction','random-feed','random-both')
CONTROLS=('constructed-off','constructed-on','no-raw-off')
LABELS=tuple(f'seed-{s}-{m}-exchange-{str(e).lower()}' for s,m,e in product(range(120000,120020),MODES,(False,True)))+tuple('control-'+n for n in CONTROLS)
OUTPUT=Path('data/v4-study-021')


def require(value,message):
    if not value:raise ValueError(message)


def describe(group,parents):
    require(group==sorted(set(group)) and len(group)==2,'complete matching pair members')
    depths=[];roots=[]
    for member in group:
        require(type(member) is int and 0<=member<len(parents),'valid member')
        node=member;depth=0
        while parents[node] is not None:
            parent=parents[node];require(type(parent) is int and 0<=parent<node,'ordered ancestry')
            node=parent;depth+=1
        require(node in (0,1),'pure target ancestry');depths.append(depth);roots.append(node)
    original=[i for i in group if i in (0,1)]
    return dict(members=group,original_members=original,depths=depths,founder_roots=sorted(set(roots)),all_new=not original)


def episode_records(groups_by_step):
    output=[]
    for a,b in episodes([len(g) for g in groups_by_step]):
        sets=[set(tuple(g) for g in groups) for groups in groups_by_step[a-1:b]]
        shared=set.intersection(*sets);active={};longest=0
        for current in sets:
            active={pair:active.get(pair,0)+1 for pair in combinations(sorted(current),2)}
            longest=max(longest,max(active.values(),default=0))
        output.append(dict(start=a,end=b,length=b-a+1,right_censored=b==len(groups_by_step),stable_groups=[list(g) for g in sorted(shared)],stable_pair=len(shared)>=2,max_same_pair_run=longest))
    return output


def analyze_case(case,label):
    require(label in LABELS,'registered label')
    if label.startswith('control-'):require(label=='control-'+case['name'],'control identity')
    else:
        require(type(case['seed']) is int and type(case['exchange']) is bool,'strict case identity')
        require(label==f"seed-{case['seed']}-{case['mode']}-exchange-{str(case['exchange']).lower()}",'environment identity')
    initial=case['initial'];parents=case['final']['parents'];roots=[]
    for i,parent in enumerate(parents):
        require(parent is None or type(parent) is int and 0<=parent<i,'acyclic ordered lineage')
        require((parent is None)==(i in (0,1,2)),'three original founders')
        roots.append(i if parent is None else roots[parent])
    def index(ids,units):
        require(len(ids)==len(units)==256,'fixed world size');found={}
        for site,i in enumerate(ids):
            require((i is None)==(units[site] is None),'occupied identity agreement')
            if i is not None:
                require(type(i) is int and 0<=i<len(parents) and i not in found,'unique live member')
                found[i]=site
        return found
    def points(group,sites,units):
        return tuple((sites[i]%16,sites[i]//16,units[sites[i]]['material'],tuple(units[sites[i]]['program'])) for i in group)
    sites=index(initial['site_ids'],initial['units']);require(set(sites)=={0,1,2},'fixed initial population')
    target=canonical(points([0,1],sites,initial['units']));steps=[]
    for tick,row in enumerate(case['rows'],1):
        require(type(row['tick']) is int and row['tick']==tick,'ordered saved steps')
        ids=row['site_ids'];units=row['physical']['units'];sites=index(ids,units)
        groups=snapshot(units,ids,16,16,phase='final')['components']['material'];copies=[]
        for group in sorted(sorted(g) for g in groups):
            if len(group)==2 and all(roots[i] in (0,1) for i in group) and canonical(points(group,sites,units))==target:
                copies.append(describe(group,parents))
        new=sum(g['all_new'] for g in copies)
        steps.append(dict(tick=tick,copies=copies,new_only_count=new,founder_containing_count=len(copies)-new))
    require(steps and case['rows'][-1]['site_ids']==case['final']['site_ids'],'final identities')
    counts=[len(s['copies']) for s in steps];require(counts==case['summary']['genetic_counts'],'old exact matching sequence')
    spans=episode_records([[c['members'] for c in s['copies']] for s in steps])
    require([[e['start'],e['end']] for e in spans]==case['summary']['episodes'],'old exact episodes')
    new_spans=episodes([s['new_only_count'] for s in steps]);longest=max((b-a+1 for a,b in new_spans),default=0)
    return dict(label=label,steps=steps,episodes=spans,new_episodes=new_spans,new_longest=longest,new_persistent10=longest>=10)


def summarize(records):
    require(len(records)==123 and {r['label'] for r in records}==set(LABELS),'complete unique123 grid')
    index={r['label']:r for r in records}
    for r in records:
        require(len(r['steps'])==32,'fixed32 samples')
        groups=[]
        for tick,s in enumerate(r['steps'],1):
            require(type(s['tick']) is int and s['tick']==tick,'ordered ticks')
            require(type(s['new_only_count']) is int and s['new_only_count']==sum(g['all_new'] for g in s['copies']),'new counts')
            require(s['founder_containing_count']==len(s['copies'])-s['new_only_count'],'founder counts')
            groups.append([g['members'] for g in s['copies']])
        require(r['episodes']==episode_records(groups),'identity intervals')
        new_spans=episodes([s['new_only_count'] for s in r['steps']]);longest=max((b-a+1 for a,b in new_spans),default=0)
        require(r['new_episodes']==new_spans and type(r['new_longest']) is int and r['new_longest']==longest and type(r['new_persistent10']) is bool and r['new_persistent10']==(longest>=10),'new interval integrity')
    def cell(label,rows):
        return dict(label=label,cases=len(rows),episodes=sum(len(r['episodes']) for r in rows),double_steps=sum(len(s['copies'])>=2 for r in rows for s in r['steps']),
                    all_new_double_steps=sum(s['new_only_count']>=2 for r in rows for s in r['steps']),ever_two_new=sum(r['new_longest']>0 for r in rows),
                    persistent_two_new=sum(r['new_persistent10'] for r in rows),stable_pair_episodes=sum(e['stable_pair'] for r in rows for e in r['episodes']),
                    max_same_pair_run=max((e['max_same_pair_run'] for r in rows for e in r['episodes']),default=0))
    cells=[cell(f'{m}-exchange-{str(e).lower()}',[index[f'seed-{s}-{m}-exchange-{str(e).lower()}'] for s in range(120000,120020)]) for m,e in product(MODES,(False,True))]
    controls=[cell('control-'+n,[index['control-'+n]]) for n in CONTROLS]
    return dict(cells=cells,controls=controls)


def main():
    from scripts.copy_member_inputs import bindings,source_cases,digest,save
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();records=[]
    meta=dict(status='running',planned_cases=123,completed_cases=0,saved_steps=0,new_simulation_steps=0,new_environment_sources=0,reused_environment_sources=20,reused_deterministic_controls=3,new_independent_initial_worlds=0,time_limit_seconds=300,storage_limit_bytes=33554432,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    try:
        before=bindings();meta['input_sha256']=before;save(OUTPUT/'metadata.json',meta)
        for label,case in source_cases():
            require(len(case['rows'])==32,'full source length');records.append(analyze_case(case,label))
            meta.update(completed_cases=len(records),saved_steps=32*len(records),elapsed_seconds=time.monotonic()-started)
            save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta)
            require(meta['elapsed_seconds']<=300 and sum(p.stat().st_size for p in OUTPUT.iterdir())<=33554432,'bounded run')
        save(OUTPUT/'summary.json',summarize(records));meta['input_sha256_after']=bindings();require(meta['input_sha256_after']==before,'unchanged inputs')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256={n:digest(OUTPUT/n) for n in ('records.json','summary.json')})
        require(meta['elapsed_seconds']<=300 and sum(p.stat().st_size for p in OUTPUT.iterdir())<=33554432,'bounded complete run')
        save(OUTPUT/'metadata.json',meta);print(json.dumps({k:v for k,v in meta.items() if 'sha256' not in k}))
    except Exception as exc:
        meta.update(status='failed',error=repr(exc),elapsed_seconds=time.monotonic()-started);save(OUTPUT/'metadata.json',meta);raise

if __name__=='__main__':main()
