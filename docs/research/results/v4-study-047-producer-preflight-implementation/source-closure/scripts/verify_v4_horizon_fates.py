"""Rebuild saved-trace fates via simultaneous owner counts, not saved classifications."""
from pathlib import Path
from fractions import Fraction
from itertools import product
import json
from scripts.horizon_fate_inputs import bindings,source_rows,read,digest,validate_grid

TICKS=(100,200,300,400)
CATEGORIES=('extinct','continuous_retained','continuous_replaced','broken_retained','broken_replaced')
BINS=('001-100','101-200','201-300','301-400','never')
ORDERS=('neither','break_only','replacement_only','break_first','same_tick','replacement_first')
STATES=('extinct','fragmented','mixed','closed_singleton','never')
TIMING=tuple(f'{prefix}:{value}' for prefix,values in (('break_bin',BINS),('replacement_bin',BINS),('order',ORDERS),('break_state',STATES)) for value in values)

def rebuild(initial,rows,final,checkpoints=TICKS,saved=None):
    assert checkpoints and all(type(t) is int and 0<t<=len(rows) for t in checkpoints)
    assert len(set(checkpoints))==len(checkpoints)
    initial_groups=initial['observation']['components']['material']
    flat=[v for group in initial_groups for v in group];assert len(flat)==len(set(flat))
    original={i:set(g) for i,g in enumerate(initial_groups)}
    initial_owner={v:i for i,g in original.items() for v in g}
    parents=final['parents'];owners={}
    for i,parent in enumerate(parents):
        if i in initial_owner:owners[i]=initial_owner[i]
        else:
            assert type(parent) is int and 0<=parent<i
            owners[i]=owners[parent]
    eligible={i:g for i,g in original.items() if 2<=len(g)<len(flat)}
    records={i:dict(component=i,anchor_members=sorted(g),checkpoints={},first_break_tick=None,first_complete_replacement_tick=None,first_break_state='never') for i,g in eligible.items()}
    for t,row in enumerate(rows,1):
        assert row['tick']==t
        groups=row['observation']['components']['material'];living=[v for g in groups for v in g]
        assert len(living)==len(set(living)) and set(living)=={v for v in row['site_ids'] if v is not None}
        descendants=dict.fromkeys(eligible,0);survivors=dict.fromkeys(eligible,0);destinations=dict.fromkeys(eligible,0);outside=dict.fromkeys(eligible,0)
        for group in groups:
            counts={}
            for v in group:
                owner=owners[v];counts[owner]=counts.get(owner,0)+1
                if owner in eligible:
                    descendants[owner]+=1
                    survivors[owner]+=int(v in eligible[owner])
            for owner,count in counts.items():
                if owner in eligible:
                    destinations[owner]+=1;outside[owner]+=len(group)-count
        for i,record in records.items():
            n,o=descendants[i],survivors[i]
            state='extinct' if n==0 else 'fragmented' if destinations[i]>1 else 'mixed' if outside[i] else 'closed_singleton' if n==1 else 'closed_multi'
            if state!='closed_multi' and record['first_break_tick'] is None:
                record['first_break_tick']=t;record['first_break_state']=state
            if n>0 and o==0 and record['first_complete_replacement_tick'] is None:record['first_complete_replacement_tick']=t
            continuous=record['first_break_tick'] is None
            if t in checkpoints:
                category='extinct' if n==0 else ('continuous_' if continuous else 'broken_')+('retained' if o else 'replaced')
                record['checkpoints'][str(t)]=dict(category=category,original_survivors=o,descendants=n,continuous=continuous)
                if saved is not None:
                    c=saved[str(t)][i];assert c['component']==i and c['anchor_members']==record['anchor_members']
                    assert c['first_break_tick']==record['first_break_tick'] and c['first_complete_replacement_tick']==record['first_complete_replacement_tick']
                    assert c['endpoint']['state']==state and c['endpoint']['descendants']==n and c['endpoint']['original_survivors']==o
                    assert c['continuous_closed_multi']==continuous and c['complete_replacement']==(n>0 and o==0)
                    assert c['primary']==(continuous and n>0 and o==0)
    for record in records.values():
        b,r=record['first_break_tick'],record['first_complete_replacement_tick']
        record['order']='neither' if b is None and r is None else 'replacement_only' if b is None else 'break_only' if r is None else 'break_first' if b<r else 'same_tick' if b==r else 'replacement_first'
    return list(records.values())

def independent_results(branches):
    validate_grid(branches);results=[]
    for branch in branches:
        components=branch['components'];n=len(components);snapshots={};timing=dict.fromkeys(TIMING,0)
        for tick in TICKS:
            counts={key:sum(c['checkpoints'][str(tick)]['category']==key for c in components) for key in CATEGORIES}
            assert sum(counts.values())==n
            snapshots[str(tick)]=dict(counts=counts,fractions={key:str(Fraction(v,n)) if n else None for key,v in counts.items()})
        for c in components:
            for prefix,key in (('break_bin','first_break_tick'),('replacement_bin','first_complete_replacement_tick')):
                t=c[key];assert t is None or type(t) is int and 1<=t<=400
                b='never' if t is None else BINS[(t-1)//100];timing[prefix+':'+b]+=1
            timing['order:'+c['order']]+=1;timing['break_state:'+c['first_break_state']]+=1
        assert sum(timing.values())==4*n
        results.append(dict(**{k:branch[k] for k in ('history','seed','mutation','exchange')},status='complete',eligible=n,checkpoints=snapshots,timing=dict(counts=timing,fractions={k:str(Fraction(v,n)) if n else None for k,v in timing.items()})))
    return results

def independent_summary(rows):
    validate_grid(rows)
    for row in rows:
        assert row['status']=='complete' and type(row['eligible']) is int and row['eligible']>=0
        assert set(row['checkpoints'])=={str(t) for t in TICKS}
        for node,keys in [(row['checkpoints'][str(t)],CATEGORIES) for t in TICKS]+[(row['timing'],TIMING)]:
            assert set(node['counts'])==set(keys)==set(node['fractions'])
            assert all(type(v) is int and 0<=v<=row['eligible'] for v in node['counts'].values())
            assert node['fractions']=={k:str(Fraction(v,row['eligible'])) if row['eligible'] else None for k,v in node['counts'].items()}
        assert all(sum(row['checkpoints'][str(t)]['counts'].values())==row['eligible'] for t in TICKS)
        for prefix in ('break_bin','replacement_bin','order','break_state'):
            assert sum(v for k,v in row['timing']['counts'].items() if k.startswith(prefix+':'))==row['eligible']
    indexed={(r['history'],r['seed'],r['mutation'],r['exchange']):r for r in rows}
    def mean(values):
        v=[Fraction(x) for x in values if x is not None]
        return dict(mean=str(sum(v)/len(v)) if v else None,available=len(v),missing=len(values)-len(v))
    def value(row,tick,key):return row['timing']['fractions'][key] if tick is None else row['checkpoints'][str(tick)]['fractions'][key]
    answer={}
    for label,ticks,keys in (('checkpoint',TICKS,CATEGORIES),('timing',(None,),TIMING)):
        cells=[];pairs=[];groups=[]
        for h,m,e,t in product((True,False),(0,100),(True,False),ticks):
            entry=dict(history=h,mutation=m,exchange=e,metrics={k:mean([value(indexed[h,s,m,e],t,k) for s in range(112000,112005)]) for k in keys})
            if t is not None:entry['tick']=t
            cells.append(entry)
        for h,s,m in product((True,False),range(112000,112005),(0,100)):
            a,b=indexed[h,s,m,True],indexed[h,s,m,False];assert a['eligible']==b['eligible']
            result=dict(history=h,seed=s,mutation=m);checkpoints={}
            for t in ticks:
                metrics={}
                for k in keys:
                    av,bv=value(a,t,k),value(b,t,k);assert (av is None)==(bv is None)
                    metrics[k]=dict(on=av,off=bv,difference=str(Fraction(av)-Fraction(bv)) if av is not None else None)
                if t is None:result['metrics']=metrics
                else:checkpoints[str(t)]=metrics
            if label=='checkpoint':result['checkpoints']=checkpoints
            pairs.append(result)
        for h,m,t in product((True,False),(0,100),ticks):
            selected=[p for p in pairs if p['history'] is h and p['mutation']==m]
            result=dict(history=h,mutation=m,metrics={k:mean([(p['metrics'] if t is None else p['checkpoints'][str(t)])[k]['difference'] for p in selected]) for k in keys})
            if t is not None:result['tick']=t
            groups.append(result)
        answer[label+'_cells']=cells;answer[label+'_pairs']=pairs;answer[label+'_groups']=groups
    return answer

def main():
    root=Path('data/v4-study-016-fates');source=Path('data/v4-study-016')
    files=('metadata.json','records.json','results.json','summary.json');before={name:digest(root/name) for name in files}
    meta=read(root/'metadata.json')
    assert meta['status']=='complete' and meta['planned_branches']==meta['completed_branches']==40
    assert meta['new_simulation_steps']==meta['new_independent_sources']==0 and meta['reused_independent_sources']==5
    assert meta['time_limit_seconds']==1200 and meta['storage_limit_bytes']==100*1024**2 and meta['elapsed_seconds']<1200
    assert sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<100*1024**2
    assert meta['input_sha256']==meta['input_sha256_after']==bindings()
    assert meta['output_sha256']=={n:digest(root/n) for n in files[1:]}
    saved_records=read(root/'records.json');validate_grid(saved_records)
    record_index={(r['history'],r['seed'],r['mutation'],r['exchange']):r for r in saved_records}
    rebuilt=[];steps_count=0
    for source_row in source_rows():
        directory=source/source_row['directory'];initial=read(directory/'initial.json');final=read(directory/'final.json')
        rows=[json.loads(line) for line in (directory/'steps.jsonl').read_text().splitlines()]
        assert len(rows)==400;steps_count+=len(rows)
        components=rebuild(initial,rows,final,saved=source_row['records'])
        branch=dict(**{k:source_row[k] for k in ('history','seed','mutation','exchange')},components=components)
        assert branch==record_index[branch['history'],branch['seed'],branch['mutation'],branch['exchange']]
        rebuilt.append(branch)
    results=independent_results(rebuilt);summary=independent_summary(results)
    assert results==read(root/'results.json') and summary==read(root/'summary.json')
    assert meta['input_sha256']==bindings() and before=={name:digest(root/name) for name in files}
    proof=dict(status='verified',branches=40,pairs=20,steps=steps_count,eligible_component_branches=sum(r['eligible'] for r in results),checkpoints=4,
               new_simulation_steps=0,new_independent_sources=0,reused_independent_sources=5,input_files=len(meta['input_sha256']),
               files_sha256=before,verifier_sha256=digest(Path(__file__)),scope='independent simultaneous owner-count reconstruction from all saved identities/material partitions/parents, saved checkpoint equality, exact five-source fate and event-order summaries; no new physical simulation')
    with (root/'independent-verification.json').open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))

if __name__=='__main__':
    try:main()
    except BaseException as error:
        root=Path('data/v4-study-016-fates')
        if root.is_dir() and not (root/'verification-failure.json').exists():
            with (root/'verification-failure.json').open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise
