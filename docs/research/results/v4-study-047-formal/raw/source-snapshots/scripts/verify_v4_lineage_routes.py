"""Study041 parent inline independent route audit: no dynamics or producer imports."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
from time import monotonic
import json
from scripts.lineage_route_inputs import bindings,input_paths,capture,read,save,digest

REGIONS=('upper','middle','lower','other')
LABELS=('left','right','other')
REASONS=('energy','occupied','raw_material','collision','formed')
OUTPUT=Path('data/v4-study-041')

def require(ok,msg):
    if not ok:raise ValueError(msg)

def same(a,b,msg):require(json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True),msg)

def region(site):
    return 'upper' if site in (85,86) else 'middle' if site in (101,102) else 'lower' if site in (117,118) else 'other'

def label_history(people,selected):
    labels=[]
    for i,p in enumerate(people):
        parent=p['parent'];require(parent is None or 0<=parent<i,'ordered parent')
        labels.append(LABELS[selected.index(i)] if i in selected else labels[parent] if parent is not None else 'other')
    return labels

def reconstruct_gates(units,raw,directions):
    alive={s:u for s,u in enumerate(units) if u is not None and u['energy']>0}
    stock=[r+int(u is not None and u['energy']==0) for r,u in zip(raw,units)]
    result={}
    for s,u in alive.items():
        x,y=s%16,s//16;d=directions[s]
        target=((x+1)%16+y*16,(x-1)%16+y*16,x+(y+1)%16*16,x+(y-1)%16*16)[d]
        energy_ok=u['energy']>=16;empty=target not in alive;raw_ok=stock[target]>=1
        reason='energy' if not energy_ok else 'occupied' if not empty else 'raw_material' if not raw_ok else 'candidate'
        result[s]=dict(target=target,direction=d,energy=u['energy'],energy_ok=energy_ok,target_empty=empty,target_raw=stock[target],raw_ok=raw_ok,reason=reason)
    counts=Counter(p['target'] for p in result.values() if p['reason']=='candidate')
    for p in result.values():
        p['candidate_count']=counts[p['target']]
        if p['reason']=='candidate':p['reason']='formed' if p['candidate_count']==1 else 'collision'
    return result

def verify_case(encoding,branch):
    sel=branch['selection'];arm=branch['ablation'];people=arm['final']['individuals'];selected=sel['offspring_ids']
    labels=label_history(people,selected)
    # Independently build full chains incrementally from earlier parent IDs.
    chains=[]
    for i,p in enumerate(people):chains.append([i]+(chains[p['parent']] if p['parent'] is not None else []))
    def identity(i,site):
        label=labels[i];ancestor=selected[LABELS.index(label)] if label!='other' else None
        return dict(site=site,identity=i,ancestor=ancestor,chain=chains[i],program=people[i]['program'])
    def occupancy(ids):
        out={a:{r:[] for r in REGIONS} for a in LABELS}
        for site,i in enumerate(ids):
            if i is not None:out[labels[i]][region(site)].append(identity(i,site))
        return out
    prior=arm['initial'];initial=occupancy(prior['site_ids']);rows=[]
    counts={a:{r:dict.fromkeys(REASONS,0) for r in REGIONS} for a in LABELS}
    arrivals={a:{r:dict(diagnostic_present=bool(initial[a][r]),first_future_tick=None) for r in ('upper','middle')} for a in LABELS}
    coexist=[]
    for tick,row in enumerate(arm['rows'],sel['t0']+1):
        same(row['tick'],tick,'future sequence');p=row['physical'];inter=p['interaction_units']
        gates=reconstruct_gates(inter,prior['raw'] if 'raw' in prior else prior['physical']['raw'],p['directions'])
        ids=prior['site_ids'];dissolved=[s for s,u in enumerate(inter) if u is not None and u['energy']==0]
        same(p['material']['dissolved'],dissolved,'dissolution sites')
        proposals=p['material']['proposals'];same([q['source'] for q in proposals],sorted(gates),'all preexisting survivors propose')
        events=[];deaths=[];expected_ids=ids.copy()
        for site in dissolved:expected_ids[site]=None
        for q in proposals:
            site=q['source'];g=gates[site];target=g['target'];i=ids[site];require(i is not None,'preexisting actor')
            same((q['target'],q['direction'],q['reason']),(target,g['direction'],g['reason']),'independent gate reason')
            info=identity(i,site);info.pop('site');label=labels[i]
            child=row['site_ids'][target] if g['reason']=='formed' else None
            if child is not None:
                same(people[child]['parent'],i,'formed child parent');same(people[child]['birth_tick'],tick,'formed child tick')
                require(child>=len(arm['initial']['individuals']) and child not in ids,'new child identity')
                expected_ids[target]=child
            events.append(dict(tick=tick,source=site,**info,lineage=label,**g,target_occupied=not g['target_empty'],target_dissolved=target in dissolved,candidate=g['energy_ok'] and g['target_empty'] and g['raw_ok'],child_id=child,target_region=region(target)))
            counts[label][region(target)][g['reason']]+=1
        for site in dissolved:
            i=ids[site];require(i is not None,'death identity');same(people[i]['death_tick'],tick,'natural death tick')
            deaths.append(dict(tick=tick,**identity(i,site),lineage=labels[i],region=region(site)))
        same(expected_ids,row['site_ids'],'independent end identities')
        same(sorted(row['deaths']),sorted(ids[s] for s in dissolved),'saved deaths')
        same(sorted(q['id'] for q in row['births']),sorted(e['child_id'] for e in events if e['child_id'] is not None),'saved births')
        for site,i in enumerate(row['site_ids']):
            if i is not None:same(p['units'][site]['program'],people[i]['program'],'history program')
        now=occupancy(row['site_ids'])
        for a in LABELS:
            for r in ('upper','middle'):
                if now[a][r] and arrivals[a][r]['first_future_tick'] is None:arrivals[a][r]['first_future_tick']=tick
        if now['left']['upper'] and now['right']['upper']:coexist.append(tick)
        rows.append(dict(tick=tick,events=events,deaths=deaths,occupancy=now));prior=row
    same(len(rows),sel['remaining_steps'],'complete future window')
    return dict(encoding=encoding,selection=sel,diagnostic=dict(tick=sel['t0'],occupancy=initial),rows=rows,arrivals=arrivals,counts=counts,upper_coexist_ticks=coexist)

def summarize(records):
    def group(chosen):
        counts={a:{r:dict.fromkeys(REASONS,0) for r in REGIONS} for a in LABELS}
        occupancy={a:dict.fromkeys(REGIONS,0) for a in LABELS};events=deaths=steps=0
        for c in chosen:
            for row in c['rows']:
                steps+=1;events+=len(row['events']);deaths+=len(row['deaths'])
                for q in row['events']:counts[q['lineage']][q['target_region']][q['reason']]+=1
                for a in LABELS:
                    for r in REGIONS:occupancy[a][r]+=len(row['occupancy'][a][r])
        return dict(cases=len(chosen),saved_steps=steps,events=events,deaths=deaths,counts=counts,upper_coexist_steps=sum(len(c['upper_coexist_ticks']) for c in chosen),occupancy_identity_steps=occupancy)
    return dict(overall=group(records),cells=[dict(encoding=e,**group([c for c in records if c['encoding']==e])) for e in ('east','west')])

def main():
    proof=OUTPUT/'independent-verification.json';require(not proof.exists(),'exclusive proof')
    start=monotonic();paths=[];result=dict(status='running',completed_cases=0,new_simulation_steps=0,review_mode='parent inline fallback independent algorithm');files={}
    def budget():require(monotonic()-start<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'verification budget')
    try:
        paths=input_paths();result['input_sha256'],result['input_read_errors_before']=capture(paths)
        bound=bindings();same(result['input_sha256'],bound,'validated source inventory')
        files={n:digest(OUTPUT/n) for n in ('metadata.json','records.json','summary.json')}
        meta=read(OUTPUT/'metadata.json')
        for key,val in dict(status='complete',planned_cases=8,completed_cases=8,saved_steps=116,diagnostic_states=8,new_simulation_steps=0,new_environment_sources=0,new_independent_initial_worlds=0,time_limit_seconds=600,storage_limit_bytes=134217728).items():same(meta[key],val,'producer '+key)
        same(meta['input_sha256'],bound,'producer source hashes');same(meta['input_sha256_after'],bound,'producer final source hashes')
        same(meta['output_sha256'],{n:files[n] for n in ('records.json','summary.json')},'producer output hashes')
        require(meta['elapsed_seconds']<600,'producer budget')
        census=read('docs/research/results/v4-study-039-design-census.json')['cases']
        wanted=[c for c in census if c['encoding'] in ('east','west') and c['trigger']]
        same(len(wanted),8,'full fixed cohort');records=[]
        policy=read('data/v4-study-039/records.json')
        for c in wanted:
            budget();b=read(f"data/v4-study-039/cases/{c['encoding']}-{c['seed']}.json")
            r=next(r for r in policy if (r['encoding'],r['seed'])==(c['encoding'],c['seed']))
            same(b['selection'],r['selection'],'source exact selection');same(b['ablation']['metrics'],r['ablation_future_metrics'],'source exact metrics')
            records.append(verify_case(c['encoding'],b));result['completed_cases']+=1
        same(sum(len(r['rows']) for r in records),116,'full future denominator')
        same(read(OUTPUT/'records.json'),records,'complete independent events and occupancy')
        same(read(OUTPUT/'summary.json'),summarize(records),'all counts and zero cells')
        same(bindings(),bound,'unchanged inputs');same({n:digest(OUTPUT/n) for n in files},files,'unchanged outputs')
        result.update(status='verified',saved_steps=116,files_sha256=files)
    except BaseException as exc:
        result.update(status='failed',error=repr(exc));raise
    finally:
        result['input_sha256_after'],result['input_read_errors_after']=capture(paths)
        result['elapsed_seconds']=monotonic()-start
        try:
            if result['status']=='verified':
                same(result['input_sha256_after'],result['input_sha256'],'final sources');same(result['input_read_errors_after'],{},'final source errors')
                budget();require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())+len(json.dumps(result,indent=2).encode())<134217728,'proof budget')
        except BaseException as exc:
            result.update(status='failed',error=repr(exc));save(proof,result);raise
        save(proof,result)
if __name__=='__main__':main()
