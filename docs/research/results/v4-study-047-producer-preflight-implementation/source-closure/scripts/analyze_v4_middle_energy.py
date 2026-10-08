"""Study042 saved-event middle identity energy accounts; never executes physics."""
from copy import deepcopy
from pathlib import Path
from time import monotonic
import subprocess
from scripts.analyze_v4_lineage_routes import analyze_case as routes, require, region, LINEAGES, REGIONS

OUTPUT=Path('data/v4-study-042')
REASONS=('dissolved','energy','occupied','raw_material','collision','formed')


def split(energy,proposal):
    child=(energy-5)//2;parent=energy-5-child
    require(energy>=16 and proposal['cost']==5 and proposal['child_energy']==child and proposal['parent_energy']==parent,'formation split')
    return 4,1,child,parent


def window(rows,alive):
    actions=[r for r in rows if r['phase']=='action']
    eligible=[r['tick'] for r in actions if r['preformation_energy']>=16]
    prefix=eligible==[r['tick'] for r in actions[:len(eligible)]]
    require(prefix,'eligible prefix')
    intervals=[]
    for t in eligible:
        if intervals and intervals[-1]['end']==t-1:intervals[-1]['end']=t;intervals[-1]['length']+=1
        else:intervals.append(dict(start=t,end=t,length=1))
    north=[r for r in actions if r['direction']==3];proposals=[r for r in north if r['reason']!='dissolved']
    success=next((r['tick'] for r in actions if r['reason']=='formed'),None)
    later=[r for r in actions if success is not None and r['tick']>success]
    return dict(eligible_ticks=eligible,eligible_intervals=intervals,eligible_steps=len(eligible),eligible_prefix=prefix,
        first_north_ticket=next((r['tick'] for r in north),None),first_north_proposal=next((r['tick'] for r in proposals),None),
        north_tickets=len(north),north_proposals=len(proposals),north_energy_qualified=sum(r['preformation_energy']>=16 for r in proposals),
        north_energy_low=sum(r['preformation_energy']<16 for r in proposals),
        north_target_failures=sum(r['reason'] in ('occupied','raw_material','collision') for r in proposals),
        north_reasons={k:sum(r['reason']==k for r in north) for k in REASONS},
        first_success_tick=success,qualification_loss_after_success=all(r['preformation_energy']<16 for r in later) if later else None,
        alive=alive,right_censored=alive,death_tick=next((r['tick'] for r in actions if r['reason']=='dissolved'),None))


def analyze_case(encoding,branch,prior041=None):
    route=routes(encoding,branch)
    if prior041 is not None:require(route==prior041,'041 account agreement')
    arm=branch['ablation'];initial=arm['initial'];people=arm['final']['individuals'];selection=deepcopy(branch['selection'])
    require(selection['exchange'] is False,'exchange disabled')
    members={};before=initial
    def add(identity,site,lineage,source_region,left,birth_row):
        person=people[identity]
        require(person['id']==identity and person['site']==site,'birth identity site')
        members[identity]=dict(identity=identity,site=site,lineage=lineage,source_region=source_region,parent=person['parent'],
            birth_tick=person['birth_tick'],birth_energy=person['birth_energy'],left_censored=left,rows=[birth_row])
    for lineage in LINEAGES:
        for p in route['diagnostic']['occupancy'][lineage]['middle']:
            i=p['identity'];s=p['site'];parent=people[i]['parent']
            # Historical birth record, not present location, establishes origin.
            source_region=region(people[parent]['site']) if parent is not None else 'other'
            add(i,s,lineage,source_region,True,dict(phase='initial',tick=initial['tick'],end_energy=initial['units'][s]['energy']))
    for saved,old in zip(arm['rows'],route['rows']):
        tick=saved['tick'];p=saved['physical'];dr=p['driven'];events={e['source']:e for e in old['events']};proposals={e['source']:e for e in p['material']['proposals']}
        require(dr['interaction']['transfers']==[],'no transfers')
        for site in (101,102):require(dr['inputs'][site]['proposed']==dr['inputs'][site]['accepted']==0,'zero middle input')
        bonds=dr['interaction']['bonds'];paid=[0]*256
        require(len({tuple(sorted(e)) for e in bonds})==len(bonds),'unique paid bonds')
        for x,y in bonds:
            require(x!=y and before['units'][x] is not None and before['units'][y] is not None,'paid bond endpoints')
            paid[x]+=1;paid[y]+=1
        energy_before=sum(u['energy'] for u in before['units'] if u is not None)
        for s,u in enumerate(before['units']):
            inp=dr['inputs'][s];inter=p['interaction_units'][s]
            require(inp['site']==s,'input site')
            accepted=0 if u is None else min(inp['proposed'],64-u['energy'])
            leakage=0 if u is None else min(1,u['energy']+accepted)
            require(inp['accepted']==accepted and inp['leakage']==leakage and inp['rejected']==inp['proposed']-accepted,'input and leakage ledger')
            if u is None:continue
            pre=u['energy']+accepted-leakage-paid[s]
            require(inter['energy']==pre and pre>=0,'paid bond energy')
            q=proposals.get(s);construction=copy=transfer=0;end=pre
            if q is not None and q['reason']=='formed':construction,copy,transfer,end=split(pre,q)
            if pre==0:require(q is None and before['site_ids'][s] in saved['deaths'],'zero identity death')
            else:require(saved['site_ids'][s]==before['site_ids'][s] and p['units'][s]['energy']==end,'parent end energy')
            if s not in (101,102):continue
            i=before['site_ids'][s];require(i in members,'tracked middle identity')
            require(tick>people[i]['birth_tick'],'birth tick cannot act')
            members[i]['rows'].append(dict(phase='action',tick=tick,age=tick-people[i]['birth_tick'],before_energy=u['energy'],
                proposed=inp['proposed'],accepted=accepted,leakage=leakage,paid_bonds=paid[s],bond_spent=paid[s],
                preformation_energy=pre,direction=p['directions'][s],north_ticket=p['directions'][s]==3,
                proposal=deepcopy(events.get(s)),reason='dissolved' if pre==0 else q['reason'],
                construction_spent=construction,copy_spent=copy,child_transfer=transfer,end_energy=end,died=pre==0))
        births=[e for e in old['events'] if e['child_id'] is not None]
        for e in births:
            q=proposals[e['source']];child=e['child_id'];target=e['target']
            require(p['units'][target]['energy']==q['child_energy']==people[child]['birth_energy'],'child birth energy')
            require(people[child]['birth_tick']==tick and people[child]['parent']==e['identity'],'birth provenance')
            if target in (101,102):
                require(child not in members and q['child_energy']<=29,'new middle identity bound')
                add(child,target,e['lineage'],region(e['source']),False,dict(phase='birth',tick=tick,end_energy=q['child_energy']))
        final_energy=sum(u['energy'] for u in p['units'] if u is not None)
        leakage=sum(i['leakage'] for i in dr['inputs']);imported=sum(i['accepted'] for i in dr['inputs']);spent=leakage+2*len(bonds)+5*len(births)
        require(dr['energy_before']==p['energy_before']==energy_before and dr['leakage']==leakage and dr['imported']==p['imported']==imported,'whole input ledger')
        require(dr['interaction']['spent']==2*len(bonds) and dr['spent']==leakage+2*len(bonds),'whole bond ledger')
        require(p['material']['spent']==5*len(births) and p['spent']==spent and p['energy']==p['energy_after']==final_energy==energy_before+imported-spent,'whole final energy ledger')
        require(p['material']['energy_before']==dr['energy_after']==energy_before+imported-dr['spent'] and p['material']['energy_after']==final_energy,'whole phase ledger')
        before=dict(units=p['units'],site_ids=saved['site_ids'],raw=p['raw'])
    for i,m in members.items():
        alive=i in arm['final']['site_ids'];m['window']=window(m['rows'],alive)
        require(m['window']['death_tick']==people[i]['death_tick'],'identity death chronology')
        if not m['left_censored']:
            require(m['window']['eligible_steps']<=max(0,m['birth_energy']-16)<=13,'birth eligibility bound')
            require(all(r['preformation_energy']<=m['birth_energy']-r['age'] for r in m['rows'] if r['phase']=='action'),'age energy bound')
        require(sum(r.get('reason')=='formed' for r in m['rows'])<=1,'middle at most one success')
    return dict(encoding=encoding,selection=selection,saved_steps=len(arm['rows']),identities=[members[i] for i in sorted(members)])


def summarize(records):
    def stats(ids):
        actions=[v for i in ids for v in i['rows'] if v['phase']=='action']
        return dict(identities=len(ids),action_steps=len(actions),births=sum(not i['left_censored'] for i in ids),left_censored=sum(i['left_censored'] for i in ids),
            right_censored=sum(i['window']['right_censored'] for i in ids),natural_deaths=sum(i['window']['death_tick'] is not None for i in ids),
            zero_windows=sum(i['window']['eligible_steps']==0 for i in ids),eligible_steps=sum(i['window']['eligible_steps'] for i in ids),
            no_north_proposal=sum(i['window']['first_north_proposal'] is None for i in ids),
            **{k:sum(i['window'][k] for i in ids) for k in ('north_tickets','north_proposals','north_energy_qualified','north_energy_low','north_target_failures')},
            reasons={r:sum(v['reason']==r for v in actions) for r in REASONS},north_reasons={r:sum(i['window']['north_reasons'][r] for i in ids) for r in REASONS},
            energy={k:sum(v[k] for v in actions) for k in ('proposed','accepted','leakage','bond_spent','construction_spent','copy_spent','child_transfer')})
    return dict(overall=stats([i for r in records for i in r['identities']]),
        cases=[dict(encoding=r['encoding'],seed=r['selection']['seed'],saved_steps=r['saved_steps'],**stats(r['identities'])) for r in records],
        cells=[dict(encoding=e,lineage=l,source_region=s,**stats([i for r in records if r['encoding']==e for i in r['identities'] if i['lineage']==l and i['source_region']==s])) for e in ('east','west') for l in LINEAGES for s in REGIONS])


def main():
    from scripts.middle_energy_inputs import bindings,sources,read,save,digest,input_paths,capture
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
        prior={(r['encoding'],r['selection']['seed']):r for r in read('data/v4-study-041/records.json')}
        for enc,path,_ in sources():
            budget();branch=read(path);record=analyze_case(enc,branch,prior[(enc,branch['selection']['seed'])]);records.append(record)
            meta.update(completed_cases=len(records),saved_steps=sum(r['saved_steps'] for r in records),diagnostic_states=len(records))
            save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta);budget()
        require(meta['completed_cases']==8 and meta['saved_steps']==116,'complete fixed cohort')
        require(sum(len(r['identities']) for r in records)==35,'all35 middle identities')
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
