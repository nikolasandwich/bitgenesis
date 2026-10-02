"""Direct translated point-set matching, independent of production fingerprints."""
from pathlib import Path
from functools import lru_cache
from collections import Counter
from fractions import Fraction
from itertools import product
import json
from scripts.structure_copy_inputs import bindings,source_rows,read,digest

SERIES=('descendant_material','descendant_genetic','unrelated_material','unrelated_genetic')
METRICS=tuple(s+'_'+suffix for s in SERIES for suffix in ('ever','persistent'))
GRID=tuple(product((True,False),range(112000,112005),(0,100),(True,False)))

@lru_cache(maxsize=8192)
def translated_equal(a,b,width=16,height=16):
    assert type(width) is int and type(height) is int and width>0 and height>0
    for points in (a,b):
        assert len({p[:2] for p in points})==len(points)
        assert all(type(p[0]) is int and type(p[1]) is int and 0<=p[0]<width and 0<=p[1]<height for p in points)
    if len(a)!=len(b) or Counter(p[2:] for p in a)!=Counter(p[2:] for p in b):return False
    if not a:return True
    reference=a[0];target=set(b)
    for q in b:
        if reference[2:]!=q[2:]:continue
        dx,dy=q[0]-reference[0],q[1]-reference[1]
        if {((p[0]+dx)%width,(p[1]+dy)%height,*p[2:]) for p in a}==target:return True
    return False

def intervals(counts):
    assert all(type(v) is int and v>=0 for v in counts)
    result=[];start=None
    for tick,n in enumerate(list(counts)+[0],1):
        if n>=2 and start is None:start=tick
        elif n<2 and start is not None:result.append([start,tick-1]);start=None
    return result

def points(ids,units,members,width):
    return tuple((site%width,site//width,units[site]['material'],tuple(units[site]['program'])) for site,i in enumerate(ids) if i in members)

def recount(initial,rows,final,width=16,height=16):
    ids=initial['site_ids'];units=initial['units'];assert len(ids)==len(units)==width*height
    groups=initial['observation']['components']['material'];founders={i:group for group,g in enumerate(groups) for i in g}
    assert all(groups) and sum(map(len,groups))==len(founders)==sum(i is not None for i in ids)
    assert set(founders)=={i for i in ids if i is not None}
    owners={}
    for i,parent in enumerate(final['parents']):
        if i in founders:owners[i]=founders[i]
        else:
            assert parent is None or type(parent) is int and 0<=parent<i
            owners[i]=None if parent is None else owners[parent]
    parents=[];parent_points={}
    for index,g in enumerate(groups):
        if not 2<=len(g)<len(founders):continue
        parent_points[index]=points(ids,units,set(g),width)
        parents.append(dict(component=index,anchor_members=sorted(g),anchor_size=len(g),impossible_double=2*len(g)>width*height,series={k:[] for k in SERIES}))
    for t,row in enumerate(rows,1):
        assert type(row['tick']) is int and row['tick']==t and t<=400
        current=row['site_ids'];physical=row['physical']['units'];assert len(current)==len(physical)==width*height
        assert all((i is None)==(u is None) for i,u in zip(current,physical))
        assert all(owners[i] is not None for i in current if i is not None)
        objects=row['observation']['components']['material'];flat=[v for g in objects for v in g]
        assert all(objects) and len(flat)==len(set(flat)) and set(flat)=={v for v in current if v is not None}
        assert len(flat)==sum(v is not None for v in current)
        indexed={}
        for g in objects:
            if len(g)<2:continue
            p=points(current,physical,set(g),width);material=tuple(x[:3] for x in p)
            indexed.setdefault(len(g),[]).append((p,material,{owners[i] for i in g}))
        for parent in parents:
            i=parent['component'];p=parent_points[i];material=tuple(x[:3] for x in p);counts=dict.fromkeys(SERIES,0)
            for q,qmaterial,roots in indexed.get(parent['anchor_size'],[]):
                label='descendant' if roots=={i} else 'unrelated' if i not in roots else None
                if label is None:continue
                if translated_equal(material,qmaterial,width,height):
                    counts[label+'_material']+=1
                    if translated_equal(p,q,width,height):counts[label+'_genetic']+=1
            for k in SERIES:parent['series'][k].append(counts[k])
    for parent in parents:
        parent['episodes']={k:intervals(parent['series'][k]) for k in SERIES}
        parent['longest']={k:max((b-a+1 for a,b in parent['episodes'][k]),default=0) for k in SERIES}
    return parents

def grid(rows):
    assert len(rows)==40 and all(type(r['history']) is bool and type(r['exchange']) is bool and type(r['seed']) is int and type(r['mutation']) is int for r in rows)
    assert {(r['history'],r['seed'],r['mutation'],r['exchange']) for r in rows}==set(GRID)

def make_results(records):
    grid(records);results=[];indexed={(r['history'],r['seed'],r['mutation'],r['exchange']):r for r in records}
    for key in GRID:
        branch=indexed[key]
        ps=branch['parents'];counts=dict.fromkeys(METRICS,0)
        assert [p['component'] for p in ps]==sorted({p['component'] for p in ps})
        for p in ps:
            assert p['anchor_size']==len(p['anchor_members'])>=2 and len(set(p['anchor_members']))==p['anchor_size']
            assert type(p['impossible_double']) is bool and p['impossible_double'] is (2*p['anchor_size']>256)
            assert set(p['series'])==set(p['episodes'])==set(p['longest'])==set(SERIES)
            for k in SERIES:
                values=p['series'][k];assert len(values)==400 and all(type(n) is int and 0<=n<=256//p['anchor_size'] for n in values)
                episodes=intervals(values);longest=max((b-a+1 for a,b in episodes),default=0)
                assert p['episodes'][k]==episodes and p['longest'][k]==longest
                counts[k+'_ever']+=longest>=1;counts[k+'_persistent']+=longest>=10
            for prefix in ('descendant','unrelated'):
                assert all(g<=m for g,m in zip(p['series'][prefix+'_genetic'],p['series'][prefix+'_material']))
        n=len(ps);results.append(dict(**{k:branch[k] for k in ('history','seed','mutation','exchange')},status='complete',eligible=n,counts=counts,fractions={k:str(Fraction(v,n)) if n else None for k,v in counts.items()}))
    return results

def make_summary(rows):
    grid(rows);indexed={(r['history'],r['seed'],r['mutation'],r['exchange']):r for r in rows}
    for r in rows:
        assert r['status']=='complete' and type(r['eligible']) is int and r['eligible']>=0
        assert set(r['counts'])==set(r['fractions'])==set(METRICS)
        assert all(type(n) is int and 0<=n<=r['eligible'] for n in r['counts'].values())
        assert r['fractions']=={k:str(Fraction(n,r['eligible'])) if r['eligible'] else None for k,n in r['counts'].items()}
        for s in SERIES:assert r['counts'][s+'_persistent']<=r['counts'][s+'_ever']
        for prefix in ('descendant','unrelated'):
            for suffix in ('ever','persistent'):assert r['counts'][prefix+'_genetic_'+suffix]<=r['counts'][prefix+'_material_'+suffix]
    def average(values):
        valid=[Fraction(v) for v in values if v is not None]
        return dict(mean=str(sum(valid)/len(valid)) if valid else None,available=len(valid),missing=len(values)-len(valid))
    cells=[];pairs=[];groups=[]
    for h,m,e in product((True,False),(0,100),(True,False)):
        cells.append(dict(history=h,mutation=m,exchange=e,metrics={k:average([indexed[h,s,m,e]['fractions'][k] for s in range(112000,112005)]) for k in METRICS}))
    for h,s,m in product((True,False),range(112000,112005),(0,100)):
        a,b=indexed[h,s,m,True],indexed[h,s,m,False];assert a['eligible']==b['eligible'];metrics={}
        for k in METRICS:
            av,bv=a['fractions'][k],b['fractions'][k];assert (av is None)==(bv is None)
            metrics[k]=dict(on=av,off=bv,difference=str(Fraction(av)-Fraction(bv)) if av is not None else None)
        pairs.append(dict(history=h,seed=s,mutation=m,metrics=metrics))
    for h,m in product((True,False),(0,100)):
        selected=[p for p in pairs if p['history'] is h and p['mutation']==m]
        groups.append(dict(history=h,mutation=m,metrics={k:average([p['metrics'][k]['difference'] for p in selected]) for k in METRICS}))
    return dict(cells=cells,pairs=pairs,groups=groups)

def main():
    root=Path('data/v4-study-017');names=('metadata.json','records.json','results.json','summary.json');before={n:digest(root/n) for n in names}
    meta=read(root/'metadata.json');assert meta['status']=='complete' and meta['planned_branches']==meta['completed_branches']==40
    assert meta['new_simulation_steps']==meta['new_independent_sources']==0 and meta['reused_independent_sources']==5
    assert meta['time_limit_seconds']==1200 and meta['storage_limit_bytes']==200*1024**2 and meta['elapsed_seconds']<1200
    assert sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<200*1024**2
    assert meta['input_sha256']==meta['input_sha256_after']==bindings()
    assert meta['output_sha256']=={n:digest(root/n) for n in names[1:]}
    saved=read(root/'records.json');grid(saved);indexed={(r['history'],r['seed'],r['mutation'],r['exchange']):r for r in saved};records=[]
    for source in source_rows():
        p=Path('data/v4-study-016')/source['directory'];bm=read(p/'metadata.json');params=read(Path(bm['source'])/'metadata.json');assert params['width']==params['height']==16
        rows=[json.loads(line) for line in (p/'steps.jsonl').read_text().splitlines()];assert len(rows)==400
        parents=recount(read(p/'initial.json'),rows,read(p/'final.json'),16,16)
        record=dict(**{k:source[k] for k in ('history','seed','mutation','exchange')},parents=parents)
        assert record==indexed[source['history'],source['seed'],source['mutation'],source['exchange']]
        records.append(record);print(f'{len(records)}/40 independently matched structure-copy branches',flush=True)
    results=make_results(records);summary=make_summary(results)
    assert results==read(root/'results.json') and summary==read(root/'summary.json')
    assert sum(r['eligible'] for r in results if r['exchange'])==824
    assert meta['input_sha256']==bindings() and before=={n:digest(root/n) for n in names}
    proof=dict(status='verified',branches=40,pairs=20,saved_steps=16000,parent_branch_records=sum(r['eligible'] for r in results),series_values=sum(r['eligible'] for r in results)*400*4,new_simulation_steps=0,new_independent_sources=0,reused_independent_sources=5,input_files=len(meta['input_sha256']),files_sha256=before,verifier_sha256=digest(Path(__file__)),scope='direct periodic translated attributed-point matching independent of canonical fingerprints; full parent-relative ancestry/unrelated counts, inclusive episodes and exact source means; candidates only')
    with (root/'independent-verification.json').open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))

if __name__=='__main__':
    try:main()
    except BaseException as error:
        root=Path('data/v4-study-017')
        if root.is_dir() and not (root/'verification-failure.json').exists():
            with (root/'verification-failure.json').open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise
