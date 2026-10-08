"""Descriptive fates from saved study016 records; never advances a simulation."""
import json
import subprocess
import time
from fractions import Fraction
from itertools import product
from pathlib import Path

TICKS=(100,200,300,400)
CATEGORIES=('extinct','continuous_retained','continuous_replaced','broken_retained','broken_replaced')
BINS=('001-100','101-200','201-300','301-400','never')
ORDERS=('neither','break_only','replacement_only','break_first','same_tick','replacement_first')
BREAK_STATES=('extinct','fragmented','mixed','closed_singleton','never')
TIMING_KEYS=tuple(f'{prefix}:{key}' for prefix,keys in (('break_bin',BINS),('replacement_bin',BINS),('order',ORDERS),('break_state',BREAK_STATES)) for key in keys)
IDENTITY=('history','seed','mutation','exchange')
GRID=tuple(product((True,False),range(112000,112005),(0,100),(True,False)))
OUTPUT=Path('data/v4-study-016-fates')
SECONDS=1200
STORAGE=100*1024**2


def require(condition,message):
    if not condition:raise ValueError(message)


def fate(descendants,original_survivors,continuous):
    require(type(descendants) is int and type(original_survivors) is int and 0<=original_survivors<=descendants and type(continuous) is bool,'invalid component counts or continuity')
    require(not continuous or descendants>=2,'continuous component must be multi')
    if descendants==0:return 'extinct'
    return ('continuous_' if continuous else 'broken_')+('retained' if original_survivors else 'replaced')


def event_bin(tick):
    require(tick is None or type(tick) is int and 1<=tick<=400,'invalid relative event tick')
    return 'never' if tick is None else BINS[(tick-1)//100]


def event_order(break_tick,replacement_tick):
    event_bin(break_tick);event_bin(replacement_tick)
    if break_tick is None:return 'neither' if replacement_tick is None else 'replacement_only'
    if replacement_tick is None:return 'break_only'
    return 'break_first' if break_tick<replacement_tick else 'same_tick' if break_tick==replacement_tick else 'replacement_first'


def first_break_state(groups,parents,initial_founders,anchor_members):
    """Resolve final parent chains, but count only the observed living identities."""
    roots=[]
    for identity,parent in enumerate(parents):
        require(parent is None or type(parent) is int and 0<=parent<identity,'invalid parent chain')
        roots.append(identity if identity in initial_founders else None if parent is None else roots[parent])
    living=set();targets=[];n=0
    for group in groups:
        require(bool(group),'empty material group')
        owned=0
        for identity in group:
            require(type(identity) is int and 0<=identity<len(roots) and identity not in living,'invalid living identity')
            living.add(identity);require(roots[identity] is not None,'living identity without initial founder')
            owned+=roots[identity] in anchor_members
        if owned:targets.append((len(group),owned));n+=owned
    return 'extinct' if not n else 'fragmented' if len(targets)>1 else 'mixed' if targets[0][0]>n else 'closed_singleton' if n==1 else 'closed_multi'


def identity(row):
    require(type(row['history']) is bool and type(row['exchange']) is bool and type(row['seed']) is int and type(row['mutation']) is int,'strict branch identity types')
    return tuple(row[k] for k in IDENTITY)


def index_grid(rows):
    keys=[identity(r) for r in rows]
    require(len(keys)==40 and set(keys)==set(GRID),'complete unique forty branch grid')
    return dict(zip(keys,rows))


def classify_branch(row):
    from scripts.horizon_fate_inputs import read
    identity(row);require(row['status']=='complete','source branch failed')
    directory=Path('data/v4-study-016')/row['directory']
    initial=read(directory/'initial.json');parents=read(directory/'final.json')['parents']
    groups=initial['observation']['components']['material'];founders={i for g in groups for i in g}
    saved=row['records'];require(set(saved)=={str(t) for t in TICKS},'checkpoint grid')
    indexes={}
    for tick in TICKS:
        items=saved[str(tick)];indexes[tick]={r['component']:r for r in items}
        require(len(indexes[tick])==len(items)==len(groups),'complete saved component grid')
        require(set(indexes[tick])==set(range(len(groups))),'saved component identities')
    needed=set();components=[]
    for i,origin in enumerate(groups):
        if len(origin)<2 or len(origin)==len(founders):continue
        last=indexes[400][i];b=last['first_break_tick'];r=last['first_complete_replacement_tick'];event_bin(b);event_bin(r)
        checkpoints={}
        for t in TICKS:
            old=indexes[t][i];ep=old['endpoint'];continuous=old['continuous_closed_multi']
            require(old['anchor_members']==origin and old['anchor_size']==len(origin) and old['whole_world_anchor'] is False,'same initial eligible cohort')
            require(old['first_break_tick']==(b if b is not None and b<=t else None),'break prefix consistency')
            require(old['first_complete_replacement_tick']==(r if r is not None and r<=t else None),'replacement prefix consistency')
            require(continuous is (b is None or b>t),'continuous event consistency')
            checkpoints[str(t)]=dict(category=fate(ep['descendants'],ep['original_survivors'],continuous),original_survivors=ep['original_survivors'],descendants=ep['descendants'],continuous=continuous)
        if b is not None:needed.add(b)
        components.append(dict(component=i,anchor_members=origin,checkpoints=checkpoints,first_break_tick=b,first_complete_replacement_tick=r,first_break_state='never',order=event_order(b,r)))
    observations={};count=0
    with (directory/'steps.jsonl').open() as stream:
        for count,line in enumerate(stream,1):
            step=json.loads(line);require(type(step['tick']) is int and step['tick']==count,'complete ordered steps')
            if count in needed:observations[count]=step['observation']['components']['material']
    require(count==400,'complete four hundred steps')
    for c in components:
        if c['first_break_tick'] is not None:
            c['first_break_state']=first_break_state(observations[c['first_break_tick']],parents,founders,c['anchor_members'])
            require(c['first_break_state'] in BREAK_STATES[:-1],'first break cannot be closed multi')
    return dict(zip(IDENTITY,identity(row)),components=components)


def distribution(counts,n):
    return dict(counts=counts,fractions={k:str(Fraction(v,n)) if n else None for k,v in counts.items()})


def branch_result(row):
    key=identity(row);components=row['components'];n=len(components)
    ids=[c['component'] for c in components]
    require(all(type(i) is int and i>=0 for i in ids) and ids==sorted(set(ids)),'unique ordered components')
    counts={str(t):dict.fromkeys(CATEGORIES,0) for t in TICKS};timing=dict.fromkeys(TIMING_KEYS,0)
    for c in components:
        members=c['anchor_members'];require(len(members)>=2 and len(set(members))==len(members) and all(type(i) is int and i>=0 for i in members),'eligible original members')
        b,r=c['first_break_tick'],c['first_complete_replacement_tick'];order=event_order(b,r)
        require(c['order']==order and c['first_break_state'] in BREAK_STATES and (c['first_break_state']=='never')==(b is None),'event descriptors')
        require(set(c['checkpoints'])=={str(t) for t in TICKS},'component checkpoints')
        previous=None
        for t in TICKS:
            cp=c['checkpoints'][str(t)];cat=fate(cp['descendants'],cp['original_survivors'],cp['continuous'])
            require(cp['category']==cat and cp['continuous'] is (b is None or b>t),'checkpoint fate consistency')
            require(cp['original_survivors']<=len(members),'original count bounded')
            require(not previous or cp['original_survivors']<=previous['original_survivors'],'original survivors cannot increase')
            require(not previous or previous['descendants'] or cp['descendants']==0,'extinction is absorbing')
            require(cp['original_survivors']!=0 or cp['descendants']==0 or r is not None and r<=t,'living replacement requires event')
            require(r is None or r>t or cp['original_survivors']==0,'replacement cannot regain original')
            counts[str(t)][cat]+=1;previous=cp
        for k in (f'break_bin:{event_bin(b)}',f'replacement_bin:{event_bin(r)}',f'order:{order}',f"break_state:{c['first_break_state']}"):timing[k]+=1
    return dict(zip(IDENTITY,key),status='complete',eligible=n,checkpoints={str(t):distribution(counts[str(t)],n) for t in TICKS},timing=distribution(timing,n))


def summarize_records(rows):
    index=index_grid(rows);results=[branch_result(index[key]) for key in GRID]
    for h,s,m in product((True,False),range(112000,112005),(0,100)):
        a,b=index[h,s,m,True],index[h,s,m,False]
        require([(c['component'],c['anchor_members']) for c in a['components']]==[(c['component'],c['anchor_members']) for c in b['components']],'paired original cohorts')
    return results,aggregate_results(results)


def average(values):
    present=[Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(present)/len(present)) if present else None,available=len(present),missing=len(values)-len(present))


def aggregate_results(rows):
    index=index_grid(rows)
    for row in rows:
        n=row['eligible'];require(row['status']=='complete' and type(n) is int and n>=0,'complete branch with integer denominator')
        require(set(row['checkpoints'])=={str(t) for t in TICKS},'result checkpoints')
        for d,keys in [(row['checkpoints'][str(t)],CATEGORIES) for t in TICKS]+[(row['timing'],TIMING_KEYS)]:
            require(set(d['counts'])==set(d['fractions'])==set(keys),'all distribution categories')
            for k in keys:
                v=d['counts'][k];require(type(v) is int and 0<=v<=n,'integer counts bounded by denominator')
                require(d['fractions'][k]==(str(Fraction(v,n)) if n else None),'exact canonical fraction or zero denominator null')
            if keys==CATEGORIES:require(sum(d['counts'].values())==n,'fate conservation')
            else:
                for prefix in ('break_bin:','replacement_bin:','order:','break_state:'):require(sum(v for k,v in d['counts'].items() if k.startswith(prefix))==n,'event conservation')
    def scalar(key,t,k):return (index[key]['timing'] if t is None else index[key]['checkpoints'][str(t)])['fractions'][k]
    output={}
    for name,ticks,metrics in (('checkpoint',TICKS,CATEGORIES),('timing',(None,),TIMING_KEYS)):
        cells=[];pairs=[];groups=[]
        for h,m,e,t in product((True,False),(0,100),(True,False),ticks):
            cells.append(dict(history=h,mutation=m,exchange=e,**({} if t is None else dict(tick=t)),metrics={k:average([scalar((h,s,m,e),t,k) for s in range(112000,112005)]) for k in metrics}))
        for h,s,m in product((True,False),range(112000,112005),(0,100)):
            require(index[h,s,m,True]['eligible']==index[h,s,m,False]['eligible'],'paired denominator')
            values={}
            for t in ticks:
                values[str(t)]={}
                for k in metrics:
                    a,b=scalar((h,s,m,True),t,k),scalar((h,s,m,False),t,k)
                    require((a is None)==(b is None),'paired missing values')
                    values[str(t)][k]=dict(on=a,off=b,difference=None if a is None else str(Fraction(a)-Fraction(b)))
            pairs.append(dict(history=h,seed=s,mutation=m,**(dict(metrics=values['None']) if name=='timing' else dict(checkpoints=values))))
        for h,m,t in product((True,False),(0,100),ticks):
            selected=[p for p in pairs if p['history'] is h and p['mutation']==m]
            groups.append(dict(history=h,mutation=m,**({} if t is None else dict(tick=t)),metrics={k:average([(p['metrics'] if t is None else p['checkpoints'][str(t)])[k]['difference'] for p in selected]) for k in metrics}))
        output.update({name+'_cells':cells,name+'_pairs':pairs,name+'_groups':groups})
    return output


def save(path,value):
    path.write_text(json.dumps(value,separators=(',',':'))+'\n')


def main():
    from scripts.horizon_fate_inputs import bindings,source_rows,digest
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch required')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();records=[];results=[]
    meta=dict(status='running',planned_branches=40,completed_branches=0,new_simulation_steps=0,new_independent_sources=0,reused_independent_sources=5,time_limit_seconds=SECONDS,storage_limit_bytes=STORAGE)
    save(OUTPUT/'metadata.json',meta);save(OUTPUT/'records.json',records);save(OUTPUT/'results.json',results)
    def check_budget():
        require(time.monotonic()-started<SECONDS,'time budget exceeded')
        require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<STORAGE,'storage budget exceeded')
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        meta['input_sha256']=bindings();save(OUTPUT/'metadata.json',meta)
        rows=source_rows();index=index_grid(rows)
        for key in GRID:
            check_budget();require(bindings()==meta['input_sha256'],'bound inputs changed during run')
            branch=classify_branch(index[key]);result=branch_result(branch)
            records.append(branch);results.append(result);meta['completed_branches']=len(records)
            save(OUTPUT/'records.json',records);save(OUTPUT/'results.json',results);save(OUTPUT/'metadata.json',meta)
            print(f'{len(records)}/40 saved fate branches',flush=True)
        results,summary=summarize_records(records)
        require(sum(r['eligible'] for r in results if r['exchange'])==824,'frozen paired eligible count')
        save(OUTPUT/'results.json',results);save(OUTPUT/'summary.json',summary)
        meta['input_sha256_after']=bindings();require(meta['input_sha256']==meta['input_sha256_after'],'bound inputs changed')
        check_budget();meta.update(status='complete',output_sha256={n:digest(OUTPUT/n) for n in ('records.json','results.json','summary.json')})
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        try:
            meta['input_sha256_after']=bindings()
            if meta.get('input_sha256')!=meta['input_sha256_after'] and meta['status']=='complete':
                meta.update(status='failed',error='bound inputs changed at finalization')
        except BaseException as error:
            meta['binding_error']=f'{type(error).__name__}: {error}'
            if meta['status']=='complete':meta.update(status='failed',error='final input binding failed')
        meta['elapsed_seconds']=time.monotonic()-started
        meta['output_sha256']={p.name:digest(p) for p in OUTPUT.iterdir() if p.name!='metadata.json' and p.is_file()}
        save(OUTPUT/'metadata.json',meta)
        if meta['status']=='failed' and 'binding_error' in meta:raise ValueError(meta['binding_error'])
        if meta.get('error')=='bound inputs changed at finalization':raise ValueError(meta['error'])


if __name__=='__main__':main()
