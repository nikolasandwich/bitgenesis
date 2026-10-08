"""Independent live-identity inventory and complete-component prerequisite audit."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
from itertools import product
import json
from scripts.copy_bottleneck_inputs import bindings,source_rows,read,digest

GATES=('population','inventory','partition','copy')
STATES=('population_fail','inventory_fail','partition_fail','copy_fail','copy_pass')
METRICS=tuple(k+'_'+s for k in GATES for s in ('ever','persistent'))
GRID=tuple(product((True,False),range(112000,112005),(0,100),(True,False)))

def intervals(values):
    assert all(type(v) is bool for v in values)
    result=[];start=None
    for t,v in enumerate(list(values)+[False],1):
        if v and start is None:start=t
        elif not v and start is not None:result.append([start,t-1]);start=None
    return result

def recount(initial,rows,final,copy_parents):
    ids=initial['site_ids'];units=initial['units'];groups=initial['observation']['components']['material']
    assert len(ids)==len(units)==256
    founders={i:g for g,members in enumerate(groups) for i in members}
    assert len(founders)==sum(map(len,groups)) and set(founders)=={i for i in ids if i is not None}
    types={i:(u['material'],tuple(u['program'])) for i,u in zip(ids,units) if i is not None}
    owners={}
    for i,p in enumerate(final['parents']):
        assert p is None or type(p) is int and 0<=p<i
        owners[i]=founders[i] if i in founders else None if p is None else owners[p]
    eligible=[i for i,g in enumerate(groups) if 2<=len(g)<len(founders)]
    assert [p['component'] for p in copy_parents]==eligible
    original={i:Counter(types[v] for v in groups[i]) for i in eligible};outputs=[]
    for i,p in zip(eligible,copy_parents):
        assert p['anchor_size']==len(groups[i]) and p['anchor_members']==sorted(groups[i])
        assert len(p['series']['descendant_genetic'])==len(rows)
        outputs.append(dict(component=i,anchor_members=sorted(groups[i]),anchor_size=len(groups[i]),series={k:[] for k in GATES}))
    for t,row in enumerate(rows,1):
        assert type(row['tick']) is int and row['tick']==t and t<=400
        current=row['site_ids'];physical=row['physical']['units'];assert len(current)==len(physical)==256
        assert all((i is None)==(u is None) for i,u in zip(current,physical))
        alive={i:(u['material'],tuple(u['program'])) for i,u in zip(current,physical) if i is not None}
        assert len(alive)==sum(i is not None for i in current) and all(owners[i] is not None for i in alive)
        components=row['observation']['components']['material'];flat=[i for g in components for i in g]
        assert all(components) and len(flat)==len(set(flat)) and set(flat)==set(alive)
        for record,saved in zip(outputs,copy_parents):
            i=record['component'];target=original[i];desc={v for v in alive if owners[v]==i};inventory=Counter(alive[v] for v in desc)
            full=sum(len(g)==record['anchor_size'] and set(g)<=desc and Counter(alive[v] for v in g)==target for g in components)
            copies=saved['series']['descendant_genetic'][t-1];assert type(copies) is int and copies>=0
            values=[len(desc)>=2*record['anchor_size'],all(inventory[k]>=2*n for k,n in target.items()),full>=2,copies>=2]
            assert all(not values[j+1] or values[j] for j in range(3))
            for k,v in zip(GATES,values):record['series'][k].append(v)
    for p in outputs:
        p['episodes']={k:intervals(v) for k,v in p['series'].items()}
        p['longest']={k:max((b-a+1 for a,b in runs),default=0) for k,runs in p['episodes'].items()}
        p['state_steps']=dict.fromkeys(STATES,0)
        for flags in zip(*(p['series'][k] for k in GATES)):
            n=next((i for i,v in enumerate(flags) if not v),4);p['state_steps'][STATES[n]]+=1
    return outputs

def grid(rows):
    assert len(rows)==40 and all(type(r['history']) is bool and type(r['exchange']) is bool and type(r['seed']) is int and type(r['mutation']) is int for r in rows)
    assert {(r['history'],r['seed'],r['mutation'],r['exchange']) for r in rows}==set(GRID)

def make_results(records):
    grid(records);index={(r['history'],r['seed'],r['mutation'],r['exchange']):r for r in records};results=[]
    for key in GRID:
        branch=index[key];parents=branch['parents'];counts=dict.fromkeys(METRICS,0);states=dict.fromkeys(STATES,0)
        assert [p['component'] for p in parents]==sorted({p['component'] for p in parents})
        for p in parents:
            assert type(p['anchor_size']) is int and 2<=p['anchor_size']<256 and p['anchor_size']==len(p['anchor_members'])==len(set(p['anchor_members']))
            assert set(p['series'])==set(p['episodes'])==set(p['longest'])==set(GATES)
            for k in GATES:
                v=p['series'][k];assert len(v)==400
                runs=intervals(v);longest=max((b-a+1 for a,b in runs),default=0)
                assert p['episodes'][k]==runs and p['longest'][k]==longest
                counts[k+'_ever']+=longest>=1;counts[k+'_persistent']+=longest>=10
            observed=dict.fromkeys(STATES,0)
            for flags in zip(*(p['series'][k] for k in GATES)):
                assert all(not flags[j+1] or flags[j] for j in range(3))
                n=next((i for i,v in enumerate(flags) if not v),4);observed[STATES[n]]+=1
            assert observed==p['state_steps']
            for k in STATES:states[k]+=observed[k]
        n=len(parents)
        results.append(dict(**{k:branch[k] for k in ('history','seed','mutation','exchange')},status='complete',eligible=n,counts=counts,fractions={k:str(Fraction(v,n)) if n else None for k,v in counts.items()},state_steps=states,state_fractions={k:str(Fraction(v,400*n)) if n else None for k,v in states.items()}))
    for h,s,m in product((True,False),range(112000,112005),(0,100)):
        identity=lambda r:[(p['component'],p['anchor_members'],p['anchor_size']) for p in r['parents']]
        assert identity(index[h,s,m,True])==identity(index[h,s,m,False])
    return results

def make_summary(rows):
    grid(rows);index={(r['history'],r['seed'],r['mutation'],r['exchange']):r for r in rows};values={}
    for r in rows:
        n=r['eligible'];assert r['status']=='complete' and type(n) is int and n>=0
        assert set(r['counts'])==set(r['fractions'])==set(METRICS) and set(r['state_steps'])==set(r['state_fractions'])==set(STATES)
        assert all(type(v) is int and 0<=v<=n for v in r['counts'].values())
        assert all(type(v) is int and v>=0 for v in r['state_steps'].values()) and sum(r['state_steps'].values())==400*n
        assert r['fractions']=={k:str(Fraction(v,n)) if n else None for k,v in r['counts'].items()}
        assert r['state_fractions']=={k:str(Fraction(v,400*n)) if n else None for k,v in r['state_steps'].items()}
        for k in GATES:assert r['counts'][k+'_persistent']<=r['counts'][k+'_ever']
        for suffix in ('ever','persistent'):
            assert all(r['counts'][GATES[j+1]+'_'+suffix]<=r['counts'][GATES[j]+'_'+suffix] for j in range(3))
        values[r['history'],r['seed'],r['mutation'],r['exchange']]={**r['fractions'],**r['state_fractions']}
    def average(v):
        present=[Fraction(x) for x in v if x is not None]
        return dict(mean=str(sum(present)/len(present)) if present else None,available=len(present),missing=len(v)-len(present))
    metrics=METRICS+STATES;cells=[];pairs=[];groups=[]
    for h,m,e in product((True,False),(0,100),(True,False)):
        cells.append(dict(history=h,mutation=m,exchange=e,metrics={k:average([values[h,s,m,e][k] for s in range(112000,112005)]) for k in metrics}))
    for h,s,m in product((True,False),range(112000,112005),(0,100)):
        assert index[h,s,m,True]['eligible']==index[h,s,m,False]['eligible'];items={}
        for k in metrics:
            a,b=values[h,s,m,True][k],values[h,s,m,False][k];assert (a is None)==(b is None)
            items[k]=dict(on=a,off=b,difference=str(Fraction(a)-Fraction(b)) if a is not None else None)
        pairs.append(dict(history=h,seed=s,mutation=m,metrics=items))
    for h,m in product((True,False),(0,100)):
        selected=[r for r in pairs if r['history'] is h and r['mutation']==m]
        groups.append(dict(history=h,mutation=m,metrics={k:average([r['metrics'][k]['difference'] for r in selected]) for k in metrics}))
    return dict(cells=cells,pairs=pairs,groups=groups)

def main():
    root=Path('data/v4-study-018');names=('metadata.json','records.json','results.json','summary.json');before={n:digest(root/n) for n in names};meta=read(root/'metadata.json')
    assert meta['status']=='complete' and meta['planned_branches']==meta['completed_branches']==40
    assert meta['new_simulation_steps']==meta['new_independent_sources']==0 and meta['reused_independent_sources']==5
    assert meta['time_limit_seconds']==1200 and meta['storage_limit_bytes']==200*1024**2 and meta['elapsed_seconds']<1200
    assert sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<200*1024**2
    assert meta['input_sha256']==meta['input_sha256_after']==bindings()
    assert meta['output_sha256']=={n:digest(root/n) for n in names[1:]}
    saved=read(root/'records.json');grid(saved);old=read('data/v4-study-017/records.json');grid(old)
    key=lambda r:(r['history'],r['seed'],r['mutation'],r['exchange'])
    saved={key(r):r for r in saved};old={key(r):r for r in old};records=[]
    for source in source_rows():
        path=Path('data/v4-study-016')/source['directory'];rows=[json.loads(line) for line in (path/'steps.jsonl').read_text().splitlines()];assert len(rows)==400
        parents=recount(read(path/'initial.json'),rows,read(path/'final.json'),old[key(source)]['parents'])
        record=dict(**{k:source[k] for k in ('history','seed','mutation','exchange')},parents=parents)
        assert record==saved[key(source)];records.append(record)
        print(f'{len(records)}/40 independently recounted prerequisite branches',flush=True)
    results=make_results(records);summary=make_summary(results)
    assert results==read(root/'results.json') and summary==read(root/'summary.json')
    assert sum(r['eligible'] for r in results if r['exchange'])==824
    assert before=={n:digest(root/n) for n in names} and bindings()==meta['input_sha256']
    proof=dict(status='verified',branches=40,pairs=20,saved_steps=16000,parent_branch_records=1648,series_values=2636800,new_simulation_steps=0,new_independent_sources=0,reused_independent_sources=5,input_files=len(meta['input_sha256']),files_sha256=before,verifier_sha256=digest(Path(__file__)),scope='independent live-identity prerequisite reconstruction, exact nesting/episodes/state steps/source means; copy reuses independently verified study017 series')
    with (root/'independent-verification.json').open('x') as f:f.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))

if __name__=='__main__':
    try:main()
    except BaseException as error:
        p=Path('data/v4-study-018/verification-failure.json')
        if p.parent.is_dir() and not p.exists():
            with p.open('x') as f:f.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise
