"""Study038: fixed program-position interventions on saved environment tapes."""
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
from scripts.analyze_v4_structure_copies import analyze, canonical, episodes, require
from scripts.run_v4_copy_control import CONFIG, normalize
from scripts.run_v4_copy_ablation import validate_summary

ENCODINGS = ('east','west','south','north','homogeneous')
NEW_ENCODINGS = ENCODINGS[:3]
SEEDS = tuple(range(120000,120020))
SERIES = ('genetic_copy_count','material_copy_count','new_genetic_copy_count')
METRICS = tuple(k for name in ('genetic','material','new_genetic')
                for k in (name+'_ever',name+'_persistent10','longest_'+name)) + (
                    'births','deaths','living','imported','rejected_import','spent','final_energy','nonzero_births','north_births')
OUTPUT = Path('data/v4-study-038')
SECONDS = 600
STORAGE = 128*1024**2
_full_world_steps = 0


def initial_units(encoding):
    require(encoding in ENCODINGS, 'fixed encoding')
    units=[None]*256
    for site,material in ((85,0),(86,0),(204,3)):
        program=[material]*4
        if site in (85,86) and encoding!='homogeneous':program[ENCODINGS.index(encoding)]=site-84
        units[site]=dict(material=material,energy=64,program=program)
    return units


def series_summary(counts):
    spans=episodes(counts)
    longest=max((b-a+1 for a,b in spans),default=0)
    return spans,longest,int(longest>0),int(longest>=10)


def new_genetic_counts(initial,rows,final):
    """Count entire translated genetic components with no original member."""
    ids=initial['site_ids'];units=initial['units'];parents=final['parents']
    sites={i:s for s,i in enumerate(ids) if i is not None}
    def fingerprint(group,where,state):
        return canonical([(where[i]%16,where[i]//16,state[where[i]]['material'],tuple(state[where[i]]['program'])) for i in group])
    template=fingerprint((0,1),sites,units)
    roots=[]
    for i,parent in enumerate(parents):
        require(parent is None or type(parent) is int and 0<=parent<i,'ordered ancestry')
        roots.append(i if parent is None else roots[parent])
    result=[]
    for row in rows:
        where={i:s for s,i in enumerate(row['site_ids']) if i is not None}
        result.append(sum(len(group)==2 and not {0,1}.intersection(group) and
                          all(roots[i] in (0,1) for i in group) and
                          fingerprint(group,where,row['physical']['units'])==template
                          for group in row['observation']['components']['material']))
    return result


def observe_case(case,encoding):
    require(encoding in ENCODINGS and case['seed'] in SEEDS and type(case['seed']) is int and
            case['mode']=='random-direction' and case['exchange'] is False and case['config']==CONFIG,'fixed source identity')
    require(case['initial']['units']==initial_units(encoding) and len(case['rows'])==32,'own fixed initial template and horizon')
    copies=analyze(case['initial'],case['rows'],case['final'])
    require(len(copies)==1 and copies[0]['anchor_members']==[0,1], 'fixed original component')
    if 'copy_parents' in case:require(copies==case['copy_parents'],'saved copy observations agree')
    series=dict(zip(SERIES,(copies[0]['series']['descendant_genetic'],copies[0]['series']['descendant_material'],
                           new_genetic_counts(case['initial'],case['rows'],case['final']))))
    spans={};metrics={}
    for name,key in zip(('genetic','material','new_genetic'),SERIES):
        spans[key],metrics['longest_'+name],metrics[name+'_ever'],metrics[name+'_persistent10']=series_summary(series[key])
    observer=Observer(case['initial']['units']);energy=192
    for tick,row in enumerate(case['rows'],1):
        physical=row['physical'];require(row['tick']==physical['tick']==tick,'ordered saved ticks')
        require(physical['energy']==energy+physical['imported']-physical['spent'],'step energy ledger')
        require(physical['material_before']==physical['material_after']==sum(physical['raw'])+sum(u is not None for u in physical['units'])==7,'step mass ledger')
        energy=physical['energy'];observer.accept(physical)
        require(observer.alive==row['site_ids'],'saved identities')
        require(snapshot(physical['units'],observer.alive,16,16,phase='final')==row['observation'],'saved components')
    last=case['rows'][-1]
    require(all(case['final'][k]==last['physical'][k] for k in ('units','raw')) and case['final']['site_ids']==observer.alive and
            case['final']['parents']==[v['parent'] for v in observer.individuals],'final state and ancestry')
    formed=[v for row in case['rows'] for v in row['physical']['material']['proposals'] if v['reason']=='formed']
    metrics.update(births=observer.result()['summary']['births'],deaths=observer.result()['summary']['deaths'],
                   living=sum(u is not None for u in case['final']['units']),final_energy=energy,
                   **{k:sum(r['physical'][k] for r in case['rows']) for k in ('imported','rejected_import','spent')},
                   nonzero_births=sum(v['material']!=0 for v in formed),north_births=sum(v['direction']==3 for v in formed))
    summary=dict(seed=case['seed'],mode='random-direction',exchange=False,steps=32,
                 **{k:metrics[k] for k in ('births','deaths','living','final_energy','imported','rejected_import','spent')},
                 initial_energy=192,proposed=1024,initial_mass=7,final_mass=7,
                 genetic_counts=series[SERIES[0]],episodes=spans[SERIES[0]],longest=metrics['longest_genetic'],
                 persistent10=bool(metrics['genetic_persistent10']),ever=bool(metrics['genetic_ever']))
    validate_summary(summary)
    if 'summary' in case:require(summary==case['summary'],'saved legacy summary agrees')
    result=dict(encoding=encoding,seed=case['seed'],mode='random-direction',exchange=False,series=series,episodes=spans,metrics=metrics,
                first_new_genetic_copy_tick=next((t for t,n in enumerate(series[SERIES[2]],1) if n>=1),None),
                formations=[dict(direction=d,material=m,count=sum(v['direction']==d and v['material']==m for v in formed)) for d in range(4) for m in range(4)])
    return result,copies,summary


def run_case(source,encoding,budget=lambda:None):
    require(encoding in NEW_ENCODINGS,'only new east west south trajectories')
    require(type(source['seed']) is int and source['seed'] in SEEDS and source['mode']=='random-direction' and
            source['exchange'] is False and source['config']==CONFIG and len(source['rows'])==32,'fixed source')
    units=[None if u is None else HeritableUnit(u['material'],u['energy'],tuple(u['program'])) for u in initial_units(encoding)]
    raw=[int(s in (101,102,117,118)) for s in range(256)]
    def serialized():return normalize([None if u is None else asdict(u) for u in units])
    observer=Observer(serialized())
    initial=dict(tick=0,units=serialized(),raw=raw.copy(),site_ids=observer.alive.copy(),observation=snapshot(serialized(),observer.alive,16,16,phase='final'))
    rows=[]
    for tick,row in enumerate(source['rows'],1):
        budget();require(row['tick']==tick,'source tick order');saved=row['physical'];inputs=saved['driven']['inputs']
        require([v['site'] for v in inputs]==list(range(256)), 'ordered original proposals')
        directions=list(saved['directions']);tickets=[tuple(v) for v in saved['mutation_tickets']]
        units,raw,event=step(units,raw,proposals=[v['proposed'] for v in inputs],directions=directions,mutation_tickets=tickets,exchange=False,**CONFIG)
        global _full_world_steps
        _full_world_steps+=1
        physical=normalize(dict(tick=tick,units=serialized(),raw=raw.copy(),energy=sum(u.energy for u in units if u is not None),directions=directions,mutation_tickets=tickets,**event))
        observer.accept(physical)
        rows.append(dict(tick=tick,site_ids=observer.alive.copy(),physical=physical,observation=snapshot(physical['units'],observer.alive,16,16,phase='final')))
        budget()
    final=dict(tick=32,units=serialized(),raw=raw.copy(),site_ids=observer.alive.copy(),parents=[v['parent'] for v in observer.individuals])
    case=dict(encoding=encoding,seed=source['seed'],mode='random-direction',exchange=False,config=dict(CONFIG),initial=initial,rows=rows,final=final)
    case['record'],case['copy_parents'],case['summary']=observe_case(case,encoding)
    return case


def record(case):return deepcopy(case['record'])


def summarize(records):
    require(len(records)==100,'all hundred cases')
    index={(r['encoding'],r['seed']):r for r in records}
    require(len(index)==100 and set(index)=={(e,s) for e in ENCODINGS for s in SEEDS},'complete unique grid')
    for r in records:
        require(r['mode']=='random-direction' and r['exchange'] is False,'fixed record mode')
        require(set(r['metrics'])==set(METRICS) and all(type(v) is int and v>=0 for v in r['metrics'].values()),'complete integer metrics')
        for name,key in zip(('genetic','material','new_genetic'),SERIES):
            require(len(r['series'][key])==32,'complete series')
            spans,longest,ever,persistent=series_summary(r['series'][key])
            require(r['episodes'][key]==spans and [r['metrics'][k] for k in ('longest_'+name,name+'_ever',name+'_persistent10')]==[longest,ever,persistent],'consistent event metrics')
        require(all(n<=g<=m for n,g,m in zip(r['series'][SERIES[2]],r['series'][SERIES[0]],r['series'][SERIES[1]])),'nested counts')
        require(r['first_new_genetic_copy_tick']==next((t for t,n in enumerate(r['series'][SERIES[2]],1) if n),None),'first single new copy')
        require([(f['direction'],f['material']) for f in r['formations']]==[(d,m) for d in range(4) for m in range(4)] and all(type(f['count']) is int and f['count']>=0 for f in r['formations']) and sum(f['count'] for f in r['formations'])==r['metrics']['births'],'complete formation cross table')
    cells=[]
    for e in ENCODINGS:
        totals={k:sum(index[e,s]['metrics'][k] for s in SEEDS) for k in METRICS}
        cells.append(dict(encoding=e,n=20,totals=totals,means={k:str(Fraction(v,20)) for k,v in totals.items()}))
    def contrast(e,reference):
        pairs=[dict(seed=s,delta={k:index[e,s]['metrics'][k]-index[reference,s]['metrics'][k] for k in METRICS}) for s in SEEDS]
        totals={k:sum(p['delta'][k] for p in pairs) for k in METRICS}
        return dict(encoding=e,reference=reference,n=20,pairs=pairs,totals=totals,mean_delta={k:str(Fraction(v,20)) for k,v in totals.items()},
                    positive={k:sum(p['delta'][k]>0 for p in pairs) for k in METRICS},negative={k:sum(p['delta'][k]<0 for p in pairs) for k in METRICS},tie={k:sum(p['delta'][k]==0 for p in pairs) for k in METRICS})
    return dict(cells=cells,north_contrasts=[contrast(e,'north') for e in NEW_ENCODINGS],homogeneous_contrasts=[contrast(e,'homogeneous') for e in ENCODINGS])


def main():
    from scripts.program_position_inputs import bindings,input_paths,read,save,digest,source_path
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False)
    started=time.monotonic();start_steps=_full_world_steps;records=[];inventory=[]
    meta=dict(status='running',planned_cases=60,completed_cases=0,completed_observation_cases=0,new_full_world_steps=0,
              reused_observation_steps=0,new_environment_sources=0,reused_environment_sources=20,new_independent_initial_worlds=0,
              artificial_initial_state=True,time_limit_seconds=SECONDS,storage_limit_bytes=STORAGE)
    def budget():require(time.monotonic()-started<SECONDS and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<STORAGE,'bounded execution')
    def hashes():return {str(p.relative_to(OUTPUT)):digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p.name!='metadata.json'}
    def raw_hashes():
        values={};errors={}
        for path in inventory:
            try:values[str(path)]=digest(path)
            except BaseException as exc:errors[str(path)]=repr(exc)
        meta['input_read_errors']=errors
        return values
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        inventory=input_paths();meta['input_paths']=[str(p) for p in inventory]
        meta['input_sha256']=raw_hashes();save(OUTPUT/'metadata.json',meta);save(OUTPUT/'records.json',records)
        before=bindings();require(before==meta['input_sha256'],'validated initial bindings');(OUTPUT/'cases').mkdir();budget()
        for encoding in ENCODINGS:
            for seed in SEEDS:
                budget();source=read(source_path(seed,encoding))
                if encoding in NEW_ENCODINGS:
                    case=run_case(source,encoding,budget);save(OUTPUT/'cases'/f'{encoding}-{seed}.json',case);records.append(record(case));meta['completed_cases']+=1
                else:
                    records.append(observe_case(source,encoding)[0]);meta['completed_observation_cases']+=1;meta['reused_observation_steps']+=32
                meta.update(new_full_world_steps=_full_world_steps-start_steps,elapsed_seconds=time.monotonic()-started)
                save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta);budget()
        require(_full_world_steps-start_steps==1920 and meta['reused_observation_steps']==1280,'fixed complete step budgets')
        save(OUTPUT/'summary.json',summarize(records));meta['input_sha256_after']=bindings();require(before==meta['input_sha256_after'],'unchanged bound sources')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256=hashes());budget();save(OUTPUT/'metadata.json',meta);budget()
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc),new_full_world_steps=_full_world_steps-start_steps,elapsed_seconds=time.monotonic()-started)
        try:meta['input_sha256_after']=bindings()
        except BaseException as err:meta['finalization_error']=repr(err);meta['input_sha256_after']=raw_hashes()
        if meta.get('input_sha256')!=meta['input_sha256_after']:meta['bindings_changed']=True
        try:meta['output_sha256']=hashes()
        except BaseException as err:meta['output_hash_error']=repr(err)
        save(OUTPUT/'metadata.json',meta)
        raise


if __name__=='__main__':main()
