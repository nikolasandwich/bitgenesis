"""Study043: fixed middle north tickets after saved first-copy removal."""
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path
import subprocess
import time

from bitgenesis.v4.hereditary_growing import step
from bitgenesis.v4.heredity import HeritableUnit
from bitgenesis.v4.lineage import Observer
from bitgenesis.v4.structure import snapshot
from scripts.analyze_v4_structure_copies import require
from scripts.run_v4_copy_control import CONFIG, normalize
from scripts import run_v4_founder_removal as removal
from scripts import run_v4_triggered_policy as prior
from scripts.run_v4_program_position import ENCODINGS, SEEDS
from scripts.program_position_inputs import read, save, digest
from scripts.run_v4_founder_removal import match_copies, ancestry, summarize_arm

OUTPUT=Path('data/v4-study-043')
CENSUS=Path('docs/research/results/v4-study-043-design-census.json')
SECONDS=600
STORAGE=128*1024**2
METRICS=prior.METRICS
_steps={'control':0,'ablation':0}


def north_directions(original):
    require(len(original)==256 and all(type(d) is int and d in range(4) for d in original),'complete valid direction tape')
    result=list(original);result[101]=result[102]=3
    return result


def run_arm(source,selection,old_arm,budget=lambda:None):
    t0=selection['t0'];observer=Observer(source['initial']['units'])
    for saved in source['rows'][:t0]:
        observer.accept(saved['physical']);require(observer.alive==saved['site_ids'],'source prefix identities')
    initial=deepcopy(old_arm['initial'])
    require(initial['tick']==t0 and initial['individuals']==observer.individuals,'prefix history only')
    expected_ids=list(observer.alive)
    expected_units=deepcopy(source['rows'][t0-1]['physical']['units'])
    expected_raw=list(source['rows'][t0-1]['physical']['raw'])
    removals=[]
    for identity in (0,1):
        require(identity in expected_ids,'living original identity')
        site=expected_ids.index(identity)
        removals.append(dict(identity=identity,site=site,energy=expected_units[site]['energy']))
        expected_ids[site]=None;expected_units[site]=None;expected_raw[site]+=1
    require(initial['site_ids']==expected_ids and initial['units']==expected_units and initial['raw']==expected_raw,'exact old removal state')
    require(initial['removals']==removals and initial['energy_export']==sum(r['energy'] for r in removals),'one original export')
    observer.alive=list(initial['site_ids'])
    units=deepcopy(initial['units']);raw=list(initial['raw'])
    energy_before=initial['energy_before'];exported=initial['energy_export']
    require(initial['parents']==[p['parent'] for p in observer.individuals],'historical parent array')
    require(initial['energy_after']==sum(u['energy'] for u in units if u is not None)==energy_before-exported,'initial energy ledger')
    units=[None if u is None else HeritableUnit(u['material'],u['energy'],tuple(u['program'])) for u in units];rows=[]
    mass=sum(raw)+sum(u is not None for u in units)
    for tick in range(t0+1,33):
        budget();old=source['rows'][tick-1];p=old['physical'];inputs=p['driven']['inputs']
        require([v['site'] for v in inputs]==list(range(256)),'ordered source proposals')
        directions=north_directions(p['directions'])
        before=sum(u.energy for u in units if u is not None);prior_ids=list(observer.alive);birth_start=len(observer.individuals)
        units,raw,event=step(units,raw,proposals=[v['proposed'] for v in inputs],directions=directions,mutation_tickets=[tuple(v) for v in p['mutation_tickets']],exchange=selection['exchange'],**CONFIG)
        _steps['ablation']+=1
        physical=normalize(dict(tick=tick,units=[None if u is None else asdict(u) for u in units],raw=list(raw),energy=sum(u.energy for u in units if u is not None),directions=directions,mutation_tickets=p['mutation_tickets'],**event))
        require(physical['energy']==before+event['imported']-event['spent'],'step energy ledger')
        require(event['material_before']==event['material_after']==sum(raw)+sum(u is not None for u in units)==mass,'step material ledger')
        observer.accept(physical);observation=snapshot(physical['units'],observer.alive,16,16,phase='final')
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


def run_branch(source,selection,old_arm,budget=lambda:None):
    require(selection['eligible'] and source['config']==CONFIG,'eligible fixed source')
    require(all(source[k]==selection[k] for k in ('mode','seed','exchange')) and not selection['exchange'],'source identity')
    require(len(source['rows'])==32 and 1<=selection['t0']<=32 and selection['remaining_steps']==32-selection['t0'],'fixed horizon')
    require(prior.selection(source,source['encoding'])==selection,'first frozen trigger selection')
    ablation=run_arm(source,selection,old_arm,budget)
    require(ablation['initial']==old_arm['initial'],'field identical t0 plus')
    mask=[dict(tick=r['tick'],site=s,original_direction=r['physical']['directions'][s],new_direction=3,changed=r['physical']['directions'][s]!=3) for r in source['rows'][selection['t0']:] for s in (101,102)]
    return dict(selection=deepcopy(selection),control=deepcopy(old_arm),ablation=ablation,
                delta={k:ablation['metrics'][k]-old_arm['metrics'][k] for k in removal.METRICS},direction_mask=mask)


def no_trigger_record(old):
    require(not old['trigger'],'no trigger only')
    result=deepcopy(old)
    for suffix in ('metrics','future_metrics','episodes'):
        result['control_'+suffix]=deepcopy(old['ablation_'+suffix])
    result['delta']=dict.fromkeys(old['delta'],0)
    return result


def summarize(records):
    result=prior.summarize(records)
    for group in [result['overall'],*result['cells']]:
        group['mean_delta']={k:str(Fraction(v,group['n'])) for k,v in group['delta_totals'].items()}
    index={(r['encoding'],r['seed']):r for r in records}
    for contrast in result['north_contrasts']+result['homogeneous_contrasts']:
        e=contrast['encoding'];ref=contrast['reference']
        pairs=[dict(seed=s,delta={k:index[e,s]['delta'][k]-index[ref,s]['delta'][k] for k in METRICS}) for s in SEEDS]
        totals={k:sum(p['delta'][k] for p in pairs) for k in METRICS}
        contrast.update(estimand='difference_in_differences',paired_persistent10_basis='new_policy',pairs=pairs,totals=totals,
            mean_delta={k:str(Fraction(v,20)) for k,v in totals.items()},
            positive={k:sum(p['delta'][k]>0 for p in pairs) for k in METRICS},
            negative={k:sum(p['delta'][k]<0 for p in pairs) for k in METRICS},
            tie={k:sum(p['delta'][k]==0 for p in pairs) for k in METRICS})
    return result


def main():
    from scripts.middle_north_policy_inputs import bindings,input_paths
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();baseline=dict(_steps);records=[];inventory=[]
    meta=dict(status='running',planned_cases=100,planned_triggers=28,planned_new_steps=390,completed_cases=0,completed_triggers=0,new_treatment_steps=0,control_replay_steps=0,reused_treatment_steps=0,new_environment_sources=0,new_independent_initial_worlds=0,time_limit_seconds=SECONDS,storage_limit_bytes=STORAGE)
    def progress():meta.update(completed_cases=len(records),completed_triggers=sum(r['trigger'] for r in records),new_treatment_steps=_steps['ablation']-baseline['ablation'],control_replay_steps=_steps['control']-baseline['control'],elapsed_seconds=time.monotonic()-started)
    def budget():require(time.monotonic()-started<SECONDS and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<STORAGE,'bounded execution')
    def hashes():return {str(p.relative_to(OUTPUT)):digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p!=OUTPUT/'metadata.json'}
    def raw_hashes():
        values={};errors={}
        for p in inventory:
            try:values[p]=digest(p)
            except BaseException as exc:errors[p]=repr(exc)
        meta['input_read_errors']=errors;return values
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        meta['input_inventory_errors']={};inventory=input_paths(meta['input_inventory_errors']);meta['input_paths']=inventory
        meta['input_sha256']=raw_hashes();save(OUTPUT/'metadata.json',meta);save(OUTPUT/'records.json',records)
        before=bindings();require(before==meta['input_sha256'],'validated initial bindings');(OUTPUT/'cases').mkdir();budget()
        census=read(CENSUS)['cases'];selections=[]
        old_records=read('data/v4-study-039/records.json')
        old_index={(r['encoding'],r['seed']):r for r in old_records}
        require(len(old_records)==len(old_index)==100,'complete old records')
        require(len(census)==100 and [(r['encoding'],r['seed']) for r in census]==[(e,s) for e in ENCODINGS for s in SEEDS],'ordered frozen census')
        by_encoding=dict.fromkeys(ENCODINGS,0)
        for item in census:
            budget();encoding=item['encoding'];seed=item['seed'];old=old_index[encoding,seed]
            require(all(item[k]==old[k] for k in ('source','trigger','t0','remaining','short_window')),'frozen source and trigger')
            if item['trigger']:
                case=prior.source_case(encoding,seed);sel=prior.selection(case,encoding)
                require(sel==old['selection'],'old first trigger selection')
                previous=read(item['baseline'])
                require(previous['selection']==sel and previous['ablation']['metrics']==old['ablation_future_metrics'],'old ablation only')
                branch=run_branch(case,sel,previous['ablation'],budget)
                require(branch['direction_mask']==item['mask'],'exact frozen mask')
                record=prior.produce_record(case,sel,branch['control'],branch['ablation'])
                require(record['control_metrics']==old['ablation_metrics'] and record['control_future_metrics']==old['ablation_future_metrics'],'old policy metric reuse')
                save(OUTPUT/'cases'/f'{encoding}-{seed}.json',branch)
                selections.append(dict(encoding=encoding,**sel));by_encoding[encoding]+=sel['remaining_steps']
                meta['reused_treatment_steps']+=sel['remaining_steps']
            else:
                require(item['baseline'] is None and item['mask']==[],'no trigger no intervention')
                record=no_trigger_record(old)
            records.append(record);progress()
            save(OUTPUT/'records.json',records);save(OUTPUT/'selection.json',selections);save(OUTPUT/'metadata.json',meta);budget()
        require(meta['new_treatment_steps']==390 and meta['control_replay_steps']==0 and meta['reused_treatment_steps']==390 and meta['completed_triggers']==28,'fixed complete budgets')
        require(by_encoding==dict(east=70,west=46,south=0,north=133,homogeneous=141),'fixed encoding budgets')
        meta['new_steps_by_encoding']=by_encoding
        save(OUTPUT/'summary.json',summarize(records));meta['input_sha256_after']=bindings();require(before==meta['input_sha256_after'],'unchanged inputs')
        meta.update(status='complete',output_sha256=hashes());progress();budget();save(OUTPUT/'metadata.json',meta);budget()
    except BaseException as exc:
        progress();meta.update(status='failed',error=repr(exc))
        try:meta['input_sha256_after']=bindings()
        except BaseException as err:meta['finalization_error']=repr(err);meta['input_sha256_after']=raw_hashes()
        if meta.get('input_sha256')!=meta['input_sha256_after']:meta['bindings_changed']=True
        try:meta['output_sha256']=hashes()
        except BaseException as err:meta['output_hash_error']=repr(err)
        save(OUTPUT/'metadata.json',meta);raise

if __name__=='__main__':main()
