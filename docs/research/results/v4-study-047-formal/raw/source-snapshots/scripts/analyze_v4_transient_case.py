"""Post hoc saved-trace family accounting, without new physical simulation."""
import json
import subprocess
import time
from pathlib import Path

OUTPUT=Path('data/v4-study-016-transient')
SECONDS=600
STORAGE=50*1024**2
FLOWS=('accepted_input','leakage','bond_cost','inflow','outflow','formation_cost','energy_to_child')


def require(condition,message):
    if not condition:raise ValueError(message)


def nonnegative(value):
    require(type(value) is int and value>=0,'nonnegative integer required')
    return value


def population_state(groups,family,original):
    flat=[i for g in groups for i in g]
    require(all(g for g in groups) and len(flat)==len(set(flat)),'complete disjoint nonempty phase groups')
    living=set(flat)&family;targets=[set(g) for g in groups if set(g)&living]
    outsiders=sum(len(g-living) for g in targets)
    state='extinct' if not living else 'fragmented' if len(targets)>1 else 'mixed' if outsiders else 'closed_singleton' if len(living)==1 else 'closed_multi'
    return dict(state=state,population=len(living),original_survivors=len(living&original),destination_components=len(targets),outsiders=outsiders)


def analyze(initial,rows,final,parameters,anchor_members=(8,9)):
    """Use saved event ledgers to track the same identities across each phase."""
    bond_price=nonnegative(parameters['bond_cost'])
    formation_price=nonnegative(parameters['construction_cost'])+nonnegative(parameters['copy_cost'])
    parents=final['parents'];death_ticks=final['death_ticks'];ids=list(initial['site_ids']);units=initial['units']
    require(len(parents)==len(death_ticks),'parent and death coverage')
    require(len(ids)==len(units) and len({i for i in ids if i is not None})==sum(i is not None for i in ids),'initial identity coverage')
    founders={i for i in ids if i is not None};original=set(anchor_members)
    require(len(original)==len(anchor_members) and original<=founders,'initial family identities')
    roots=[]
    for i,parent in enumerate(parents):
        require(parent is None or type(parent) is int and 0<=parent<i,'ordered parent chain')
        roots.append(i if i in founders else None if parent is None else roots[parent])
    family={i for i,root in enumerate(roots) if root in original}
    biographies={i:dict(identity=i,parent=parents[i],founder=roots[i],site=site,born_tick=0,died_tick=None,original=True) for site,i in enumerate(ids) if i in original}
    seen=set(founders);steps=[]
    for tick,row in enumerate(rows,1):
        require(type(row['tick']) is int and row['tick']==tick and tick<=400,'complete ordered relative steps')
        physical=row['physical'];intermediate=physical['interaction_units'];after=physical['units'];next_ids=row['site_ids'];driven=physical['driven'];material=physical['material']
        require(len(ids)==len(units)==len(intermediate)==len(after)==len(next_ids),'phase site coverage')
        for site,i in enumerate(ids):
            require((i is None)==(units[site] is None)==(intermediate[site] is None),'interaction preserves initial population')
        inputs={p['site']:p for p in driven['inputs']}
        require(len(inputs)==len(driven['inputs'])==len(ids) and set(inputs)==set(range(len(ids))),'input site coverage')
        members={}
        for site,i in enumerate(ids):
            if i not in family:continue
            members[i]=dict(identity=i,site=site,energy_before=nonnegative(units[site]['energy']),accepted_input=nonnegative(inputs[site]['accepted']),leakage=nonnegative(inputs[site]['leakage']),bond_cost=0,inflow=0,outflow=0,interaction_energy=nonnegative(intermediate[site]['energy']),formation_cost=0,energy_to_child=0,energy_after=0,status='alive')
        for edge in driven['interaction']['bonds']:
            require(len(edge)==2 and len(set(edge))==2,'distinct bond endpoints')
            for site in edge:
                require(type(site) is int and 0<=site<len(ids) and ids[site] is not None,'occupied bond endpoint')
                if ids[site] in members:members[ids[site]]['bond_cost']+=bond_price
        internal=0
        for transfer in driven['interaction']['transfers']:
            a,b=transfer['donor'],transfer['recipient'];amount=nonnegative(transfer['amount'])
            require(type(a) is int and type(b) is int and 0<=a<len(ids) and 0<=b<len(ids) and a!=b and ids[a] is not None and ids[b] is not None,'occupied transfer endpoints')
            if ids[a] in members:members[ids[a]]['outflow']+=amount
            if ids[b] in members:members[ids[b]]['inflow']+=amount
            if ids[a] in members and ids[b] in members:internal+=amount
        event_ids=list(ids);deaths=[];births=[]
        dissolved=material['dissolved'];require(len(dissolved)==len(set(dissolved)),'unique dissolved sites')
        require(set(dissolved)=={site for site,u in enumerate(intermediate) if u is not None and u['energy']==0},'dissolution corresponds to exhausted identities')
        for site in dissolved:
            require(type(site) is int and 0<=site<len(ids) and event_ids[site] is not None,'occupied death site')
            dead=event_ids[site];event_ids[site]=None
            require(death_ticks[dead]==tick,'saved death tick')
            if dead in members:
                deaths.append(dead);biographies[dead]['died_tick']=tick;members[dead]['status']='dead'
        actors=set()
        for proposal in material['proposals']:
            if proposal['reason']!='formed':continue
            actor,target=proposal['source'],proposal['target']
            require(type(actor) is int and type(target) is int and 0<=actor<len(ids) and 0<=target<len(ids),'formation site bounds')
            parent=ids[actor];child=next_ids[target]
            require(actor not in actors and parent is not None and event_ids[actor]==parent and event_ids[target] is None,'formation needs surviving pre-step parent and empty target')
            require(type(child) is int and 0<=child<len(parents) and child not in seen and parents[child]==parent,'new child with observed old parent')
            actors.add(actor);seen.add(child);event_ids[target]=child
            cost=nonnegative(proposal['cost']);child_energy=nonnegative(proposal['child_energy']);parent_energy=nonnegative(proposal['parent_energy'])
            require(cost==formation_price and intermediate[actor]['energy']==cost+child_energy+parent_energy,'formation energy allocation and configured costs')
            require(after[actor] is not None and after[target] is not None and after[actor]['energy']==parent_energy and after[target]['energy']==child_energy,'saved formation endpoint energy')
            if parent in members:
                members[parent]['formation_cost']+=cost;members[parent]['energy_to_child']+=child_energy
                require(child in family,'child founder agrees with parent')
                births.append(dict(identity=child,parent=parent,founder=roots[child],site=target,energy=child_energy))
                biographies[child]=dict(identity=child,parent=parent,founder=roots[child],site=target,born_tick=tick,died_tick=None,original=False)
            else:require(child not in family,'foreign birth must remain foreign')
        require(event_ids==next_ids,'event identity ledger matches saved final identities')
        require(len({i for i in next_ids if i is not None})==sum(i is not None for i in next_ids),'unique final living identities')
        for site,i in enumerate(next_ids):require((i is None)==(after[site] is None),'final occupancy matches identity')
        for i,member in members.items():
            if member['status']=='alive':
                require(next_ids[member['site']]==i,'surviving identity does not move')
                member['energy_after']=nonnegative(after[member['site']]['energy'])
            require(member['interaction_energy']==member['energy_before']+member['accepted_input']-member['leakage']-member['bond_cost']+member['inflow']-member['outflow'],'per-identity interaction energy conservation')
            require(member['energy_after']==member['interaction_energy']-member['formation_cost']-member['energy_to_child'],'per-identity formation energy conservation')
        ledger=dict(population_before=len(members),population_after=sum(i in family for i in next_ids),births=len(births),deaths=len(deaths),energy_before=sum(m['energy_before'] for m in members.values()),**{k:sum(m[k] for m in members.values()) for k in FLOWS},internal_transfer=internal,birth_energy=sum(b['energy'] for b in births),energy_after=sum(after[site]['energy'] for site,i in enumerate(next_ids) if i in family))
        require(ledger['population_after']==ledger['population_before']+ledger['births']-ledger['deaths'],'family population conservation')
        require(ledger['energy_to_child']==ledger['birth_energy'],'parent child allocation cancels within family')
        require(ledger['energy_after']==ledger['energy_before']+ledger['accepted_input']-ledger['leakage']-ledger['bond_cost']+ledger['inflow']-ledger['outflow']-ledger['formation_cost'],'family energy conservation')
        interaction_sites=physical['interaction_components']
        require(sorted(site for g in interaction_sites for site in g)==[site for site,i in enumerate(ids) if i is not None],'complete interaction phase grouping')
        interaction_groups=[[ids[site] for site in g] for g in interaction_sites]
        final_groups=row['observation']['components']['material']
        require(sorted(i for g in final_groups for i in g)==sorted(i for i in next_ids if i is not None),'complete final material grouping')
        interaction=population_state(interaction_groups,family,original);material_final=population_state(final_groups,family,original)
        require(interaction['population']==ledger['population_before'] and material_final['population']==ledger['population_after'],'phase population consistency')
        steps.append(dict(tick=tick,members=[members[i] for i in sorted(members)],births=sorted(births,key=lambda b:b['identity']),deaths=sorted(deaths),ledger=ledger,interaction=interaction,material_final=material_final))
        ids=list(next_ids);units=after
    require(ids==final['site_ids'] and units==final['units'],'saved final endpoint')
    require(set(biographies)==family,'all family births accounted for by observed events')
    for i,bio in biographies.items():require(bio['died_tick']==death_ticks[i],'complete family lifespan matches saved death ledger')
    return [biographies[i] for i in sorted(biographies)],steps


def summarize(branches):
    require(len(branches)==2 and [b['exchange'] for b in branches]==[True,False] and all(type(b['exchange']) is bool for b in branches),'fixed ordered paired switches')
    summaries=[]
    totals=('accepted_input','leakage','bond_cost','inflow','outflow','internal_transfer','formation_cost')
    for b in branches:
        require(b['history'] is False and type(b['seed']) is int and b['seed']==112000 and type(b['mutation']) is int and b['mutation']==0 and type(b['component']) is int and b['component']==7 and b['anchor_members']==[8,9],'fixed case identity')
        steps=b['steps'];require(len(steps)==400 and all(type(s['tick']) is int and s['tick']==t for t,s in enumerate(steps,1)),'complete four hundred step case')
        summaries.append(dict(exchange=b['exchange'],births=sum(s['ledger']['births'] for s in steps),deaths=sum(s['ledger']['deaths'] for s in steps),extinction_tick=next((s['tick'] for s in steps if s['ledger']['population_after']==0),None),final_population=steps[-1]['ledger']['population_after'],initial_energy=steps[0]['ledger']['energy_before'],final_energy=steps[-1]['ledger']['energy_after'],**{k:sum(s['ledger'][k] for s in steps) for k in totals},original_biographies=[v for v in b['biographies'] if v['original']],selected_steps=[s for s in steps if s['tick'] in (20,21,22)]))
    return summaries


def save(path,value):path.write_text(json.dumps(value,separators=(',',':'))+'\n')


def main():
    from scripts.transient_case_inputs import bindings,cases,read,digest
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch required')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();branches=[]
    meta=dict(status='running',planned_branches=2,completed_branches=0,new_simulation_steps=0,new_independent_sources=0,reused_independent_sources=1,time_limit_seconds=SECONDS,storage_limit_bytes=STORAGE)
    save(OUTPUT/'metadata.json',meta);save(OUTPUT/'branches.json',branches)
    def budget():
        require(time.monotonic()-started<SECONDS,'time budget exceeded')
        require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<STORAGE,'storage budget exceeded')
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();meta['input_sha256']=bindings();save(OUTPUT/'metadata.json',meta)
        inputs=cases();require(len(inputs)==2 and [x['exchange'] for x in inputs]==[True,False] and all(type(x['exchange']) is bool for x in inputs),'fixed paired input grid')
        for case in inputs:
            budget();require(bindings()==meta['input_sha256'],'bound inputs changed during run')
            directory=Path(case['directory']);parameters=read(Path(case['source'])/'metadata.json')
            rows=[json.loads(line) for line in (directory/'steps.jsonl').read_text().splitlines()];require(len(rows)==400,'full case horizon')
            initial=read(directory/'initial.json')
            require(initial['observation']['components']['material'][7]==[8,9],'fixed initial component seven')
            biographies,steps=analyze(initial,rows,read(directory/'final.json'),parameters)
            branches.append(dict(history=False,seed=112000,mutation=0,exchange=case['exchange'],component=7,anchor_members=[8,9],biographies=biographies,steps=steps))
            meta['completed_branches']=len(branches);save(OUTPUT/'branches.json',branches);save(OUTPUT/'metadata.json',meta)
            print(f'{len(branches)}/2 saved transient case branches',flush=True)
        save(OUTPUT/'summary.json',summarize(branches));budget();meta['input_sha256_after']=bindings()
        require(meta['input_sha256']==meta['input_sha256_after'],'bound inputs changed')
        meta.update(status='complete',output_sha256={n:digest(OUTPUT/n) for n in ('branches.json','summary.json')})
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
        if meta['status']=='complete' and (meta['elapsed_seconds']>=SECONDS or sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())>=STORAGE):
            meta.update(status='failed',error='budget exceeded at finalization')
        meta['output_sha256']={p.name:digest(p) for p in OUTPUT.iterdir() if p.name!='metadata.json' and p.is_file()}
        save(OUTPUT/'metadata.json',meta)
        if meta['status']=='failed' and 'binding_error' in meta:raise ValueError(meta['binding_error'])
        if meta.get('error') in ('bound inputs changed at finalization','budget exceeded at finalization'):raise ValueError(meta['error'])


if __name__=='__main__':main()
