"""Study043 independent dictionary replay; parent inline fallback author."""
from copy import deepcopy
from pathlib import Path
from types import FunctionType
from time import monotonic
import subprocess
import math
from scripts import verify_v4_founder_removal as v
from scripts.verify_v4_triggered_policy import source_path, observe_arm, make_record
from scripts.middle_north_policy_inputs import bindings,input_paths,read,save,digest
ENCODINGS=('east','west','south','north','homogeneous')
METRICS=v.METRICS+('rejected_import','energy_export','removals')
ROOT=Path('data/v4-study-043')

def north_physics(units,raw,config,tape,exchange):
    actual=deepcopy(tape)
    actual['directions'][101]=actual['directions'][102]=3
    return v.physical_step(units,raw,config,actual,exchange)

def direction_mask(case,t0):
    return [dict(tick=r['tick'],site=s,original_direction=r['physical']['directions'][s],new_direction=3,changed=r['physical']['directions'][s]!=3) for r in case['rows'][t0:] for s in (101,102)]

def verify_new(case,sel,on_step=lambda:None):
    scope=dict(v.verify_arm.__globals__,physical_step=north_physics)
    fn=FunctionType(v.verify_arm.__code__,scope,argdefs=v.verify_arm.__defaults__)
    return fn(case,sel,'ablation',on_step)

def check_case(enc,seed,on_step=lambda:None):
    path=source_path(enc,seed);case=read(path)
    v.same((case['seed'],case['mode'],case['exchange']),(seed,'random-direction',False),'source identity')
    selected=v.choose_case(case,'homogeneous' if enc=='homogeneous' else 'heterogeneous',path)
    sel=selected if selected['eligible'] else None
    old=new=None;branch=None
    if sel:
        if enc in ('east','west'):oldpath=f'data/v4-study-039/cases/{enc}-{seed}.json'
        else:
            matches=[i for i,r in enumerate(read('data/v4-study-036/records.json')) if r['selection']==sel]
            v.same(len(matches),1,'unique old branch');oldpath=f'data/v4-study-036/cases/branch-{matches[0]:03d}.json'
        saved=read(oldpath);v.same(saved['selection'],sel,'old selection')
        old=observe_arm(case,sel,'ablation',saved['ablation']['rows'])
        v.same(old,saved['ablation'],'all old physics observations and identities')
        new=verify_new(case,sel,on_step)
        v.same(new['initial'],old['initial'],'identical removal initial state')
        branch=dict(selection=sel,control=old,ablation=new,delta={k:new['metrics'][k]-old['metrics'][k] for k in v.METRICS},direction_mask=direction_mask(case,sel['t0']))
    return make_record(enc,seed,case,sel,old,new),branch

def summary(records):
    from fractions import Fraction
    metrics=v.METRICS+('rejected_import','energy_export','removals')
    def signs(deltas):
        return {name:{k:sum((d[k]>0 if name=='positive' else d[k]<0 if name=='negative' else d[k]==0) for d in deltas) for k in metrics} for name in ('positive','negative','tie')}
    def group(rows):
        result=dict(n=len(rows),triggers=sum(bool(r['trigger']) for r in rows),no_trigger=sum(not r['trigger'] for r in rows),short_window=sum(bool(r['short_window']) for r in rows),remaining=sum(r['remaining'] for r in rows))
        for name in ('control','ablation'):
            result[name+'_totals']={k:sum(r[name+'_metrics'][k] for r in rows) for k in metrics}
        result['delta_totals']={k:sum(r['delta'][k] for r in rows) for k in metrics}
        result.update(signs([r['delta'] for r in rows]))
        result['mean_delta']={k:str(Fraction(val,len(rows))) for k,val in result['delta_totals'].items()}
        result['paired_persistent10']=[dict(control=c,ablation=a,n=sum(r['control_metrics']['persistent10']==c and r['ablation_metrics']['persistent10']==a for r in rows)) for c in (0,1) for a in (0,1)]
        return result
    groups={e:sorted((r for r in records if r['encoding']==e),key=lambda r:r['seed']) for e in ENCODINGS}
    for e,rows in groups.items():v.same([r['seed'] for r in rows],list(range(120000,120020)),'complete encoding denominator')
    def contrast(e,ref):
        pairs=[];table={(c,a):0 for c in (0,1) for a in (0,1)}
        for x,y in zip(groups[e],groups[ref]):
            pairs.append(dict(seed=x['seed'],delta={k:x['delta'][k]-y['delta'][k] for k in metrics}))
            table[y['ablation_metrics']['persistent10'],x['ablation_metrics']['persistent10']]+=1
        totals={k:sum(p['delta'][k] for p in pairs) for k in metrics}
        return dict(encoding=e,reference=ref,n=20,estimand='difference_in_differences',paired_persistent10_basis='new_policy',pairs=pairs,totals=totals,mean_delta={k:str(Fraction(val,20)) for k,val in totals.items()},**signs([p['delta'] for p in pairs]),paired_persistent10=[dict(reference=c,encoding=a,n=table[c,a]) for c,a in table])
    return dict(cases=100,overall=group(records),cells=[dict(encoding=e,**group(groups[e])) for e in ENCODINGS],north_contrasts=[contrast(e,'north') for e in ENCODINGS[:3]],homogeneous_contrasts=[contrast(e,'homogeneous') for e in ENCODINGS])

def main():
    proof=ROOT/'independent-verification.json'
    v.require(not proof.exists() and not (ROOT/'verification-failure.json').exists(),'exclusive verification')
    start=monotonic();result=dict(status='running',author='parent inline fallback independent algorithm',physical_steps=0,completed_cases=0,reused_treatment_observations=0,control_replay_steps=0)
    baseline={};before={};records=[];errors={}
    def budget():v.require(monotonic()-start<600 and sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())<134217728,'verification budget')
    def step():result['physical_steps']+=1;budget()
    try:
        paths=input_paths(errors)
        for p in paths:
            try:before[p]=digest(p)
            except Exception as exc:errors[p]=repr(exc)
        result['input_sha256']=before;result['input_read_errors']=errors
        v.same(errors,{},'source readable');v.same(before,bindings(),'complete binding')
        baseline={str(p.relative_to(ROOT)):digest(p) for p in ROOT.rglob('*.json')}
        meta=read(ROOT/'metadata.json');v.same(meta['status'],'complete','producer complete')
        for key in ('input_sha256','input_sha256_after'):v.same(meta[key],before,'producer '+key)
        v.require(math.isfinite(meta['elapsed_seconds']) and 0<=meta['elapsed_seconds']<600,'producer duration')
        v.same(meta['time_limit_seconds'],600,'time cap');v.same(meta['storage_limit_bytes'],134217728,'storage cap')
        fixed=dict(planned_cases=100,planned_triggers=28,planned_new_steps=390,completed_cases=100,completed_triggers=28,new_treatment_steps=390,control_replay_steps=0,reused_treatment_steps=390,new_environment_sources=0,new_independent_initial_worlds=0,new_steps_by_encoding=dict(east=70,west=46,south=0,north=133,homogeneous=141))
        for k,val in fixed.items():v.same(meta[k],val,'metadata '+k)
        v.same(meta['input_paths'],paths,'inventory paths')
        v.same(meta['input_inventory_errors'],{},'inventory errors');v.same(meta['input_read_errors'],{},'read errors')
        v.require(len(meta['git_commit'])==40 and all(c in '0123456789abcdef' for c in meta['git_commit']),'producer commit')
        selections=[];expected_cases=[]
        oldrecords={(r['encoding'],r['seed']):r for r in read('data/v4-study-039/records.json')}
        for enc in ENCODINGS:
            for seed in range(120000,120020):
                budget();record,branch=check_case(enc,seed,step)
                old=oldrecords[enc,seed]
                v.same(record['control_metrics'],old['ablation_metrics'],'old full policy metrics')
                v.same(record['control_future_metrics'],old['ablation_future_metrics'],'old future metrics')
                if branch:
                    name=f'cases/{enc}-{seed}.json';expected_cases.append(name)
                    v.same(read(ROOT/name),branch,'entire independent new branch')
                    selections.append(dict(encoding=enc,**record['selection']))
                    result['reused_treatment_observations']+=record['remaining']
                records.append(record);result['completed_cases']+=1
        v.same(read(ROOT/'records.json'),records,'all100 records');v.same(read(ROOT/'summary.json'),summary(records),'all summaries')
        v.same(read(ROOT/'selection.json'),selections,'28 selections')
        v.same(result['physical_steps'],390,'390 independent physical steps')
        v.same(result['reused_treatment_observations'],390,'390 old saved observations')
        v.same(sorted(baseline),sorted(expected_cases+['metadata.json','records.json','summary.json','selection.json']),'exact output inventory')
        after=bindings();result['input_sha256_after']=after;v.same(before,after,'inputs unchanged')
        v.same(baseline,{p:digest(ROOT/p) for p in baseline},'producer files unchanged')
        v.same(meta['output_sha256'],{p:h for p,h in baseline.items() if p!='metadata.json'},'producer outputs binding')
        result.update(status='verified',files_sha256=baseline,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    except BaseException as exc:
        result.update(status='failed',error=repr(exc));raise
    finally:
        result['elapsed_seconds']=monotonic()-start
        result['input_sha256_after']={p:digest(p) for p in before if Path(p).is_file()}
        save(proof if result['status']=='verified' else ROOT/'verification-failure.json',result)
if __name__=='__main__':main()
