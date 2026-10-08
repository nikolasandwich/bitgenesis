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
OUTPUT=Path('data/v4-study-023')

def run_case(source):
    seed,mode,exchange=source['seed'],source['mode'],source['exchange']
    identity(seed,mode,exchange)
    require(mode=='random-direction' and source['config']==CONFIG and len(source['rows'])==32,'fixed saved source')
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
    require(all(case[k]==source[k] for k in ('seed','mode','exchange')) and case['mode']=='random-direction','paired source identity')
    old,new=metrics(source),metrics(case)
    return dict(seed=case['seed'],exchange=case['exchange'],homogeneous=old,heterogeneous=new,delta={k:new[k]-old[k] for k in METRICS})


def summarize(records):
    require(len(records)==40,'full40 pairs');keys=[]
    for r in records:
        key=(r['seed'],r['exchange']);require(type(r['seed']) is int and type(r['exchange']) is bool and key in GRID,'strict identity');keys.append(key)
        for name in ('homogeneous','heterogeneous','delta'):
            require(set(r[name])==set(METRICS) and all(type(v) is int for v in r[name].values()),'exact integer metrics')
        for name in ('homogeneous','heterogeneous'):
            v=r[name];require(all(n>=0 for n in v.values()) and all(v[k] in (0,1) for k in METRICS[:4]),'valid nonnegative metrics')
            require(v['genetic_persistent10']<=v['genetic_ever']<=v['material_ever'] and v['genetic_persistent10']<=v['material_persistent10']<=v['material_ever'] and v['longest_genetic']<=32,'nested events')
        require(r['delta']=={k:r['heterogeneous'][k]-r['homogeneous'][k] for k in METRICS},'paired deltas')
    require(len(set(keys))==40,'unique complete grid')
    cells=[];contrasts=[]
    for genotype,exchange in product(('homogeneous','heterogeneous'),(False,True)):
        rows=[r[genotype] for r in records if r['exchange'] is exchange];totals={k:sum(r[k] for r in rows) for k in METRICS}
        cells.append(dict(genotype=genotype,exchange=exchange,n=20,totals=totals,means={k:str(Fraction(v,20)) for k,v in totals.items()}))
    for exchange in (False,True):
        rows=[r['delta'] for r in records if r['exchange'] is exchange]
        contrasts.append(dict(exchange=exchange,n=20,mean_delta={k:str(Fraction(sum(r[k] for r in rows),20)) for k in METRICS},positive={k:sum(r[k]>0 for r in rows) for k in METRICS},negative={k:sum(r[k]<0 for r in rows) for k in METRICS},tie={k:sum(r[k]==0 for r in rows) for k in METRICS}))
    return dict(cells=cells,contrasts=contrasts)


def main():
    from scripts.program_direction_inputs import bindings,source_cases,read,save,digest
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);(OUTPUT/'cases').mkdir();started=time.monotonic();records=[]
    meta=dict(status='running',planned_cases=40,completed_cases=0,new_simulation_steps=0,new_environment_sources=0,reused_environment_sources=20,new_independent_initial_worlds=0,artificial_initial_state=True,
              git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),time_limit_seconds=600,storage_limit_bytes=134217728)
    def hashes():return {str(p.relative_to(OUTPUT)):digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p.name!='metadata.json'}
    def budget():require(time.monotonic()-started<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'bounded execution')
    try:
        before=bindings();meta['input_sha256']=before;save(OUTPUT/'metadata.json',meta);save(OUTPUT/'results.json',records)
        for path in source_cases():
            budget();source=read(path);case=run_case(source);save(OUTPUT/'cases'/path.name,case);records.append(pair_record(case,source))
            meta.update(completed_cases=len(records),new_simulation_steps=32*len(records));save(OUTPUT/'results.json',records);save(OUTPUT/'metadata.json',meta)
        save(OUTPUT/'summary.json',summarize(records));meta['input_sha256_after']=bindings();require(before==meta['input_sha256_after'],'unchanged inputs')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256=hashes());budget();save(OUTPUT/'metadata.json',meta)
        print(json.dumps({k:v for k,v in meta.items() if 'sha256' not in k}))
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc),elapsed_seconds=time.monotonic()-started)
        try:
            meta['input_sha256_after']=bindings()
            if meta.get('input_sha256')!=meta['input_sha256_after']:meta['finalization_error']='inputs changed during failure'
        except BaseException as err:meta['finalization_error']=repr(err)
        try:meta['output_sha256']=hashes()
        except BaseException as err:meta['output_hash_error']=repr(err)
        save(OUTPUT/'metadata.json',meta);raise

if __name__=='__main__':main()
