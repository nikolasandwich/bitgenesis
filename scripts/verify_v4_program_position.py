"""Study038 inline-fallback dictionary physics and direct-template verification."""
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import json
import time
from bitgenesis.v4.exchange_branch_audit import physical_step
from bitgenesis.v4.structure_audit import reconstruct
from scripts.verify_v4_structure_copies import recount,translated_equal,points,intervals

OUTPUT=Path('data/v4-study-038')
ENCODINGS=('east','west','south','north','homogeneous')
METRICS=('genetic_ever','genetic_persistent10','longest_genetic','material_ever','material_persistent10','longest_material','new_genetic_ever','new_genetic_persistent10','longest_new_genetic','births','deaths','living','imported','rejected_import','spent','final_energy','nonzero_births','north_births')
CONFIG=dict(width=16,height=16,capacity=64,leak=1,bond_cost=1,threshold=16,construction_cost=4,copy_cost=1,mutation_per_thousand=0)


def require(value,message):
    if not value:raise ValueError(message)


def same(a,b,message):
    require(json.dumps(a,sort_keys=True,allow_nan=False)==json.dumps(b,sort_keys=True,allow_nan=False),message)


def program(encoding,identity):
    require(encoding in ENCODINGS and identity in (0,1),'program identity')
    result=[0]*4
    if encoding!='homogeneous':result[ENCODINGS.index(encoding)]=identity+1
    return result


def new_counts(initial,rows,parents):
    roots=[]
    for i,p in enumerate(parents):
        require(p is None or type(p) is int and 0<=p<i,'parent order')
        roots.append(i if p is None else roots[p])
    template=points(initial['site_ids'],initial['units'],[0,1],16);result=[]
    for row in rows:
        ids=row['site_ids'];units=row['physical']['units'];groups=reconstruct(units,ids,16,16,'final')['components']['material']
        result.append(sum(len(g)==2 and all(i not in (0,1) and roots[i] in (0,1) for i in g) and translated_equal(template,points(ids,units,g,16)) for g in groups))
    return result


def observe_case(case,encoding):
    same(case['config'],CONFIG,'config');require(case['exchange'] is False and case['mode']=='random-direction','source cohort')
    initial=case['initial'];same(initial['units'][85]['program'],program(encoding,0),'template A');same(initial['units'][86]['program'],program(encoding,1),'template B')
    copies=recount(initial,case['rows'],case['final']);same(copies,case['copy_parents'],'old or new copy observations')
    require(len(copies)==1 and copies[0]['anchor_members']==[0,1],'single original template')
    series=dict(genetic_copy_count=copies[0]['series']['descendant_genetic'],material_copy_count=copies[0]['series']['descendant_material'],new_genetic_copy_count=new_counts(initial,case['rows'],case['final']['parents']))
    episodes={k:intervals(v) for k,v in series.items()};metrics={}
    for prefix,key in (('genetic','genetic_copy_count'),('material','material_copy_count'),('new_genetic','new_genetic_copy_count')):
        longest=max((b-a+1 for a,b in episodes[key]),default=0)
        metrics.update({prefix+'_ever':int(longest>0),prefix+'_persistent10':int(longest>=10),'longest_'+prefix:longest})
    formed=[p for r in case['rows'] for p in r['physical']['material']['proposals'] if p['reason']=='formed']
    metrics.update(births=len(formed),deaths=sum(len(r['physical']['material']['dissolved']) for r in case['rows']),living=sum(u is not None for u in case['final']['units']),imported=sum(r['physical']['imported'] for r in case['rows']),rejected_import=sum(r['physical']['rejected_import'] for r in case['rows']),spent=sum(r['physical']['spent'] for r in case['rows']),final_energy=sum(u['energy'] for u in case['final']['units'] if u is not None),nonzero_births=sum(p['material']!=0 for p in formed),north_births=sum(p['direction']==3 for p in formed))
    for row in case['rows']:
        physical=row['physical'];same(physical['energy_after'],physical['energy_before']+physical['imported']-physical['spent'],'step energy')
        same([v+int(u is not None) for v,u in zip(physical['raw'],physical['units'])],[v+int(u is not None) for v,u in zip(initial['raw'],initial['units'])],'local stock')
    same(192+metrics['imported']-metrics['spent'],metrics['final_energy'],'cumulative energy')
    s=case['summary'];same(s['genetic_counts'],series['genetic_copy_count'],'old genetic counts');same(s['longest'],metrics['longest_genetic'],'old longest');same(s['persistent10'],bool(metrics['genetic_persistent10']),'old persistent')
    return dict(encoding=encoding,seed=case['seed'],mode='random-direction',exchange=False,series=series,episodes=episodes,metrics=metrics,
        first_new_genetic_copy_tick=next((i for i,c in enumerate(series['new_genetic_copy_count'],1) if c>=1),None),
        formations=[dict(direction=d,material=m,count=sum(p['direction']==d and p['material']==m for p in formed)) for d in range(4) for m in range(4)])


def verify_case(source,encoding,on_step=lambda:None):
    require(encoding in ENCODINGS[:3],'new encodings only');same(source['config'],CONFIG,'source config')
    units=[None]*256;raw=[0]*256;ids=[None]*256;parents=[None,None,None]
    for i,(site,material) in enumerate(((85,0),(86,0),(204,3))):
        units[site]=dict(material=material,energy=64,program=program(encoding,i) if i<2 else [3]*4);ids[site]=i
    for site in (101,102,117,118):raw[site]=1
    initial=dict(tick=0,units=deepcopy(units),raw=raw.copy(),site_ids=ids.copy(),observation=reconstruct(units,ids,16,16,'final'))
    rows=[];births=deaths=0
    for tick,tape in enumerate(source['rows'],1):
        same(tape['tick'],tick,'source tick');physical=physical_step(units,raw,CONFIG,tape['physical'],False);on_step()
        prior=ids.copy()
        for site in physical['material']['dissolved']:require(ids[site] is not None,'living death');ids[site]=None;deaths+=1
        for p in physical['material']['proposals']:
            if p['reason']=='formed':
                require(ids[p['target']] is None and prior[p['source']] is not None,'formation parent and vacancy')
                ids[p['target']]=len(parents);parents.append(prior[p['source']]);births+=1
        units,raw=physical['units'],physical['raw'];rows.append(dict(tick=tick,physical=physical,site_ids=ids.copy(),observation=reconstruct(units,ids,16,16,'final')))
    same(len(rows),32,'fixed horizon');final=dict(tick=32,units=units,raw=raw,site_ids=ids.copy(),parents=parents)
    copies=recount(initial,rows,final);copy=copies[0];longest=copy['longest']['descendant_genetic']
    summary=dict(seed=source['seed'],mode='random-direction',exchange=False,steps=32,births=births,deaths=deaths,living=sum(u is not None for u in units),initial_energy=192,final_energy=sum(u['energy'] for u in units if u is not None),imported=sum(r['physical']['imported'] for r in rows),rejected_import=sum(r['physical']['rejected_import'] for r in rows),spent=sum(r['physical']['spent'] for r in rows),proposed=1024,initial_mass=7,final_mass=sum(raw)+sum(u is not None for u in units),genetic_counts=copy['series']['descendant_genetic'],episodes=copy['episodes']['descendant_genetic'],longest=longest,persistent10=longest>=10,ever=longest>0)
    case=dict(encoding=encoding,seed=source['seed'],mode='random-direction',exchange=False,config=CONFIG.copy(),initial=initial,rows=rows,final=final,copy_parents=copies,summary=summary)
    case['record']=observe_case(case,encoding);return case


def summarize(records):
    same([(r['encoding'],r['seed']) for r in records],[(e,s) for e in ENCODINGS for s in range(120000,120020)],'100 ordered records')
    indexed={(r['encoding'],r['seed']):r['metrics'] for r in records}
    cells=[]
    for encoding in ENCODINGS:
        totals={m:sum(indexed[encoding,s][m] for s in range(120000,120020)) for m in METRICS}
        cells.append(dict(encoding=encoding,n=20,totals=totals,means={m:str(Fraction(v,20)) for m,v in totals.items()}))
    def contrasts(encodings,ref):
        result=[]
        for encoding in encodings:
            pairs=[dict(seed=s,delta={m:indexed[encoding,s][m]-indexed[ref,s][m] for m in METRICS}) for s in range(120000,120020)]
            totals={m:sum(p['delta'][m] for p in pairs) for m in METRICS}
            result.append(dict(encoding=encoding,reference=ref,n=20,pairs=pairs,totals=totals,mean_delta={m:str(Fraction(v,20)) for m,v in totals.items()},positive={m:sum(p['delta'][m]>0 for p in pairs) for m in METRICS},negative={m:sum(p['delta'][m]<0 for p in pairs) for m in METRICS},tie={m:sum(p['delta'][m]==0 for p in pairs) for m in METRICS}))
        return result
    return dict(cells=cells,north_contrasts=contrasts(ENCODINGS[:3],'north'),homogeneous_contrasts=contrasts(ENCODINGS,'homogeneous'))


def main():
    from scripts.program_position_inputs import bindings,input_paths,read,digest,source_path
    proof_path=OUTPUT/'independent-verification.json';require(not proof_path.exists(),'proof exists')
    started=time.monotonic();before={};bound={};steps=completed=observed=0;paths=[]
    names=('metadata.json','records.json','summary.json')+tuple(f'cases/{e}-{s}.json' for e in ENCODINGS[:3] for s in range(120000,120020))
    def budget():
        require(time.monotonic()-started<600,'verification time budget')
        require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'verification storage budget')
    def counted():
        nonlocal steps
        steps+=1;budget()
    try:
        paths=input_paths();bound=bindings();same(paths,sorted(bound),'input inventory')
        before={n:digest(OUTPUT/n) for n in names};meta=read(OUTPUT/'metadata.json')
        same(meta['input_sha256'],bound,'production before binding');same(meta['input_sha256_after'],bound,'production after binding')
        same(meta['input_paths'],paths,'production inventory');same(meta['input_read_errors'],{},'input read errors')
        same(meta['output_sha256'],{n:before[n] for n in names if n!='metadata.json'},'all saved outputs')
        for k,v in dict(status='complete',planned_cases=60,completed_cases=60,completed_observation_cases=40,new_full_world_steps=1920,reused_observation_steps=1280,new_environment_sources=0,reused_environment_sources=20,new_independent_initial_worlds=0,artificial_initial_state=True,time_limit_seconds=600,storage_limit_bytes=134217728).items():same(meta[k],v,'metadata '+k)
        require(0<=meta['elapsed_seconds']<600,'production elapsed budget')
        same(sorted(p.name for p in OUTPUT.iterdir()),sorted(['metadata.json','records.json','summary.json','cases']),'output inventory')
        same(sorted(p.name for p in (OUTPUT/'cases').iterdir()),sorted(n.split('/')[1] for n in names if n.startswith('cases/')),'case inventory')
        records=[]
        for encoding in ENCODINGS:
            for seed in range(120000,120020):
                budget();source=read(source_path(seed,encoding))
                if encoding in ENCODINGS[:3]:
                    case=verify_case(source,encoding,counted)
                    same(read(OUTPUT/'cases'/f'{encoding}-{seed}.json'),case,'full independent new case')
                    records.append(case['record']);completed+=1
                else:records.append(observe_case(source,encoding));observed+=1
        same(steps,1920,'new-case verification steps');same(observed,40,'old observation cases')
        same(read(OUTPUT/'records.json'),records,'100 records');same(read(OUTPUT/'summary.json'),summarize(records),'five cells and contrasts')
        same(bindings(),bound,'inputs unchanged');same({n:digest(OUTPUT/n) for n in names},before,'outputs unchanged');budget()
        proof=dict(status='verified',new_cases=completed,reused_cases=observed,observed_steps=3200,new_case_physics_replay_steps=steps,old_case_physics_replay_steps=0,new_environment_sources=0,input_files=len(bound),input_sha256=bound,input_sha256_after=bound,files_sha256=before,verifier_sha256=digest(Path(__file__)),elapsed_seconds=time.monotonic()-started,review_mode='inline fallback; parent separate algorithm, not fresh independent author',scope='dictionary physics + independent identity/union-find/direct translation; all100 observations and paired contrasts')
        payload=json.dumps(proof,indent=2,allow_nan=False)+'\n'
        require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())+len(payload.encode())<134217728,'proof size budget')
        with proof_path.open('x') as f:f.write(payload)
        print('verified60 new cases/1920 dictionary steps and40 old observations; inline fallback')
    except BaseException as error:
        failure=OUTPUT/'verification-failure.json'
        if OUTPUT.is_dir() and not failure.exists():
            after={};errors={}
            for p in paths:
                try:after[p]=digest(p)
                except Exception as exc:errors[p]=repr(exc)
            with failure.open('x') as f:json.dump(dict(status='failed',error=repr(error),new_case_physics_replay_steps=steps,completed_cases=completed,old_observations=observed,input_sha256=bound,input_sha256_after=after,input_read_errors=errors,files_sha256_before=before),f,indent=2)
        raise


if __name__=='__main__':main()
