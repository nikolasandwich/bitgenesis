"""Study042 independent snapshot energy accounting; no producer or physics calls."""
from pathlib import Path
from time import monotonic
import json
from scripts.middle_energy_inputs import bindings,input_paths,capture,read,save,digest
OUTPUT=Path('data/v4-study-042')
LABELS=('left','right','other')
REGIONS=('upper','middle','lower','other')
REASONS=('energy','occupied','raw_material','collision','formed')

def require(ok,message):
    if not ok:raise ValueError(message)

def same(a,b,message):require(json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True),message)

def region(s):return 'upper' if s in (85,86) else 'middle' if s in (101,102) else 'lower' if s in (117,118) else 'other'

def eligible_intervals(pairs):
    intervals=[]
    for tick,energy in pairs:
        if energy>=16:
            if intervals and intervals[-1][1]==tick-1:intervals[-1][1]=tick
            else:intervals.append([tick,tick])
    return intervals

def energy_stage(units,proposed):
    supplied=[];inputs=[]
    for site,u in enumerate(units):
        accepted=0 if u is None else min(proposed[site],64-u['energy'])
        leakage=0 if u is None else min(1,u['energy']+accepted)
        inputs.append(dict(site=site,proposed=proposed[site],accepted=accepted,rejected=proposed[site]-accepted,leakage=leakage))
        supplied.append(None if u is None else u['energy']+accepted-leakage)
    neighbors={i:[] for i,u in enumerate(units) if u is not None}
    edges=[]
    for s in neighbors:
        for t in ((s//16)*16+(s%16+1)%16,((s//16+1)%16)*16+s%16):
            if t in neighbors and units[s]['material']==units[t]['material']:
                edges.append([s,t]);neighbors[s].append(t);neighbors[t].append(s)
    bonds=[edge for edge in edges if all(supplied[i]>=len(neighbors[i]) for i in edge)]
    energies=supplied.copy()
    for s,t in bonds:energies[s]-=1;energies[t]-=1
    return energies,bonds,inputs

def identity_window(rows,alive):
    actions=[r for r in rows if r['phase']=='action'];eligible=[r['tick'] for r in actions if r['preformation_energy']>=16]
    spans=eligible_intervals([(r['tick'],r['preformation_energy']) for r in actions])
    require(eligible==[r['tick'] for r in actions[:len(eligible)]],'monotone prefix')
    north=[r for r in actions if r['direction']==3];proposals=[r for r in north if not r['died']]
    successes=[r['tick'] for r in actions if r['reason']=='formed'];require(len(successes)<=1,'one middle success')
    first=successes[0] if successes else None;later=[r for r in actions if first is not None and r['tick']>first]
    reasons=('dissolved',)+REASONS
    return dict(eligible_ticks=eligible,eligible_intervals=[dict(start=a,end=b,length=b-a+1) for a,b in spans],eligible_steps=len(eligible),eligible_prefix=True,
        first_north_ticket=north[0]['tick'] if north else None,first_north_proposal=proposals[0]['tick'] if proposals else None,
        north_tickets=len(north),north_proposals=len(proposals),north_energy_qualified=sum(r['preformation_energy']>=16 for r in proposals),north_energy_low=sum(r['preformation_energy']<16 for r in proposals),north_target_failures=sum(r['reason'] in ('occupied','raw_material','collision') for r in proposals),north_reasons={k:sum(r['reason']==k for r in north) for k in reasons},first_success_tick=first,qualification_loss_after_success=all(r['preformation_energy']<16 for r in later) if later else None,alive=alive,right_censored=alive,death_tick=next((r['tick'] for r in actions if r['died']),None))

def verify_case(encoding,branch,prior041):
    arm=branch['ablation'];sel=branch['selection'];t0=sel['t0'];people=arm['final']['individuals'];selected=sel['offspring_ids']
    labels=[]
    for i,p in enumerate(people):
        parent=p['parent'];require(parent is None or parent<i,'parent ordering')
        labels.append(LABELS[selected.index(i)] if i in selected else labels[parent] if parent is not None else 'other')
    frames=[];before=arm['initial']
    same(len(prior041['rows']),len(arm['rows']),'041 complete future')
    for row,old in zip(arm['rows'],prior041['rows']):
        p=row['physical'];same(old['tick'],row['tick'],'041 tick')
        energies,bonds,inputs=energy_stage(before['units'],[i['proposed'] for i in p['driven']['inputs']])
        same(inputs,p['driven']['inputs'],'independent feed/leak')
        same(bonds,p['driven']['interaction']['bonds'],'independent paid reservations');same(p['driven']['interaction']['transfers'],[],'no exchange')
        same(energies,[None if u is None else u['energy'] for u in p['interaction_units']],'independent intermediate energy')
        for site in (101,102):same(inputs[site]['proposed'],0,'no middle feed')
        qmap={q['source']:q for q in p['material']['proposals']};emap={e['source']:e for e in old['events']}
        same(sorted(qmap),sorted(emap),'041 actors')
        for site,q in qmap.items():
            e=emap[site];same(e['energy'],energies[site],'041 preformation energy');same(e['identity'],before['site_ids'][site],'041 actor identity')
            same((q['target'],q['direction'],q['reason']),(e['target'],e['direction'],e['reason']),'041 proposal')
            if q['reason']=='formed':
                child=(energies[site]-5)//2;parent=energies[site]-5-child
                same(q['child_energy'],child,'child transfer');same(q['parent_energy'],parent,'split remainder');same(q['cost'],5,'split cost')
                same(p['units'][site]['energy'],parent,'parent observed energy')
                same(p['units'][q['target']]['energy'],child,'child observed energy')
        imported=sum(i['accepted'] for i in inputs);leak=sum(i['leakage'] for i in inputs);created=sum(q['reason']=='formed' for q in qmap.values())
        initial=sum(u['energy'] for u in before['units'] if u is not None);final=sum(u['energy'] for u in p['units'] if u is not None)
        spent=leak+2*len(bonds)+5*created
        same(initial+imported-spent,final,'whole world energy ledger')
        same(p['energy_before'],initial,'initial energy');same(p['spent'],spent,'total spent');same(p['imported'],imported,'total imported');same(p['energy_after'],final,'final energy')
        frames.append((row,before,energies,bonds,inputs,qmap,emap))
        before=dict(units=p['units'],raw=p['raw'],site_ids=row['site_ids'])
    identities=[]
    for i,person in enumerate(people):
        site=person['site']
        if site not in (101,102) or (person['birth_tick']<=t0 and i not in arm['initial']['site_ids']):continue
        left=person['birth_tick']<=t0;birth=person['birth_tick'];parent=person['parent']
        if left:rows=[dict(phase='initial',tick=t0,end_energy=arm['initial']['units'][site]['energy'])]
        else:rows=[dict(phase='birth',tick=birth,end_energy=person['birth_energy'])]
        for row,before,energies,bonds,inputs,qmap,emap in frames:
            if before['site_ids'][site]!=i:continue
            p=row['physical'];tick=row['tick'];require(tick>birth,'newborn cannot act');pre=energies[site];died=pre==0
            q=qmap.get(site);reason='dissolved' if died else q['reason'];cost=5 if reason=='formed' else 0
            child=(pre-5)//2 if cost else 0;end=pre-cost-child
            if died:
                require(i in row['deaths'] and q is None,'old identity dissolution')
                same(person['death_tick'],tick,'death history')
            else:
                same(row['site_ids'][site],i,'surviving parent ID');same(p['units'][site]['energy'],end,'old identity end energy')
            paid=sum(site in edge for edge in bonds);inp=inputs[site]
            rows.append(dict(phase='action',tick=tick,age=tick-birth,before_energy=before['units'][site]['energy'],proposed=inp['proposed'],accepted=inp['accepted'],leakage=inp['leakage'],paid_bonds=paid,bond_spent=paid,preformation_energy=pre,direction=p['directions'][site],north_ticket=p['directions'][site]==3,proposal=emap.get(site),reason=reason,construction_spent=4 if cost else 0,copy_spent=1 if cost else 0,child_transfer=child,end_energy=end,died=died))
        alive=i in arm['final']['site_ids'];window=identity_window(rows,alive);same(window['death_tick'],person['death_tick'],'lifetime death')
        require(window['eligible_steps']<=max(0,person['birth_energy']-16) if not left else True,'eligible length bound')
        identities.append(dict(identity=i,site=site,lineage=labels[i],source_region=region(people[parent]['site']) if parent is not None else 'other',parent=parent,birth_tick=birth,birth_energy=person['birth_energy'],left_censored=left,rows=rows,window=window))
    return dict(encoding=encoding,selection=sel,saved_steps=len(arm['rows']),identities=identities)

def summarize(records):
    reasons=('dissolved',)+REASONS
    def stats(ids):
        actions=[a for i in ids for a in i['rows'] if a['phase']=='action'];windows=[i['window'] for i in ids]
        out=dict(identities=len(ids),action_steps=len(actions),births=sum(not i['left_censored'] for i in ids),left_censored=sum(i['left_censored'] for i in ids),right_censored=sum(w['right_censored'] for w in windows),natural_deaths=sum(w['death_tick'] is not None for w in windows),zero_windows=sum(w['eligible_steps']==0 for w in windows),eligible_steps=sum(w['eligible_steps'] for w in windows),no_north_proposal=sum(w['first_north_proposal'] is None for w in windows))
        for k in ('north_tickets','north_proposals','north_energy_qualified','north_energy_low','north_target_failures'):out[k]=sum(w[k] for w in windows)
        out['reasons']={k:sum(a['reason']==k for a in actions) for k in reasons}
        out['north_reasons']={k:sum(a['reason']==k and a['direction']==3 for a in actions) for k in reasons}
        out['energy']={k:sum(a[k] for a in actions) for k in ('proposed','accepted','leakage','bond_spent','construction_spent','copy_spent','child_transfer')}
        return out
    return dict(overall=stats([i for r in records for i in r['identities']]),cases=[dict(encoding=r['encoding'],seed=r['selection']['seed'],saved_steps=r['saved_steps'],**stats(r['identities'])) for r in records],cells=[dict(encoding=e,lineage=a,source_region=s,**stats([i for r in records if r['encoding']==e for i in r['identities'] if i['lineage']==a and i['source_region']==s])) for e in ('east','west') for a in LABELS for s in REGIONS])

def main():
    proof=OUTPUT/'independent-verification.json';require(not proof.exists(),'exclusive proof')
    start=monotonic();paths=[];result=dict(status='running',completed_cases=0,new_simulation_steps=0,review_mode='parent inline fallback independent energy accounting');files={}
    def budget():require(monotonic()-start<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'verification budget')
    try:
        paths=input_paths();result['input_sha256'],result['input_read_errors_before']=capture(paths);bound=bindings();same(bound,result['input_sha256'],'valid initial sources')
        files={n:digest(OUTPUT/n) for n in ('metadata.json','records.json','summary.json')};meta=read(OUTPUT/'metadata.json')
        same(meta['status'],'complete','producer completion');same(meta['input_sha256'],bound,'producer sources');same(meta['input_sha256_after'],bound,'producer final sources');same(meta['output_sha256'],{n:files[n] for n in ('records.json','summary.json')},'producer output hashes')
        require(meta['elapsed_seconds']<600,'producer time');same(meta['time_limit_seconds'],600,'time budget');same(meta['storage_limit_bytes'],134217728,'storage budget')
        old=read('data/v4-study-041/records.json');same(len(old),8,'all eight sourcecases');records=[]
        census=read('docs/research/results/v4-study-042-design-census.json')['births']
        for prior in old:
            budget();enc=prior['encoding'];seed=prior['selection']['seed'];branch=read(f'data/v4-study-039/cases/{enc}-{seed}.json');same(branch['selection'],prior['selection'],'source selection')
            record=verify_case(enc,branch,prior)
            chosen=[c for c in census if (c['encoding'],c['seed'])==(enc,seed)]
            same([(i['identity'],i['birth_energy'],i['source_region']) for i in record['identities']],[(c['identity'],c['birth_energy'],c['source_region']) for c in chosen],'frozen birth census')
            records.append(record);result['completed_cases']+=1
        same(sum(r['saved_steps'] for r in records),116,'complete source horizon');same(sum(len(r['identities']) for r in records),35,'35 identities')
        same(read(OUTPUT/'records.json'),records,'full independent timelines');same(read(OUTPUT/'summary.json'),summarize(records),'full independent summaries')
        same(bindings(),bound,'unchanged sources');same({n:digest(OUTPUT/n) for n in files},files,'unchanged outputs');budget()
        result.update(status='verified',saved_steps=116,identities=35,files_sha256=files)
    except BaseException as exc:
        result.update(status='failed',error=repr(exc));raise
    finally:
        result['input_sha256_after'],result['input_read_errors_after']=capture(paths);result['elapsed_seconds']=monotonic()-start
        try:
            if result['status']=='verified':
                same(result['input_sha256_after'],result['input_sha256'],'final sources');same(result['input_read_errors_after'],{},'final source errors');budget()
                require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())+len(json.dumps(result,indent=2).encode())<134217728,'final proof budget')
        except BaseException as exc:
            result.update(status='failed',error=repr(exc));save(proof,result);raise
        save(proof,result)
if __name__=='__main__':main()
