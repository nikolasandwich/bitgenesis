"""Whole attributed component translation fingerprints on saved trajectories."""
import json
import subprocess
import time
from fractions import Fraction
from itertools import product
from pathlib import Path

SERIES=('descendant_material','descendant_genetic','unrelated_material','unrelated_genetic')
METRICS=tuple(s+'_'+suffix for s in SERIES for suffix in ('ever','persistent'))
IDENTITY=('history','seed','mutation','exchange')
GRID=tuple(product((True,False),range(112000,112005),(0,100),(True,False)))
OUTPUT=Path('data/v4-study-017')
SECONDS=1200
STORAGE=200*1024**2


def require(condition,message):
    if not condition:raise ValueError(message)


def canonical(points,width=16,height=16):
    """The least translated attributed point set; never rotate program axes."""
    require(type(width) is int and type(height) is int and width>0 and height>0,'positive integer world dimensions')
    points=tuple(tuple(p) for p in points)
    require(points and len({p[:2] for p in points})==len(points),'nonempty unique point locations')
    arity=len(points[0]);require(arity in (3,4) and all(len(p)==arity for p in points),'consistent attributed point shape')
    for p in points:
        x,y,material=p[:3]
        require(type(x) is int and type(y) is int and 0<=x<width and 0<=y<height and type(material) is int and 0<=material<4,'valid attributed coordinates')
        if arity==4:require(type(p[3]) is tuple and len(p[3])==4 and all(type(v) is int and 0<=v<4 for v in p[3]),'four absolute program directions')
    return min(tuple(sorted(((p[0]-x)%width,(p[1]-y)%height,*p[2:]) for p in points)) for x,y,*_ in points)


def episodes(counts):
    require(all(type(v) is int and v>=0 for v in counts),'nonnegative integer matching counts')
    output=[];start=None
    for tick,n in enumerate(counts,1):
        if n>=2 and start is None:start=tick
        if n<2 and start is not None:output.append([start,tick-1]);start=None
    if start is not None:output.append([start,len(counts)])
    return output


def analyze(initial,rows,final,width=16,height=16):
    """Index complete final components, then test each original parent cohort."""
    require(type(width) is int and type(height) is int and width>0 and height>0,'world dimensions')
    capacity=width*height;parents=final['parents'];initial_groups=initial['observation']['components']['material']
    def observe(ids,units,groups):
        require(len(ids)==len(units)==capacity,'world site coverage')
        occupied={}
        for site,i in enumerate(ids):
            require((i is None)==(units[site] is None),'identity unit occupancy')
            if i is not None:
                require(type(i) is int and 0<=i<len(parents) and i not in occupied,'unique valid live identities')
                occupied[i]=site
        flat=[i for g in groups for i in g]
        require(all(g for g in groups) and len(flat)==len(set(flat)) and set(flat)==set(occupied),'complete disjoint material components')
        return occupied
    initial_sites=observe(initial['site_ids'],initial['units'],initial_groups)
    owner={i:index for index,g in enumerate(initial_groups) for i in g};roots=[]
    for i,parent in enumerate(parents):
        require(parent is None or type(parent) is int and 0<=parent<i,'ordered final parent chain')
        roots.append(owner[i] if i in owner else None if parent is None else roots[parent])
    eligible=[index for index,g in enumerate(initial_groups) if 2<=len(g)<len(initial_sites)]
    sizes={len(initial_groups[i]) for i in eligible};cache={}
    def fingerprints(group,sites,units):
        genetic=tuple(sorted((sites[i]%width,sites[i]//width,units[sites[i]]['material'],tuple(units[sites[i]]['program'])) for i in group))
        if genetic not in cache:
            if len(cache)>=4096:cache.clear()
            cache[genetic]=(canonical(tuple(p[:3] for p in genetic),width,height),canonical(genetic,width,height))
        return cache[genetic]
    original_prints={i:fingerprints(initial_groups[i],initial_sites,initial['units']) for i in eligible}
    series={i:{key:[] for key in SERIES} for i in eligible}
    for tick,row in enumerate(rows,1):
        require(type(row['tick']) is int and row['tick']==tick and tick<=400,'ordered relative steps')
        ids=row['site_ids'];units=row['physical']['units'];groups=row['observation']['components']['material']
        sites=observe(ids,units,groups);require(all(roots[i] is not None for i in sites),'living identity needs initial ancestry')
        material_index={};genetic_index={}
        for group in groups:
            if len(group) not in sizes:continue
            m,g=fingerprints(group,sites,units);origins=frozenset(roots[i] for i in group)
            material_index.setdefault(m,[]).append(origins);genetic_index.setdefault(g,[]).append(origins)
        for i in eligible:
            m,g=original_prints[i]
            for kind,index,key in (('material',material_index,m),('genetic',genetic_index,g)):
                matches=index.get(key,[])
                series[i]['descendant_'+kind].append(sum(origins=={i} for origins in matches))
                series[i]['unrelated_'+kind].append(sum(i not in origins for origins in matches))
    if rows:require(rows[-1]['site_ids']==final['site_ids'],'final saved identities')
    output=[]
    for i in eligible:
        spans={k:episodes(v) for k,v in series[i].items()}
        output.append(dict(component=i,anchor_members=sorted(initial_groups[i]),anchor_size=len(initial_groups[i]),impossible_double=2*len(initial_groups[i])>capacity,series=series[i],episodes=spans,longest={k:max((end-start+1 for start,end in v),default=0) for k,v in spans.items()}))
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
    counts=dict.fromkeys(METRICS,0);all_members=[]
    for p in parents:
        n=p['anchor_size'];members=p['anchor_members'];all_members.extend(members)
        require(type(n) is int and 2<=n<256 and len(members)==n and members==sorted(set(members)) and all(type(i) is int and i>=0 for i in members),'original eligible cohort')
        require(type(p['impossible_double']) is bool and p['impossible_double']==(2*n>256),'geometric impossibility flag')
        require(set(p['series'])==set(p['episodes'])==set(p['longest'])==set(SERIES),'four complete series')
        for s in SERIES:
            values=p['series'][s];require(len(values)==400,'four hundred recorded counts')
            spans=episodes(values);longest=max((end-start+1 for start,end in spans),default=0)
            require(all(v<=256//n for v in values),'component count limited by world capacity')
            require(p['episodes'][s]==spans and type(p['longest'][s]) is int and p['longest'][s]==longest,'exact inclusive episodes and longest interval')
            counts[s+'_ever']+=longest>=1;counts[s+'_persistent']+=longest>=10
        for t in range(400):
            require(p['series']['descendant_genetic'][t]<=p['series']['descendant_material'][t] and p['series']['unrelated_genetic'][t]<=p['series']['unrelated_material'][t],'genetic subset of material matches')
            require(p['series']['descendant_material'][t]+p['series']['unrelated_material'][t]<=256//n,'distinct full matching components')
    require(len(all_members)==len(set(all_members)),'original parents cannot overlap')
    n=len(parents)
    return dict(zip(IDENTITY,key),status='complete',eligible=n,counts=counts,fractions={k:str(Fraction(v,n)) if n else None for k,v in counts.items()})


def summarize_records(rows):
    index=index_grid(rows)
    for h,s,m in product((True,False),range(112000,112005),(0,100)):
        a,b=index[h,s,m,True],index[h,s,m,False]
        require([(p['component'],p['anchor_members'],p['anchor_size'],p['impossible_double']) for p in a['parents']]==[(p['component'],p['anchor_members'],p['anchor_size'],p['impossible_double']) for p in b['parents']],'same paired original parents')
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
            require(type(v) is int and 0<=v<=n,'bounded integer event count')
            require(r['fractions'][k]==(str(Fraction(v,n)) if n else None),'canonical exact fractions and zero-denominator null')
        for s in SERIES:require(r['counts'][s+'_persistent']<=r['counts'][s+'_ever'],'persistent subset of ever')
        for prefix in ('descendant','unrelated'):
            for suffix in ('ever','persistent'):require(r['counts'][prefix+'_genetic_'+suffix]<=r['counts'][prefix+'_material_'+suffix],'genetic event subset of material')
    cells=[];pairs=[];groups=[]
    for h,m,e in product((True,False),(0,100),(True,False)):
        cells.append(dict(history=h,mutation=m,exchange=e,metrics={k:average([index[h,s,m,e]['fractions'][k] for s in range(112000,112005)]) for k in METRICS}))
    for h,s,m in product((True,False),range(112000,112005),(0,100)):
        a,b=index[h,s,m,True],index[h,s,m,False];require(a['eligible']==b['eligible'],'paired eligible denominator')
        metrics={}
        for k in METRICS:
            av,bv=a['fractions'][k],b['fractions'][k];require((av is None)==(bv is None),'paired missingness')
            metrics[k]=dict(on=av,off=bv,difference=None if av is None else str(Fraction(av)-Fraction(bv)))
        pairs.append(dict(history=h,seed=s,mutation=m,metrics=metrics))
    for h,m in product((True,False),(0,100)):
        selected=[p for p in pairs if p['history'] is h and p['mutation']==m]
        groups.append(dict(history=h,mutation=m,metrics={k:average([p['metrics'][k]['difference'] for p in selected]) for k in METRICS}))
    return dict(cells=cells,pairs=pairs,groups=groups)


def save(path,value):path.write_text(json.dumps(value,separators=(',',':'))+'\n')


def main():
    from scripts.structure_copy_inputs import bindings,source_rows,read,digest
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch required')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();records=[];results=[]
    meta=dict(status='running',planned_branches=40,completed_branches=0,new_simulation_steps=0,new_independent_sources=0,reused_independent_sources=5,time_limit_seconds=SECONDS,storage_limit_bytes=STORAGE)
    save(OUTPUT/'metadata.json',meta);save(OUTPUT/'records.json',records);save(OUTPUT/'results.json',results)
    def budget():
        require(time.monotonic()-started<SECONDS,'time budget exceeded')
        require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<STORAGE,'storage budget exceeded')
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();meta['input_sha256']=bindings();save(OUTPUT/'metadata.json',meta)
        index=index_grid(source_rows())
        for key in GRID:
            budget();require(bindings()==meta['input_sha256'],'bound inputs changed during run')
            r=index[key];require(r['status']=='complete','source branch must be complete')
            directory=Path('data/v4-study-016')/r['directory'];branch_meta=read(directory/'metadata.json');parameters=read(Path(branch_meta['source'])/'metadata.json')
            require(parameters['width']==parameters['height']==16,'frozen periodic world size')
            rows=[json.loads(line) for line in (directory/'steps.jsonl').read_text().splitlines()];require(len(rows)==400,'full fixed horizon')
            record=dict(zip(IDENTITY,key),parents=analyze(read(directory/'initial.json'),rows,read(directory/'final.json'),parameters['width'],parameters['height']))
            result=branch_result(record);records.append(record);results.append(result);meta['completed_branches']=len(records)
            save(OUTPUT/'records.json',records);save(OUTPUT/'results.json',results);save(OUTPUT/'metadata.json',meta)
            print(f'{len(records)}/40 saved structure-copy branches',flush=True)
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
