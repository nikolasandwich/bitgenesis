"""Nested necessary conditions on saved structure-copy trajectories."""
import json
import subprocess
import time
from collections import Counter
from fractions import Fraction
from itertools import product
from pathlib import Path

GATES=('population','inventory','partition','copy')
STATES=('population_fail','inventory_fail','partition_fail','copy_fail','copy_pass')
METRICS=tuple(g+'_'+suffix for g in GATES for suffix in ('ever','persistent'))
SUMMARY_METRICS=METRICS+STATES
IDENTITY=('history','seed','mutation','exchange')
GRID=tuple(product((True,False),range(112000,112005),(0,100),(True,False)))
OUTPUT=Path('data/v4-study-018')
SECONDS=1200
STORAGE=200*1024**2


def require(condition,message):
    if not condition:raise ValueError(message)


def episodes(values):
    require(all(type(v) is bool for v in values),'boolean gate sequence')
    spans=[];start=None
    for tick,value in enumerate(values,1):
        if value and start is None:start=tick
        if not value and start is not None:spans.append([start,tick-1]);start=None
    if start is not None:spans.append([start,len(values)])
    return spans


def analyze(initial,rows,final,copy_parents):
    parents=final['parents'];groups=initial['observation']['components']['material']
    def observed(ids,units,components):
        require(len(ids)==len(units),'identity/unit sites')
        live={}
        for i,u in zip(ids,units):
            require((i is None)==(u is None),'identity/unit occupancy')
            if i is not None:
                require(type(i) is int and 0<=i<len(parents) and i not in live,'unique valid live identity')
                material=u['material'];program=u['program']
                require(type(material) is int and 0<=material<4 and len(program)==4 and all(type(v) is int and 0<=v<4 for v in program),'exact material/program type')
                live[i]=(material,tuple(program))
        flat=[i for group in components for i in group]
        require(all(components) and len(flat)==len(set(flat)) and set(flat)==set(live),'full disjoint material partition')
        return live
    original=observed(initial['site_ids'],initial['units'],groups)
    owner={i:c for c,g in enumerate(groups) for i in g};roots=[]
    for i,parent in enumerate(parents):
        require(parent is None or type(parent) is int and 0<=parent<i,'ordered parent chain')
        require(i not in owner or parent is None,'initial identities are roots')
        roots.append(owner[i] if i in owner else None if parent is None else roots[parent])
    eligible=[c for c,g in enumerate(groups) if 2<=len(g)<len(original)]
    expected=[(c,sorted(groups[c]),len(groups[c])) for c in eligible]
    require([(p['component'],p['anchor_members'],p['anchor_size']) for p in copy_parents]==expected,'017 original parent binding')
    copy_index={p['component']:p for p in copy_parents}
    for p in copy_parents:
        values=p['series']['descendant_genetic']
        require(len(values)==len(rows) and all(type(v) is int and v>=0 for v in values),'017 count sequence')
    histograms={c:Counter(original[i] for i in groups[c]) for c in eligible}
    series={c:{g:[] for g in GATES} for c in eligible}
    for tick,row in enumerate(rows,1):
        require(type(row['tick']) is int and row['tick']==tick and tick<=400,'ordered relative steps')
        components=row['observation']['components']['material']
        live=observed(row['site_ids'],row['physical']['units'],components)
        require(all(roots[i] is not None for i in live),'living identity needs initial ancestry')
        inventories={c:Counter() for c in eligible};matches=Counter()
        for group in components:
            origins={roots[i] for i in group}
            histogram=Counter(live[i] for i in group)
            for i in group:
                if roots[i] in inventories:inventories[roots[i]][live[i]]+=1
            if len(origins)==1:
                c=next(iter(origins))
                if c in histograms and histogram==histograms[c]:matches[c]+=1
        for c in eligible:
            inventory=inventories[c];original_hist=histograms[c]
            gates=(sum(inventory.values())>=2*len(groups[c]),all(inventory[k]>=2*v for k,v in original_hist.items()),matches[c]>=2,copy_index[c]['series']['descendant_genetic'][tick-1]>=2)
            require(all(not gates[i+1] or gates[i] for i in range(3)),'copy/partition/inventory/population nesting')
            for gate,value in zip(GATES,gates):series[c][gate].append(value)
    if rows:require(rows[-1]['site_ids']==final['site_ids'],'final identities')
    output=[]
    for c in eligible:
        spans={g:episodes(series[c][g]) for g in GATES};steps=dict.fromkeys(STATES,0)
        for flags in zip(*(series[c][g] for g in GATES)):
            steps[STATES[next((i for i,v in enumerate(flags) if not v),4)]]+=1
        output.append(dict(component=c,anchor_members=sorted(groups[c]),anchor_size=len(groups[c]),series=series[c],episodes=spans,
            longest={g:max((b-a+1 for a,b in spans[g]),default=0) for g in GATES},state_steps=steps))
    return output


def identity(row):
    require(type(row['history']) is bool and type(row['exchange']) is bool and type(row['seed']) is int and type(row['mutation']) is int,'strict branch identity types')
    return tuple(row[k] for k in IDENTITY)


def index_grid(rows):
    keys=[identity(r) for r in rows]
    require(len(keys)==40 and set(keys)==set(GRID),'complete unique forty branch grid')
    return dict(zip(keys,rows))


def branch_result(row):
    key=identity(row);parents=row['parents'];ids=[p['component'] for p in parents]
    require(all(type(i) is int and i>=0 for i in ids) and ids==sorted(set(ids)),'unique ordered parent components')
    counts=dict.fromkeys(METRICS,0);state_steps=dict.fromkeys(STATES,0);all_members=[]
    for p in parents:
        n=p['anchor_size'];members=p['anchor_members'];all_members.extend(members)
        require(type(n) is int and 2<=n<256 and len(members)==n and members==sorted(set(members)) and all(type(i) is int and i>=0 for i in members),'original eligible cohort')
        require(set(p['series'])==set(p['episodes'])==set(p['longest'])==set(GATES),'four complete gate series')
        for g in GATES:
            values=p['series'][g];require(len(values)==400,'four hundred recorded gates')
            spans=episodes(values);longest=max((b-a+1 for a,b in spans),default=0)
            require(p['episodes'][g]==spans and type(p['longest'][g]) is int and p['longest'][g]==longest,'exact episodes and longest')
            counts[g+'_ever']+=longest>=1;counts[g+'_persistent']+=longest>=10
        steps=dict.fromkeys(STATES,0)
        for flags in zip(*(p['series'][g] for g in GATES)):
            require(all(not flags[i+1] or flags[i] for i in range(3)),'nested gate series')
            steps[STATES[next((i for i,v in enumerate(flags) if not v),4)]]+=1
        require(p['state_steps']==steps and all(type(v) is int for v in p['state_steps'].values()),'exact five state counts')
        for s in STATES:state_steps[s]+=steps[s]
    require(len(all_members)==len(set(all_members)),'original parents cannot overlap')
    n=len(parents)
    return dict(zip(IDENTITY,key),status='complete',eligible=n,counts=counts,
        fractions={k:str(Fraction(v,n)) if n else None for k,v in counts.items()},state_steps=state_steps,
        state_fractions={s:str(Fraction(v,400*n)) if n else None for s,v in state_steps.items()})


def summarize_records(rows):
    index=index_grid(rows)
    for h,s,m in product((True,False),range(112000,112005),(0,100)):
        a,b=index[h,s,m,True],index[h,s,m,False]
        require([(p['component'],p['anchor_members'],p['anchor_size']) for p in a['parents']]==[(p['component'],p['anchor_members'],p['anchor_size']) for p in b['parents']],'same paired original parents')
    results=[branch_result(index[k]) for k in GRID]
    return results,aggregate(results)


def average(values):
    available=[Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(available)/len(available)) if available else None,available=len(available),missing=len(values)-len(available))


def aggregate(rows):
    index=index_grid(rows)
    for r in rows:
        n=r['eligible'];require(r['status']=='complete' and type(n) is int and n>=0,'complete branch denominator')
        require(set(r['counts'])==set(r['fractions'])==set(METRICS),'eight complete metrics')
        for k,v in r['counts'].items():
            require(type(v) is int and 0<=v<=n,'bounded event count')
            require(r['fractions'][k]==(str(Fraction(v,n)) if n else None),'canonical event fractions')
        for g in GATES:require(r['counts'][g+'_persistent']<=r['counts'][g+'_ever'],'persistent subset of ever')
        for suffix in ('ever','persistent'):
            require(all(r['counts'][GATES[i+1]+'_'+suffix]<=r['counts'][GATES[i]+'_'+suffix] for i in range(3)),'nested event counts')
        require(set(r['state_steps'])==set(r['state_fractions'])==set(STATES),'five complete states')
        require(sum(r['state_steps'].values())==400*n,'exhaustive state counts')
        for s,v in r['state_steps'].items():
            require(type(v) is int and 0<=v<=400*n,'bounded integer state count')
            require(r['state_fractions'][s]==(str(Fraction(v,400*n)) if n else None),'canonical state fractions')
    def values(row):return dict(row['fractions'],**row['state_fractions'])
    cells=[];pairs=[];groups=[]
    for h,m,e in product((True,False),(0,100),(True,False)):
        cells.append(dict(history=h,mutation=m,exchange=e,metrics={k:average([values(index[h,s,m,e])[k] for s in range(112000,112005)]) for k in SUMMARY_METRICS}))
    for h,s,m in product((True,False),range(112000,112005),(0,100)):
        a,b=index[h,s,m,True],index[h,s,m,False];require(a['eligible']==b['eligible'],'paired eligible denominator')
        metrics={}
        for k in SUMMARY_METRICS:
            av,bv=values(a)[k],values(b)[k];require((av is None)==(bv is None),'paired missingness')
            metrics[k]=dict(on=av,off=bv,difference=None if av is None else str(Fraction(av)-Fraction(bv)))
        pairs.append(dict(history=h,seed=s,mutation=m,metrics=metrics))
    for h,m in product((True,False),(0,100)):
        selected=[p for p in pairs if p['history'] is h and p['mutation']==m]
        groups.append(dict(history=h,mutation=m,metrics={k:average([p['metrics'][k]['difference'] for p in selected]) for k in SUMMARY_METRICS}))
    return dict(cells=cells,pairs=pairs,groups=groups)


def save(path,value):path.write_text(json.dumps(value,separators=(',',':'))+'\n')


def main():
    from scripts.copy_bottleneck_inputs import bindings,source_rows,read,digest
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch required')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();records=[];results=[]
    meta=dict(status='running',planned_branches=40,completed_branches=0,new_simulation_steps=0,new_independent_sources=0,reused_independent_sources=5,time_limit_seconds=SECONDS,storage_limit_bytes=STORAGE)
    save(OUTPUT/'metadata.json',meta);save(OUTPUT/'records.json',records);save(OUTPUT/'results.json',results)
    def budget():
        require(time.monotonic()-started<SECONDS,'time budget exceeded')
        require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<STORAGE,'storage budget exceeded')
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();meta['input_sha256']=bindings();require(len(meta['input_sha256'])==1631,'complete frozen input inventory');save(OUTPUT/'metadata.json',meta)
        index=index_grid(source_rows());copies=index_grid(read(Path('data/v4-study-017/records.json')))
        for key in GRID:
            budget();require(bindings()==meta['input_sha256'],'bound inputs changed during run')
            r=index[key];require(r['status']=='complete','source branch must be complete')
            directory=Path('data/v4-study-016')/r['directory'];branch_meta=read(directory/'metadata.json');parameters=read(Path(branch_meta['source'])/'metadata.json')
            require(parameters['width']==parameters['height']==16,'frozen periodic world size')
            rows=[json.loads(line) for line in (directory/'steps.jsonl').read_text().splitlines()];require(len(rows)==400,'full fixed horizon')
            record=dict(zip(IDENTITY,key),parents=analyze(read(directory/'initial.json'),rows,read(directory/'final.json'),copies[key]['parents']))
            result=branch_result(record);records.append(record);results.append(result);meta['completed_branches']=len(records)
            save(OUTPUT/'records.json',records);save(OUTPUT/'results.json',results);save(OUTPUT/'metadata.json',meta)
            print(f'{len(records)}/40 saved copy-bottleneck branches',flush=True)
        results,summary=summarize_records(records);require(sum(r['eligible'] for r in results if r['exchange'])==824,'all frozen paired parent cohorts')
        save(OUTPUT/'results.json',results);save(OUTPUT/'summary.json',summary);budget()
        meta['input_sha256_after']=bindings();require(meta['input_sha256']==meta['input_sha256_after'],'bound inputs changed')
        meta.update(status='complete',output_sha256={n:digest(OUTPUT/n) for n in ('records.json','results.json','summary.json')})
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}');raise
    finally:
        try:
            meta['input_sha256_after']=bindings()
            if meta.get('input_sha256')!=meta['input_sha256_after'] and meta['status']=='complete':meta.update(status='failed',error='bound inputs changed at finalization')
        except BaseException as error:
            meta['binding_error']=f'{type(error).__name__}: {error}'
            if meta['status']=='complete':meta.update(status='failed',error='final input binding failed')
        meta['elapsed_seconds']=time.monotonic()-started
        if meta['status']=='complete' and (meta['elapsed_seconds']>=SECONDS or sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())>=STORAGE):meta.update(status='failed',error='budget exceeded at finalization')
        meta['output_sha256']={p.name:digest(p) for p in OUTPUT.iterdir() if p.name!='metadata.json' and p.is_file()}
        save(OUTPUT/'metadata.json',meta)
        if meta['status']=='failed' and 'binding_error' in meta:raise ValueError(meta['binding_error'])
        if meta.get('error') in ('bound inputs changed at finalization','budget exceeded at finalization'):raise ValueError(meta['error'])


if __name__=='__main__':main()
