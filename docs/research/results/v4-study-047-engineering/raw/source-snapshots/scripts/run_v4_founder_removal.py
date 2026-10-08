"""Study036: paired original-ticket continuation after founder removal."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import subprocess
import time

from bitgenesis.v4.hereditary_growing import step
from bitgenesis.v4.heredity import HeritableUnit
from bitgenesis.v4.lineage import Observer
from bitgenesis.v4.structure import snapshot
from scripts.analyze_v4_structure_copies import canonical, episodes, require
from scripts.run_v4_copy_control import CONFIG, normalize

OUTPUT=Path('data/v4-study-036')
SELECTION=Path('docs/research/results/v4-study-035-selection.json')
METRICS=('births','deaths','living','final_energy','imported','spent','new_copy_ever',
         'double_new_ever','persistent10','longest_double','formation_supported','upper_formed','selected_ancestry_supported','formation_persistent10','upper_persistent10','selected_ancestry_persistent10')
CATEGORIES=('horizontal_structural_zero','short_window','remaining_conditional')
_steps={'control':0,'ablation':0}


def intervene(units,raw,observer):
    removed=[]
    for identity in (0,1):
        require(identity in observer.alive,'living original member')
        site=observer.alive.index(identity)
        removed.append(dict(identity=identity,site=site,energy=units[site]['energy']))
        units[site]=None;raw[site]+=1;observer.alive[site]=None
    return removed,sum(r['energy'] for r in removed)


def match_copies(anchor,units,ids,observation,individuals):
    def fingerprint(members,us,site_ids):
        sites={i:s for s,i in enumerate(site_ids) if i is not None}
        return canonical([(sites[i]%16,sites[i]//16,us[sites[i]]['material'],tuple(us[sites[i]]['program'])) for i in members])
    target=fingerprint([0,1],anchor['units'],anchor['site_ids'])
    result=[]
    for members in observation['components']['material']:
        if len(members)!=2 or not all(individuals[i]['founder'] in (0,1) for i in members):continue
        if fingerprint(members,units,ids)==target:
            result.append(dict(members=list(members),sites=[ids.index(i) for i in members],all_new=not bool(set(members)&{0,1})))
    return result


def ancestry(identity,individuals,selected):
    chain=[];current=identity
    while current is not None:
        chain.append(current)
        if current in selected:return dict(identity=identity,chain=chain,selected_ancestor=current)
        current=individuals[current]['parent']
    return dict(identity=identity,chain=chain,selected_ancestor=None)


def summarize_arm(arm,selected):
    t0=arm['initial']['tick'];rows=arm['rows'];people=arm['final']['individuals']
    counts=[sum(c['all_new'] for c in r['copies']) for r in rows]
    spans=[[a+t0,b+t0] for a,b in episodes(counts)]
    longest=max((b-a+1 for a,b in spans),default=0)
    formations=[];upper=[]
    def witness(i):
        p=people[i]
        return dict(identity=i,birth_tick=p['birth_tick'],parent=p['parent'],site=p['site'])
    for row,n in zip(rows,counts):
        if n<2:continue
        copies=[c for c in row['copies'] if c['all_new']]
        born=[witness(i) for c in copies for i in c['members'] if people[i]['birth_tick']>t0]
        if born:formations.append(dict(tick=row['tick'],copies=[c['members'] for c in copies],births=born))
        for c in copies:
            if sorted(c['sites'])==[85,86] and all(people[i]['birth_tick']>t0 for i in c['members']):
                upper.append(dict(tick=row['tick'],members=c['members'],sites=c['sites'],births=[witness(i) for i in c['members']],selected_ancestry=[ancestry(i,people,selected) for i in c['members']]))
    metrics=dict(births=sum(len(r['births']) for r in rows),deaths=sum(len(r['deaths']) for r in rows),
                 living=sum(u is not None for u in arm['final']['units']),
                 final_energy=sum(u['energy'] for u in arm['final']['units'] if u is not None),
                 imported=sum(r['physical']['imported'] for r in rows),spent=sum(r['physical']['spent'] for r in rows),
                 new_copy_ever=int(any(counts)),double_new_ever=int(longest>0),persistent10=int(longest>=10),
                 longest_double=longest,formation_supported=int(bool(formations)),upper_formed=int(bool(upper)),
                 selected_ancestry_supported=int(any(all(a['selected_ancestor'] is not None for a in w['selected_ancestry']) for w in upper)))
    for name,ticks in (('formation_persistent10',{w['tick'] for w in formations}),('upper_persistent10',{w['tick'] for w in upper}),('selected_ancestry_persistent10',{w['tick'] for w in upper if all(a['selected_ancestor'] is not None for a in w['selected_ancestry'])})):
        metrics[name]=int(any(b-a+1>=10 for a,b in episodes([2 if r['tick'] in ticks else 0 for r in rows])))
    return dict(metrics=metrics,new_copy_counts=counts,episodes=spans,formation_witnesses=formations,upper_witnesses=upper)


def run_arm(source,selection,name,budget=lambda:None):
    t0=selection['t0'];observer=Observer(source['initial']['units'])
    for saved in source['rows'][:t0]:
        observer.accept(saved['physical']);require(observer.alive==saved['site_ids'],'source prefix identities')
    saved=source['rows'][t0-1];units=deepcopy(saved['physical']['units']);raw=list(saved['physical']['raw'])
    energy_before=sum(u['energy'] for u in units if u is not None)
    removals,exported=intervene(units,raw,observer) if name=='ablation' else ([],0)
    initial=dict(tick=t0,units=deepcopy(units),raw=list(raw),site_ids=list(observer.alive),
                 parents=[p['parent'] for p in observer.individuals],individuals=deepcopy(observer.individuals),
                 observation=snapshot(units,observer.alive,16,16,phase='final'),removals=removals,
                 energy_before=energy_before,energy_export=exported,energy_after=sum(u['energy'] for u in units if u is not None))
    initial['copies']=match_copies(source['initial'],units,observer.alive,initial['observation'],observer.individuals)
    require(initial['energy_after']==energy_before-exported,'immediate export ledger')
    require(all(raw[s]+int(units[s] is not None)==saved['physical']['raw'][s]+int(saved['physical']['units'][s] is not None) for s in range(256)),'local material ledger')
    units=[None if u is None else HeritableUnit(u['material'],u['energy'],tuple(u['program'])) for u in units];rows=[]
    mass=sum(raw)+sum(u is not None for u in units)
    for tick in range(t0+1,33):
        budget();old=source['rows'][tick-1];p=old['physical'];inputs=p['driven']['inputs']
        require([v['site'] for v in inputs]==list(range(256)),'ordered source proposals')
        before=sum(u.energy for u in units if u is not None);prior_ids=list(observer.alive);birth_start=len(observer.individuals)
        units,raw,event=step(units,raw,proposals=[v['proposed'] for v in inputs],directions=p['directions'],mutation_tickets=[tuple(v) for v in p['mutation_tickets']],exchange=selection['exchange'],**CONFIG)
        _steps[name]+=1
        physical=normalize(dict(tick=tick,units=[None if u is None else asdict(u) for u in units],raw=list(raw),energy=sum(u.energy for u in units if u is not None),directions=p['directions'],mutation_tickets=p['mutation_tickets'],**event))
        require(physical['energy']==before+event['imported']-event['spent'],'step energy ledger')
        require(event['material_before']==event['material_after']==sum(raw)+sum(u is not None for u in units)==mass,'step material ledger')
        observer.accept(physical);observation=snapshot(physical['units'],observer.alive,16,16,phase='final')
        if name=='control':require(physical==old['physical'] and observer.alive==old['site_ids'] and observation==old['observation'],'control exact saved suffix')
        lineage=[]
        for identity in selection['offspring_ids']:
            living=[i for i in observer.alive if i is not None and ancestry(i,observer.individuals,[identity])['selected_ancestor'] is not None]
            lineage.append(dict(identity=identity,alive=identity in observer.alive,living_descendants=sorted(living)))
        rows.append(dict(tick=tick,site_ids=list(observer.alive),physical=physical,observation=observation,
                         copies=match_copies(source['initial'],physical['units'],observer.alive,observation,observer.individuals),
                         births=deepcopy(observer.individuals[birth_start:]),deaths=[prior_ids[s] for s in event['material']['dissolved']],selected_lineage=lineage))
    final=dict(tick=32,units=normalize([None if u is None else asdict(u) for u in units]),raw=list(raw),site_ids=list(observer.alive),parents=[p['parent'] for p in observer.individuals],individuals=deepcopy(observer.individuals))
    arm=dict(initial=initial,rows=rows,final=final);arm.update(summarize_arm(arm,selection['offspring_ids']))
    m=arm['metrics'];require(m['final_energy']==energy_before-exported+m['imported']-m['spent'],'cumulative export once')
    return arm


def run_branch(source,selection,budget=lambda:None):
    require(selection['eligible'] and source['config']==CONFIG,'eligible fixed source')
    require(all(source[k]==selection[k] for k in ('mode','seed','exchange')) and not selection['exchange'],'source identity')
    require(len(source['rows'])==32 and selection['remaining_steps']==32-selection['t0'],'fixed horizon')
    t0=selection['t0'];row=source['rows'][t0-1]
    history=Observer(source['initial']['units']);first=None
    for original in source['rows'][:t0]:
        history.accept(original['physical'])
        matches=match_copies(source['initial'],original['physical']['units'],history.alive,original['observation'],history.individuals)
        if first is None and any(c['all_new'] for c in matches):first=original['tick']
    require(first==t0,'first eligible final state')
    require(any(c['all_new'] and set(c['members'])==set(selection['offspring_ids']) for c in matches),'selected whole new copy')
    require([row['site_ids'][s] for s in selection['offspring_sites']]==selection['offspring_ids'],'selected lower identities')
    require([row['site_ids'][s] for s in selection['original_sites']]==[0,1],'original identities')
    control=run_arm(source,selection,'control',budget);ablation=run_arm(source,selection,'ablation',budget)
    require(ablation['initial']['energy_export']==selection['energy_export_preview'],'selection export preview')
    if selection['category']==CATEGORIES[0]:require(ablation['metrics']['double_new_ever']==0,'structural zero')
    return dict(selection=deepcopy(selection),control=control,ablation=ablation,delta={k:ablation['metrics'][k]-control['metrics'][k] for k in METRICS})


def record(branch):
    return dict(selection=deepcopy(branch['selection']),control_metrics=deepcopy(branch['control']['metrics']),ablation_metrics=deepcopy(branch['ablation']['metrics']),delta=deepcopy(branch['delta']),control_episodes=deepcopy(branch['control']['episodes']),ablation_episodes=deepcopy(branch['ablation']['episodes']))


def summarize(records,selection):
    eligible=[s for s in selection if s['eligible']]
    require([r['selection'] for r in records]==eligible,'complete ordered selection')
    def group(rows):
        return dict(n=len(rows),control_totals={k:sum(r['control_metrics'][k] for r in rows) for k in METRICS},ablation_totals={k:sum(r['ablation_metrics'][k] for r in rows) for k in METRICS},delta_totals={k:sum(r['delta'][k] for r in rows) for k in METRICS},paired_persistent10=[dict(control=c,ablation=a,n=sum(r['control_metrics']['persistent10']==c and r['ablation_metrics']['persistent10']==a for r in rows)) for c in (0,1) for a in (0,1)])
    cells=[]
    for genotype in ('homogeneous','heterogeneous'):
        for mode in ('random-direction','random-feed','random-both'):
            for exchange in (False,True):
                chosen=[r for r in records if (r['selection']['genotype'],r['selection']['mode'],r['selection']['exchange'])==(genotype,mode,exchange)]
                cells.append(dict(genotype=genotype,mode=mode,exchange=exchange,**group(chosen)))
    return dict(source_cases=len(selection),eligible=len(records),noeligible=len(selection)-len(records),cells=cells,strata=[dict(category=c,**group([r for r in records if r['selection']['category']==c])) for c in CATEGORIES],overall=group(records))


def main():
    from scripts.founder_removal_inputs import bindings,input_paths,read,save,digest
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();records=[];inventory=[];baseline=dict(_steps)
    meta=dict(status='running',planned_cases=58,completed_cases=0,treatment_steps=0,control_replay_steps=0,new_environment_sources=0,new_independent_initial_worlds=0,reused_environment_sources=20,selected_environment_sources=19,time_limit_seconds=600,storage_limit_bytes=134217728)
    def budget():
        require(time.monotonic()-started<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'bounded execution')
    def hashes():return {str(p.relative_to(OUTPUT)):digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p!=OUTPUT/'metadata.json'}
    def input_hashes(error_key):
        values={};meta[error_key]={}
        for path in inventory:
            try:values[path]=digest(path)
            except BaseException as exc:meta[error_key][path]=repr(exc)
        return values
    def progress():
        meta.update(completed_cases=len(records),treatment_steps=_steps['ablation']-baseline['ablation'],control_replay_steps=_steps['control']-baseline['control'],elapsed_seconds=time.monotonic()-started)
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        meta['input_inventory_errors']={};inventory=input_paths(meta['input_inventory_errors']);meta['input_paths']=inventory
        meta['input_sha256']=input_hashes('input_read_errors_before')
        save(OUTPUT/'metadata.json',meta);save(OUTPUT/'records.json',records);(OUTPUT/'cases').mkdir()
        before=bindings();require(before==meta['input_sha256'],'validated initial inputs');budget()
        selection=read(SELECTION)['cases'];eligible=[s for s in selection if s['eligible']]
        require(len(selection)==240 and len(eligible)==58,'fixed cohort')
        require([sum(s['category']==c for s in eligible) for c in CATEGORIES]==[36,8,14],'fixed strata')
        require(sum(s['remaining_steps'] for s in eligible)==1260,'fixed planned steps')
        save(OUTPUT/'selection.json',selection)
        for index,selected in enumerate(eligible):
            budget();branch=run_branch(read(Path(selected['source'])),selected,budget)
            save(OUTPUT/'cases'/f'branch-{index:03d}.json',branch);records.append(record(branch));progress()
            save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta);budget()
        require(meta['treatment_steps']==meta['control_replay_steps']==1260,'fixed completed steps')
        save(OUTPUT/'summary.json',summarize(records,selection))
        meta['input_sha256_after']=bindings();require(before==meta['input_sha256_after'],'unchanged inputs')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256=hashes())
        budget();save(OUTPUT/'metadata.json',meta);budget()
    except BaseException as exc:
        progress();meta.update(status='failed',error=repr(exc))
        try:
            meta['input_sha256_after']=bindings()
            if meta.get('input_sha256')!=meta['input_sha256_after']:meta['finalization_error']='inputs changed during failure'
        except BaseException as err:
            meta['finalization_error']=repr(err);meta['input_sha256_after']=input_hashes('input_read_errors')
        try:meta['output_sha256']=hashes()
        except BaseException as err:meta['output_hash_error']=repr(err)
        save(OUTPUT/'metadata.json',meta);raise


if __name__=='__main__':main()
