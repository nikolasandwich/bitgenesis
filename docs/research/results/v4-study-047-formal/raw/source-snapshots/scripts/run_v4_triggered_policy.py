"""Study039 first-new-copy removal policy; saved controls never replay physics."""
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import subprocess
import time

from bitgenesis.v4.lineage import Observer
from bitgenesis.v4.structure import snapshot
from scripts.analyze_v4_structure_copies import require
from scripts import run_v4_founder_removal as removal
from scripts.run_v4_program_position import ENCODINGS, SEEDS, observe_case
from scripts.program_position_inputs import source_path, read, save, digest

OUTPUT=Path('data/v4-study-039')
SECONDS=600
STORAGE=128*1024**2
PHYSICAL=('births','deaths','living','final_energy','imported','spent')
METRICS=removal.METRICS+('rejected_import','energy_export','removals')


def source_location(encoding,seed):
    require(encoding in ENCODINGS and type(seed) is int and seed in SEEDS,'fixed source key')
    return Path(f'data/v4-study-038/cases/{encoding}-{seed}.json') if encoding in ENCODINGS[:3] else source_path(seed,encoding)


def source_case(encoding,seed):
    case=read(source_location(encoding,seed));case['encoding']=encoding
    return case


def selection(source,encoding):
    observed=observe_case(source,encoding)[0]
    t0=observed['first_new_genetic_copy_tick']
    if t0 is None:return None
    observer=Observer(source['initial']['units'])
    for row in source['rows'][:t0]:observer.accept(row['physical'])
    row=source['rows'][t0-1]
    copies=removal.match_copies(source['initial'],row['physical']['units'],row['site_ids'],row['observation'],observer.individuals)
    chosen=next(c for c in copies if c['all_new'])
    sites=sorted(chosen['sites']);ids=[row['site_ids'][s] for s in sites]
    return dict(genotype='homogeneous' if encoding=='homogeneous' else 'heterogeneous',mode=source['mode'],exchange=source['exchange'],seed=source['seed'],source=str(source_location(encoding,source['seed'])),eligible=True,t0=t0,remaining_steps=32-t0,category='short_window' if 32-t0<10 else 'remaining_conditional',original_sites=[row['site_ids'].index(i) for i in (0,1)],offspring_ids=ids,offspring_sites=sites,energy_export_preview=sum(row['physical']['units'][row['site_ids'].index(i)]['energy'] for i in (0,1)))


def observe_arm(source,sel):
    """Reconstruct the exact036 control schema from saved states and events only."""
    observer=Observer(source['initial']['units']);t0=sel['t0'];rows=[]
    for saved in source['rows'][:t0]:
        observer.accept(saved['physical']);require(observer.alive==saved['site_ids'],'saved prefix identities')
    saved=source['rows'][t0-1];p=saved['physical'];energy=sum(u['energy'] for u in p['units'] if u is not None)
    initial=dict(tick=t0,units=deepcopy(p['units']),raw=list(p['raw']),site_ids=list(observer.alive),parents=[v['parent'] for v in observer.individuals],individuals=deepcopy(observer.individuals),observation=deepcopy(saved['observation']),removals=[],energy_before=energy,energy_export=0,energy_after=energy)
    initial['copies']=removal.match_copies(source['initial'],p['units'],observer.alive,initial['observation'],observer.individuals)
    for saved in source['rows'][t0:]:
        p=saved['physical'];prior=list(observer.alive);start=len(observer.individuals);observer.accept(p)
        require(observer.alive==saved['site_ids'],'saved suffix identities')
        require(snapshot(p['units'],observer.alive,16,16,phase='final')==saved['observation'],'saved suffix components')
        lineage=[dict(identity=i,alive=i in observer.alive,living_descendants=sorted(j for j in observer.alive if j is not None and removal.ancestry(j,observer.individuals,[i])['selected_ancestor'] is not None)) for i in sel['offspring_ids']]
        rows.append(dict(tick=saved['tick'],site_ids=list(observer.alive),physical=deepcopy(p),observation=deepcopy(saved['observation']),copies=removal.match_copies(source['initial'],p['units'],observer.alive,saved['observation'],observer.individuals),births=deepcopy(observer.individuals[start:]),deaths=[prior[s] for s in p['material']['dissolved']],selected_lineage=lineage))
    last=source['rows'][-1]['physical']
    final=dict(tick=32,units=deepcopy(last['units']),raw=list(last['raw']),site_ids=list(observer.alive),parents=[v['parent'] for v in observer.individuals],individuals=deepcopy(observer.individuals))
    arm=dict(initial=initial,rows=rows,final=final);arm.update(removal.summarize_arm(arm,sel['offspring_ids']))
    return arm


def reuse_arm(source,sel,control):
    old=read('data/v4-study-036/records.json')
    matches=[i for i,r in enumerate(old) if r['selection']==sel]
    require(len(matches)==1,'exact old selection identity')
    branch=read(f'data/v4-study-036/cases/branch-{matches[0]:03d}.json')
    require(branch['selection']==sel and branch['control']==control,'exact old state and control metrics')
    require(removal.record(branch)==old[matches[0]],'exact old recorded metrics')
    arm=branch['ablation'];expected=deepcopy(control['initial']);observer=Observer(source['initial']['units'])
    for row in source['rows'][:sel['t0']]:observer.accept(row['physical'])
    removed,exported=removal.intervene(expected['units'],expected['raw'],observer)
    expected.update(site_ids=list(observer.alive),removals=removed,energy_export=exported,energy_after=expected['energy_before']-exported,observation=snapshot(expected['units'],observer.alive,16,16,phase='final'))
    expected['copies']=removal.match_copies(source['initial'],expected['units'],observer.alive,expected['observation'],observer.individuals)
    require(expected==arm['initial'],'exact removal initial stock and history')
    recalculated=removal.summarize_arm(arm,sel['offspring_ids'])
    require(all(arm[k]==v for k,v in recalculated.items()),'all old observation metrics')
    return arm


def produce_record(case,sel,control,ablation):
    encoding=case['encoding'];observed=observe_case(case,encoding)[0]
    def metrics(arm):
        if sel is None:
            future=dict.fromkeys(removal.METRICS,0)
            full={k:future[k] for k in removal.METRICS}
            full.update({k:observed['metrics'][k] for k in PHYSICAL})
            full.update(rejected_import=observed['metrics']['rejected_import'],energy_export=0,removals=0)
            return full,future
        future=deepcopy(arm['metrics']);full=deepcopy(future)
        prefix=case['rows'][:sel['t0']];observer=Observer(case['initial']['units'])
        for row in prefix:observer.accept(row['physical'])
        full['births']+=observer.result()['summary']['births'];full['deaths']+=observer.result()['summary']['deaths']
        for k in ('imported','spent'):full[k]+=sum(r['physical'][k] for r in prefix)
        full.update(rejected_import=sum(r['physical']['rejected_import'] for r in prefix+arm['rows']),energy_export=arm['initial']['energy_export'],removals=len(arm['initial']['removals']))
        return full,future
    c,cf=metrics(control);a,af=metrics(ablation)
    for m in (c,a):require(m['final_energy']==192+m['imported']-m['spent']-m['energy_export'],'full window energy ledger')
    return dict(encoding=encoding,seed=case['seed'],source=str(source_location(encoding,case['seed'])),trigger=sel is not None,t0=sel['t0'] if sel else None,remaining=sel['remaining_steps'] if sel else 0,short_window=bool(sel and sel['remaining_steps']<10),applicability={k:sel is not None for k in ('future_window','formation','upper_formation','selected_ancestry')},selection=deepcopy(sel),control_metrics=c,ablation_metrics=a,delta={k:a[k]-c[k] for k in METRICS},control_future_metrics=cf,ablation_future_metrics=af,control_episodes=control['episodes'] if sel else [],ablation_episodes=ablation['episodes'] if sel else [])


def summarize(records):
    index={(r['encoding'],r['seed']):r for r in records}
    require(len(records)==len(index)==100 and set(index)=={(e,s) for e in ENCODINGS for s in SEEDS},'complete hundred policy records')
    def group(rows):
        return dict(n=len(rows),triggers=sum(r['trigger'] for r in rows),no_trigger=sum(not r['trigger'] for r in rows),short_window=sum(r['short_window'] for r in rows),remaining=sum(r['remaining'] for r in rows),**{name+'_totals':{k:sum(r[name+'_metrics'][k] for r in rows) for k in METRICS} for name in ('control','ablation')},delta_totals={k:sum(r['delta'][k] for r in rows) for k in METRICS},positive={k:sum(r['delta'][k]>0 for r in rows) for k in METRICS},negative={k:sum(r['delta'][k]<0 for r in rows) for k in METRICS},tie={k:sum(r['delta'][k]==0 for r in rows) for k in METRICS},paired_persistent10=[dict(control=c,ablation=a,n=sum(r['control_metrics']['persistent10']==c and r['ablation_metrics']['persistent10']==a for r in rows)) for c in (0,1) for a in (0,1)])
    def contrast(e,reference):
        pairs=[dict(seed=s,delta={k:index[e,s]['ablation_metrics'][k]-index[reference,s]['ablation_metrics'][k] for k in METRICS}) for s in SEEDS]
        totals={k:sum(p['delta'][k] for p in pairs) for k in METRICS}
        return dict(encoding=e,reference=reference,n=20,pairs=pairs,totals=totals,mean_delta={k:str(Fraction(v,20)) for k,v in totals.items()},positive={k:sum(p['delta'][k]>0 for p in pairs) for k in METRICS},negative={k:sum(p['delta'][k]<0 for p in pairs) for k in METRICS},tie={k:sum(p['delta'][k]==0 for p in pairs) for k in METRICS},paired_persistent10=[dict(reference=c,encoding=a,n=sum(index[reference,s]['ablation_metrics']['persistent10']==c and index[e,s]['ablation_metrics']['persistent10']==a for s in SEEDS)) for c in (0,1) for a in (0,1)])
    return dict(cases=100,overall=group(records),cells=[dict(encoding=e,**group([index[e,s] for s in SEEDS])) for e in ENCODINGS],north_contrasts=[contrast(e,'north') for e in ENCODINGS[:3]],homogeneous_contrasts=[contrast(e,'homogeneous') for e in ENCODINGS])


def main():
    from scripts.triggered_policy_inputs import bindings,input_paths
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();baseline=dict(removal._steps);records=[];inventory=[]
    meta=dict(status='running',planned_cases=100,planned_triggers=28,planned_new_steps=116,completed_cases=0,completed_triggers=0,new_treatment_steps=0,control_replay_steps=0,reused_treatment_steps=0,new_environment_sources=0,new_independent_initial_worlds=0,time_limit_seconds=SECONDS,storage_limit_bytes=STORAGE)
    def progress():meta.update(completed_cases=len(records),completed_triggers=sum(r['trigger'] for r in records),new_treatment_steps=removal._steps['ablation']-baseline['ablation'],control_replay_steps=removal._steps['control']-baseline['control'],elapsed_seconds=time.monotonic()-started)
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
        census=read('docs/research/results/v4-study-039-design-census.json')['cases'];selections=[]
        for encoding in ENCODINGS:
            for seed in SEEDS:
                budget();case=source_case(encoding,seed);sel=selection(case,encoding)
                expected=next(c for c in census if (c['encoding'],c['seed'])==(encoding,seed))
                require(expected['t0']==(sel['t0'] if sel else None),'frozen first trigger')
                control=ablation=None
                if sel:
                    control=observe_arm(case,sel)
                    if encoding in ('north','homogeneous'):
                        ablation=reuse_arm(case,sel,control);meta['reused_treatment_steps']+=sel['remaining_steps']
                    else:
                        require(encoding in ('east','west'),'fixed new treatment encodings')
                        ablation=removal.run_arm(case,sel,'ablation',budget)
                        branch=dict(selection=sel,control=control,ablation=ablation,delta={k:ablation['metrics'][k]-control['metrics'][k] for k in removal.METRICS})
                        save(OUTPUT/'cases'/f'{encoding}-{seed}.json',branch)
                    selections.append(dict(encoding=encoding,**sel))
                records.append(produce_record(case,sel,control,ablation));progress()
                save(OUTPUT/'records.json',records);save(OUTPUT/'selection.json',selections);save(OUTPUT/'metadata.json',meta);budget()
        require(meta['new_treatment_steps']==116 and meta['control_replay_steps']==0 and meta['reused_treatment_steps']==274 and meta['completed_triggers']==28,'fixed complete budgets')
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
