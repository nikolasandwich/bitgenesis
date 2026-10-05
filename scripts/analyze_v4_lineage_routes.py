"""Study041: ancestry backtracking and saved proposal gates; no world execution."""
from copy import deepcopy
from pathlib import Path
from time import monotonic
import subprocess

OUTPUT=Path('data/v4-study-041')
REGIONS=('upper','middle','lower','other')
LINEAGES=('left','right','other')
REASONS=('energy','occupied','raw_material','collision','formed')


def require(value,message):
    if not value:raise ValueError(message)


def region(site):
    return 'upper' if site in (85,86) else 'middle' if site in (101,102) else 'lower' if site in (117,118) else 'other'


def empty_counts():
    return {a:{r:dict.fromkeys(REASONS,0) for r in REGIONS} for a in LINEAGES}


def analyze_case(encoding,branch):
    require(encoding in ('east','west'),'encoding')
    selection=deepcopy(branch['selection']);arm=branch['ablation'];initial=arm['initial'];parents=arm['final']['parents']
    t0=selection['t0'];require(initial['tick']==t0,'diagnostic tick')
    if 'parents' in initial:require(parents[:len(initial['parents'])]==initial['parents'],'historical parent prefix')
    require(set(selection['offspring_sites'])=={117,118} and len(selection['offspring_ids'])==2,'selected sites')
    selected={i:('left' if s==117 else 'right') for s,i in zip(selection['offspring_sites'],selection['offspring_ids'])}
    require(len(selected)==2,'distinct selected identities')
    for i,parent in enumerate(parents):require(parent is None or type(parent) is int and 0<=parent<i,'ordered parents')
    if 'individuals' in arm['final']:require([p['parent'] for p in arm['final']['individuals']]==parents,'parent table agreement')
    def ancestry(identity):
        require(type(identity) is int and 0<=identity<len(parents),'identity bounds')
        chain=[];node=identity;ancestor=None
        while node is not None:
            chain.append(node)
            if node in selected and ancestor is None:ancestor=node
            node=parents[node]
        return dict(lineage=selected.get(ancestor,'other'),ancestor=ancestor,chain=chain)
    def occupancy(ids,units):
        require(len(ids)==len(units)==256,'world coverage')
        result={a:{r:[] for r in REGIONS} for a in LINEAGES};seen=set()
        for site,(i,u) in enumerate(zip(ids,units)):
            require((i is None)==(u is None),'occupancy identity')
            if i is None:continue
            require(i not in seen,'unique live identity');seen.add(i);a=ancestry(i)
            result[a.pop('lineage')][region(site)].append(dict(site=site,identity=i,program=list(u['program']),**a))
        return result
    diagnostic=dict(tick=t0,occupancy=occupancy(initial['site_ids'],initial['units']))
    before=initial;rows=[];counts=empty_counts();seen={i for i in initial['site_ids'] if i is not None}
    for tick,saved in enumerate(arm['rows'],t0+1):
        require(type(saved['tick']) is int and saved['tick']==tick,'strict future ticks')
        p=saved['physical'];units=p['interaction_units'];ids=before['site_ids'];raw=before['raw']
        require(len(units)==len(ids)==len(raw)==len(p['directions'])==256,'saved stage coverage')
        require([u is not None for u in units]==[i is not None for i in ids],'pre-state actor coverage')
        dead=[s for s,u in enumerate(units) if u is not None and u['energy']==0]
        require(p['material']['dissolved']==dead,'saved dissolution')
        occupied=[u is not None and u['energy']>0 for u in units];resources=[v+int(s in dead) for s,v in enumerate(raw)]
        targets={};candidates={};gates={}
        for s,u in enumerate(units):
            if u is None or s in dead:continue
            require(type(u['energy']) is int and u['energy']>0,'positive actor energy')
            require(u['program']==before['units'][s]['program'],'actor program continuity')
            d=p['directions'][s];require(type(d) is int and d in range(4),'direction')
            x,y=s%16,s//16;target=(y*16+(x+1)%16,y*16+(x-1)%16,((y+1)%16)*16+x,((y-1)%16)*16+x)[d]
            targets[s]=target;gates[s]=(u['energy']>=16,not occupied[target],resources[target]>=1)
            if all(gates[s]):candidates.setdefault(target,[]).append(s)
        proposals=p['material']['proposals']
        require(len(proposals)==len(targets) and {q['source'] for q in proposals}==set(targets),'all surviving actors propose exactly once')
        expected_ids=ids[:];deaths=[]
        for s in dead:
            a=ancestry(ids[s]);deaths.append(dict(tick=tick,site=s,identity=ids[s],program=list(units[s]['program']),region=region(s),**a));expected_ids[s]=None
        events=[]
        for q in proposals:
            s=q['source'];target=targets[s];energy_ok,empty,raw_ok=gates[s];n=len(candidates.get(target,[]))
            reason='energy' if not energy_ok else 'occupied' if not empty else 'raw_material' if not raw_ok else 'collision' if n>1 else 'formed'
            require(q['target']==target and q['direction']==p['directions'][s] and q['reason']==reason,'saved proposal target/direction/reason')
            child=None
            if reason=='formed':
                child=saved['site_ids'][target]
                require(type(child) is int and 0<=child<len(parents) and child not in seen and parents[child]==ids[s],'formed child identity')
                if 'parents' in initial:require(child>=len(initial['parents']),'new identity after diagnostic history')
                expected_ids[target]=child;seen.add(child)
            a=ancestry(ids[s]);events.append(dict(tick=tick,source=s,target=target,direction=q['direction'],identity=ids[s],program=list(units[s]['program']),energy=units[s]['energy'],target_region=region(target),target_raw=resources[target],target_occupied=occupied[target],target_dissolved=target in dead,energy_ok=energy_ok,target_empty=empty,raw_ok=raw_ok,candidate=all(gates[s]),candidate_count=n,reason=reason,child_id=child,**a))
            counts[a['lineage']][region(target)][reason]+=1
        require(expected_ids==saved['site_ids'],'saved end identity reconstruction')
        require(sorted(saved['deaths'])==sorted(ids[s] for s in dead),'saved death IDs')
        require(sorted(v['id'] for v in saved['births'])==sorted(e['child_id'] for e in events if e['child_id'] is not None),'saved birth IDs')
        rows.append(dict(tick=tick,events=events,deaths=deaths,occupancy=occupancy(saved['site_ids'],p['units'])))
        before=dict(site_ids=saved['site_ids'],units=p['units'],raw=p['raw'])
    require(len(rows)==selection['remaining_steps'],'full saved future window')
    require(before['site_ids']==arm['final']['site_ids'],'final identities')
    arrivals={a:{r:dict(diagnostic_present=bool(diagnostic['occupancy'][a][r]),first_future_tick=next((v['tick'] for v in rows if v['occupancy'][a][r]),None)) for r in ('upper','middle')} for a in LINEAGES}
    return dict(encoding=encoding,selection=selection,diagnostic=diagnostic,rows=rows,arrivals=arrivals,counts=counts,upper_coexist_ticks=[v['tick'] for v in rows if v['occupancy']['left']['upper'] and v['occupancy']['right']['upper']])


def summarize(records):
    def group(chosen):
        rows=[v for c in chosen for v in c['rows']]
        counts=empty_counts()
        for v in rows:
            for e in v['events']:counts[e['lineage']][e['target_region']][e['reason']]+=1
        return dict(cases=len(chosen),saved_steps=len(rows),events=sum(len(v['events']) for v in rows),deaths=sum(len(v['deaths']) for v in rows),counts=counts,upper_coexist_steps=sum(len(c['upper_coexist_ticks']) for c in chosen),occupancy_identity_steps={a:{r:sum(len(v['occupancy'][a][r]) for v in rows) for r in REGIONS} for a in LINEAGES})
    return dict(overall=group(records),cells=[dict(encoding=e,**group([c for c in records if c['encoding']==e])) for e in ('east','west')])


def main():
    from scripts.lineage_route_inputs import bindings,sources,read,save,digest,input_paths,capture
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);start=monotonic();records=[];paths=[]
    meta=dict(status='running',planned_cases=8,completed_cases=0,saved_steps=0,diagnostic_states=0,new_simulation_steps=0,new_environment_sources=0,new_independent_initial_worlds=0,time_limit_seconds=600,storage_limit_bytes=134217728)
    def budget():require(monotonic()-start<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'bounded audit')
    def hashes():return {p.name:digest(p) for p in sorted(OUTPUT.glob('*.json')) if p.name!='metadata.json'}
    try:
        save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta)
        paths=input_paths();meta['input_paths']=paths
        meta['input_sha256'],meta['input_read_errors_before']=capture(paths)
        save(OUTPUT/'metadata.json',meta)
        require(bindings()==meta['input_sha256'] and not meta['input_read_errors_before'],'validated initial bindings')
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        for enc,path,_ in sources():
            budget();record=analyze_case(enc,read(path));records.append(record)
            meta.update(completed_cases=len(records),saved_steps=sum(len(r['rows']) for r in records),diagnostic_states=len(records))
            save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta);budget()
        require(meta['completed_cases']==8 and meta['saved_steps']==116,'complete fixed cohort')
        save(OUTPUT/'summary.json',summarize(records));require(bindings()==meta['input_sha256'],'unchanged inputs')
        budget();meta['status']='complete'
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc));raise
    finally:
        try:
            meta['input_sha256_after'],meta['input_read_errors_after']=capture(paths)
            meta['output_sha256']=hashes();meta['elapsed_seconds']=monotonic()-start
            if meta['status']=='complete':
                require(meta['input_sha256_after']==meta['input_sha256'] and not meta['input_read_errors_after'],'final input binding')
                budget()
            save(OUTPUT/'metadata.json',meta)
            if meta['status']=='complete':budget()
        except BaseException as exc:
            meta.update(status='failed',finalization_error=repr(exc),elapsed_seconds=monotonic()-start)
            save(OUTPUT/'metadata.json',meta);raise


if __name__=='__main__':main()
