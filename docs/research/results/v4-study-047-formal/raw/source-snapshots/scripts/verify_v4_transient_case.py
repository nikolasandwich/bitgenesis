"""Independent identity-difference and raw-flow ledger for the frozen transient pair."""
from pathlib import Path
import json
from scripts.transient_case_inputs import read,digest,bindings,cases,validate_cases

def state(groups,owned,original):
    flat=[i for g in groups for i in g];assert len(flat)==len(set(flat))
    alive=set(flat)&owned;targets=[set(g) for g in groups if set(g)&alive]
    outside=sum(len(g-alive) for g in targets)
    label='extinct' if not alive else 'fragmented' if len(targets)>1 else 'mixed' if outside else 'closed_singleton' if len(alive)==1 else 'closed_multi'
    return dict(state=label,population=len(alive),original_survivors=len(alive&original),destination_components=len(targets),outsiders=outside)

def bond_groups(ids,bonds):
    neighbours={i:set() for i,v in enumerate(ids) if v is not None}
    for a,b in bonds:
        assert a in neighbours and b in neighbours and a!=b
        neighbours[a].add(b);neighbours[b].add(a)
    groups=[];remaining=set(neighbours)
    while remaining:
        pending=[min(remaining)];group=set()
        while pending:
            i=pending.pop()
            if i in group:continue
            group.add(i);pending.extend(neighbours[i]-group)
        remaining-=group;groups.append(sorted(group))
    return groups

def reconstruct(initial,rows,final,parameters,anchor_members=(8,9)):
    original=set(anchor_members);parents=final['parents'];founder={}
    assert len(parents)==len(final['death_ticks'])
    for i,p in enumerate(parents):
        assert p is None or type(p) is int and 0<=p<i
        if i in original:founder[i]=i
        elif p in founder:founder[i]=founder[p]
    owned=set(founder);prior_ids=initial['site_ids'];prior_units=initial['units']
    assert original<={v for v in prior_ids if v is not None}
    assert {v for v in prior_ids if v is not None}&owned==original
    biographies={i:dict(identity=i,parent=parents[i],founder=i,site=prior_ids.index(i),born_tick=0,died_tick=None,original=True) for i in sorted(original)}
    seen=set(original);dead=set();steps=[]
    for tick,row in enumerate(rows,1):
        assert type(row['tick']) is int and row['tick']==tick
        physical=row['physical'];current_ids=row['site_ids'];current_units=physical['units']
        assert len(prior_ids)==len(current_ids)==len(prior_units)==len(current_units)
        for ids,units in ((prior_ids,prior_units),(current_ids,current_units)):
            nonnull=[v for v in ids if v is not None];assert len(nonnull)==len(set(nonnull))
            assert all((i is None)==(u is None) for i,u in zip(ids,units))
        before={i:site for site,i in enumerate(prior_ids) if i is not None};after={i:site for site,i in enumerate(current_ids) if i is not None}
        old=set(before)&owned;now=set(after)&owned;born=now-old;lost=old-now
        assert not born&seen and not now&dead
        for i in old&now:assert before[i]==after[i]
        inputs=physical['driven']['inputs'];assert len(inputs)==len(prior_ids)
        supplied={x['site']:x for x in inputs};assert set(supplied)==set(range(len(prior_ids)))
        interactions=physical['driven']['interaction'];bonds=interactions['bonds'];transfers=interactions['transfers']
        groups=bond_groups(prior_ids,bonds)
        assert {tuple(g) for g in groups}=={tuple(sorted(g)) for g in physical['interaction_components']}
        material_groups=row['observation']['components']['material']
        assert {i for g in material_groups for i in g}==set(after)
        matches={};births=[]
        for proposal in physical['material']['proposals']:
            if proposal['reason']!='formed':continue
            source,target=proposal['source'],proposal['target'];parent=prior_ids[source];child=current_ids[target]
            assert parent is not None and child is not None and child not in before and parents[child]==parent
            assert proposal['cost']==parameters['construction_cost']+parameters['copy_cost']
            assert current_units[target]['energy']==proposal['child_energy'] and current_units[source]['energy']==proposal['parent_energy']
            if parent in owned:
                assert child in born and parent not in matches
                matches[parent]=proposal
                births.append(dict(identity=child,parent=parent,founder=founder[child],site=target,energy=current_units[target]['energy']))
        births.sort(key=lambda x:x['identity']);assert {b['identity'] for b in births}==born
        dissolved=set(physical['material']['dissolved']);assert {prior_ids[s] for s in dissolved if prior_ids[s] in owned}==lost
        members=[]
        for i in sorted(old):
            site=before[i];u=prior_units[site];supply=supplied[site]
            bcost=sum(site in edge for edge in bonds)*parameters['bond_cost']
            inflow=sum(t['amount'] for t in transfers if t['recipient']==site);outflow=sum(t['amount'] for t in transfers if t['donor']==site)
            energy=u['energy']+supply['accepted']-supply['leakage']-bcost+inflow-outflow
            assert energy==physical['interaction_units'][site]['energy'] and energy>=0
            proposal=matches.get(i);cost=proposal['cost'] if proposal else 0;child_energy=proposal['child_energy'] if proposal else 0
            endpoint=current_units[after[i]]['energy'] if i in now else 0
            assert endpoint==energy-cost-child_energy
            assert (i in lost)==(energy==0)
            members.append(dict(identity=i,site=site,energy_before=u['energy'],accepted_input=supply['accepted'],leakage=supply['leakage'],bond_cost=bcost,inflow=inflow,outflow=outflow,interaction_energy=energy,formation_cost=cost,energy_to_child=child_energy,energy_after=endpoint,status='dead' if i in lost else 'alive'))
        for b in births:
            i=b['identity'];biographies[i]=dict(identity=i,parent=b['parent'],founder=b['founder'],site=b['site'],born_tick=tick,died_tick=None,original=False)
        for i in lost:biographies[i]['died_tick']=tick
        seen|=born;dead|=lost
        keys=('energy_before','accepted_input','leakage','bond_cost','inflow','outflow','formation_cost','energy_to_child')
        ledger={k:sum(m[k] for m in members) for k in keys}
        ledger.update(population_before=len(old),population_after=len(now),births=len(born),deaths=len(lost),
                      internal_transfer=sum(t['amount'] for t in transfers if prior_ids[t['donor']] in owned and prior_ids[t['recipient']] in owned),
                      birth_energy=sum(b['energy'] for b in births),energy_after=sum(current_units[after[i]]['energy'] for i in now))
        assert ledger['population_after']==ledger['population_before']+ledger['births']-ledger['deaths']
        assert ledger['birth_energy']==ledger['energy_to_child']
        assert ledger['energy_after']==ledger['energy_before']+ledger['accepted_input']-ledger['leakage']-ledger['bond_cost']+ledger['inflow']-ledger['outflow']-ledger['formation_cost']
        assert ledger['energy_after']==sum(m['energy_after'] for m in members)+ledger['birth_energy']
        interaction=state([[prior_ids[site] for site in g] for g in groups],owned,original)
        final_state=state(material_groups,owned,original)
        steps.append(dict(tick=tick,members=members,births=births,deaths=sorted(lost),ledger=ledger,interaction=interaction,material_final=final_state))
        prior_ids=current_ids;prior_units=current_units
    assert prior_ids==final['site_ids'] and prior_units==final['units']
    assert set(biographies)==owned
    for i,b in biographies.items():assert b['died_tick']==final['death_ticks'][i]
    return [biographies[i] for i in sorted(biographies)],steps

def summary(branches):
    assert len(branches)==2 and [type(b['exchange']) for b in branches]==[bool,bool] and [b['exchange'] for b in branches]==[True,False]
    results=[]
    for b in branches:
        rows=b['steps'];assert len(rows)==400 and [r['tick'] for r in rows]==list(range(1,401))
        results.append(dict(exchange=b['exchange'],births=sum(r['ledger']['births'] for r in rows),deaths=sum(r['ledger']['deaths'] for r in rows),
            extinction_tick=next((r['tick'] for r in rows if r['ledger']['population_after']==0),None),final_population=rows[-1]['ledger']['population_after'],
            initial_energy=rows[0]['ledger']['energy_before'],final_energy=rows[-1]['ledger']['energy_after'],
            **{k:sum(r['ledger'][k] for r in rows) for k in ('accepted_input','leakage','bond_cost','inflow','outflow','internal_transfer','formation_cost')},
            original_biographies=[x for x in b['biographies'] if x['original']],selected_steps=[rows[t-1] for t in (20,21,22)]))
    return results

def main():
    root=Path('data/v4-study-016-transient');names=('metadata.json','branches.json','summary.json');before={n:digest(root/n) for n in names}
    meta=read(root/'metadata.json');assert meta['status']=='complete' and meta['planned_branches']==meta['completed_branches']==2
    assert meta['new_simulation_steps']==meta['new_independent_sources']==0 and meta['reused_independent_sources']==1
    assert meta['time_limit_seconds']==600 and meta['storage_limit_bytes']==50*1024**2 and meta['elapsed_seconds']<600
    assert sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<50*1024**2
    assert meta['input_sha256']==meta['input_sha256_after']==bindings()
    assert meta['output_sha256']=={n:digest(root/n) for n in names[1:]}
    selected=cases();validate_cases(selected);branches=[]
    for c in selected:
        p=Path(c['directory']);rows=[json.loads(line) for line in (p/'steps.jsonl').read_text().splitlines()];assert len(rows)==400
        bios,steps=reconstruct(read(p/'initial.json'),rows,read(p/'final.json'),read(Path(c['source'])/'metadata.json'))
        branches.append(dict(history=False,seed=112000,mutation=0,exchange=c['exchange'],component=7,anchor_members=[8,9],biographies=bios,steps=steps))
    assert branches==read(root/'branches.json') and summary(branches)==read(root/'summary.json')
    assert meta['input_sha256']==bindings() and before=={n:digest(root/n) for n in names}
    proof=dict(status='verified',branches=2,saved_steps=800,member_step_records=sum(len(r['members']) for b in branches for r in b['steps']),new_simulation_steps=0,new_independent_sources=0,reused_independent_sources=1,input_files=len(meta['input_sha256']),files_sha256=before,verifier_sha256=digest(Path(__file__)),scope='independent live-identity differences, raw transfer and bond reconstruction, all member and family energy equations, births/deaths and stage-specific partitions; posthoc single paired case')
    with (root/'independent-verification.json').open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))

if __name__=='__main__':
    try:main()
    except BaseException as error:
        root=Path('data/v4-study-016-transient')
        if root.is_dir() and not (root/'verification-failure.json').exists():
            with (root/'verification-failure.json').open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise
