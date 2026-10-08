"""Paired heterogeneous initial programs on already saved full environment tapes."""
from dataclasses import asdict
from fractions import Fraction
from itertools import product
from pathlib import Path
import json,subprocess,time
from bitgenesis.v4.hereditary_growing import step
from bitgenesis.v4.heredity import HeritableUnit
from bitgenesis.v4.lineage import Observer
from bitgenesis.v4.structure import snapshot
from scripts.analyze_v4_structure_copies import analyze,episodes
from scripts.run_v4_copy_ablation import identity,validate_summary,require
from scripts.run_v4_copy_control import CONFIG,normalize

GRID=tuple(product(range(120000,120020),(False,True)))
METRICS=('genetic_persistent10','genetic_ever','material_persistent10','material_ever','longest_genetic','births','deaths','living','imported','spent','final_energy','nonzero_births','north_births')
OUTPUT=Path('data/v4-study-025')
MODES=('random-feed','random-both')

def run_case(source):
    seed,mode,exchange=source['seed'],source['mode'],source['exchange']
    identity(seed,mode,exchange)
    require(mode in MODES and source['config']==CONFIG and len(source['rows'])==32,'fixed saved source')
    inputs=source['rows']
    units = [None] * 256
    raw = [0] * 256
    for site, material in ((85, 0), (86, 0), (204, 3)):
        units[site] = HeritableUnit(material,64,(0,0,0,1) if site==85 else (0,0,0,2) if site==86 else (3,3,3,3))
    for site in (101, 102, 117, 118):
        raw[site] = 1

    def serialized():
        return normalize([None if u is None else asdict(u) for u in units])

    observer = Observer(serialized())
    initial = dict(tick=0, units=serialized(), raw=list(raw), site_ids=list(observer.alive),
                   observation=snapshot(serialized(), observer.alive, 16, 16, phase='final'))
    rows = []
    for tick, tape in enumerate(inputs, 1):
        require(tape['tick']==tick,'source tick order')
        physical_source=tape['physical']
        proposals=[v['proposed'] for v in physical_source['driven']['inputs']]
        directions=list(physical_source['directions'])
        tickets=[tuple(v) for v in physical_source['mutation_tickets']]
        units, raw, record = step(units, raw, proposals=proposals, directions=directions,
                                  mutation_tickets=tickets, exchange=exchange, **CONFIG)
        physical = normalize(dict(tick=tick, units=serialized(), raw=list(raw),
                                  energy=sum(u.energy for u in units if u is not None),
                                  directions=directions, mutation_tickets=tickets, **record))
        observer.accept(physical)
        rows.append(dict(tick=tick, site_ids=list(observer.alive), physical=physical,
                         observation=snapshot(physical['units'], observer.alive, 16, 16, phase='final')))
    lineage = observer.result()
    final = dict(tick=32, units=serialized(), raw=list(raw), site_ids=list(observer.alive),
                 parents=[v['parent'] for v in lineage['individuals']])
    copies = analyze(initial, rows, final)
    require(len(copies) == 1 and copies[0]['component'] == 0 and copies[0]['anchor_members'] == [0, 1],
            'fixed eligible original parent')
    copy = copies[0]
    longest = copy['longest']['descendant_genetic']
    summary = dict(seed=seed, mode=mode, exchange=exchange, steps=32,
                   births=lineage['summary']['births'], deaths=lineage['summary']['deaths'],
                   living=sum(u is not None for u in units), initial_energy=192,
                   final_energy=sum(u.energy for u in units if u is not None),
                   imported=sum(r['physical']['imported'] for r in rows),
                   rejected_import=sum(r['physical']['rejected_import'] for r in rows),
                   spent=sum(r['physical']['spent'] for r in rows), proposed=1024,
                   initial_mass=7, final_mass=sum(raw) + sum(u is not None for u in units),
                   genetic_counts=copy['series']['descendant_genetic'],
                   episodes=copy['episodes']['descendant_genetic'], longest=longest,
                   persistent10=longest >= 10, ever=longest > 0)
    validate_summary(summary)
    return dict(seed=seed, mode=mode, exchange=exchange, config=dict(CONFIG), initial=initial,
                rows=rows, final=final, copy_parents=copies, summary=summary)



def metrics(case):
    validate_summary(case['summary']);s=case['summary'];copy=case['copy_parents'][0]
    material=copy['series']['descendant_material'];require(len(material)==32,'all material observations')
    spans=episodes(material);longest=max((b-a+1 for a,b in spans),default=0)
    formed=[p for r in case['rows'] for p in r['physical']['material']['proposals'] if p['reason']=='formed']
    return dict(genetic_persistent10=int(s['persistent10']),genetic_ever=int(s['ever']),material_persistent10=int(longest>=10),material_ever=int(longest>0),
                longest_genetic=s['longest'],**{k:s[k] for k in ('births','deaths','living','imported','spent','final_energy')},
                nonzero_births=sum(p['material']!=0 for p in formed),north_births=sum(p['direction']==3 for p in formed))


def pair_record(case,source):
    require(all(case[k]==source[k] for k in ('seed','mode','exchange')) and case['mode'] in MODES,'paired source identity')
    old,new=metrics(source),metrics(case)
    return dict(seed=case['seed'],mode=case['mode'],exchange=case['exchange'],homogeneous=old,heterogeneous=new,delta={k:new[k]-old[k] for k in METRICS})


def summarize(records):
    from scripts.run_v4_program_direction import summarize as summarize_direction
    require(len(records)==80 and all(r['mode'] in MODES for r in records),'full80 mode pairs')
    return [dict(mode=mode,**summarize_direction([r for r in records if r['mode']==mode])) for mode in MODES]

def main():
    from scripts.program_feed_inputs import bindings,source_cases,read,save,digest,input_paths
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);(OUTPUT/'cases').mkdir();started=time.monotonic();records=[]
    meta=dict(status='running',planned_cases=80,completed_cases=0,new_simulation_steps=0,new_environment_sources=0,reused_environment_sources=20,new_independent_initial_worlds=0,artificial_initial_state=True,
              git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),time_limit_seconds=600,storage_limit_bytes=268435456)
    def hashes():return {str(p.relative_to(OUTPUT)):digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p.name!='metadata.json'}
    def budget():require(time.monotonic()-started<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<268435456,'bounded execution')
    inventory=[]
    def input_hashes(error_key):
        values={};meta[error_key]={}
        for path in inventory:
            try:values[path]=digest(path)
            except BaseException as exc:meta[error_key][path]=repr(exc)
        return values
    try:
        meta['input_inventory_errors']={}
        inventory=input_paths(meta['input_inventory_errors'])
        meta['input_paths']=inventory
        meta['input_sha256']=input_hashes('input_read_errors_before')
        save(OUTPUT/'metadata.json',meta);save(OUTPUT/'results.json',records)
        before=bindings();require(before==meta['input_sha256'],'validated initial inputs')
        for path in source_cases():
            budget();source=read(path);case=run_case(source);save(OUTPUT/'cases'/path.name,case);records.append(pair_record(case,source))
            meta.update(completed_cases=len(records),new_simulation_steps=32*len(records));save(OUTPUT/'results.json',records);save(OUTPUT/'metadata.json',meta)
        save(OUTPUT/'summary.json',summarize(records));meta['input_sha256_after']=bindings();require(before==meta['input_sha256_after'],'unchanged inputs')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256=hashes());budget();save(OUTPUT/'metadata.json',meta);budget()
        print(json.dumps({k:v for k,v in meta.items() if 'sha256' not in k}))
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc),elapsed_seconds=time.monotonic()-started)
        try:
            meta['input_sha256_after']=bindings()
            if meta.get('input_sha256')!=meta['input_sha256_after']:meta['finalization_error']='inputs changed during failure'
        except BaseException as err:
            meta['finalization_error']=repr(err);meta['input_sha256_after']=input_hashes('input_read_errors')
        try:meta['output_sha256']=hashes()
        except BaseException as err:meta['output_hash_error']=repr(err)
        save(OUTPUT/'metadata.json',meta);raise

if __name__=='__main__':main()
