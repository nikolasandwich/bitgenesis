"""Study039 independent dictionary continuation and saved-state observation.

Parent inline fallback author; no production scientific imports. Existing verified
physical rows are read through an adapter, never simulated again.
"""
from copy import deepcopy
from pathlib import Path
from types import FunctionType
from time import monotonic
import json
import subprocess
from scripts import verify_v4_founder_removal as v
from scripts.triggered_policy_inputs import bindings,read,save,digest

ENCODINGS=('east','west','south','north','homogeneous')
ROOT=Path('data/v4-study-039')

def source_path(enc,seed):
    if enc in ENCODINGS[:3]:return f'data/v4-study-038/cases/{enc}-{seed}.json'
    number='023' if enc=='north' else '019'
    return f'data/v4-study-{number}/cases/seed-{seed}-random-direction-exchange-false.json'

def saved_physics(rows):
    remaining=iter(rows)
    def observe(units,raw,config,tape,exchange):
        p=deepcopy(next(remaining)['physical'])
        v.same(sum(u['energy'] for u in units if u is not None),p['energy_before'],'saved pre-energy')
        v.same(p['tick'],tape['tick'],'saved tick')
        for key in ('directions','mutation_tickets'):
            v.same(p[key],tape[key],'saved tape '+key)
        v.same([i['proposed'] for i in p['driven']['inputs']],[i['proposed'] for i in tape['driven']['inputs']],'saved proposals')
        v.same([n+int(u is not None) for n,u in zip(raw,units)],[n+int(u is not None) for n,u in zip(p['raw'],p['units'])],'saved local stock')
        return p
    return observe

def observe_arm(case,sel,name,rows):
    # A private globals mapping preserves the independent verifier algorithm and
    # avoids mutating its module or calling even one old physical step.
    scope=dict(v.verify_arm.__globals__,physical_step=saved_physics(rows))
    fn=FunctionType(v.verify_arm.__code__,scope,argdefs=v.verify_arm.__defaults__)
    return fn(case,sel,name)

def full_metrics(case,sel,arm):
    t=sel['t0'] if sel else 32
    physical=[r['physical'] for r in case['rows'][:t]]+([r['physical'] for r in arm['rows']] if sel else [])
    final=arm['final'] if sel else case['final']
    m=deepcopy(arm['metrics']) if sel else dict.fromkeys(v.METRICS,0)
    m.update(births=sum(sum(p['reason']=='formed' for p in r['material']['proposals']) for r in physical),deaths=sum(len(r['material']['dissolved']) for r in physical),living=sum(u is not None for u in final['units']),final_energy=sum(u['energy'] for u in final['units'] if u is not None),imported=sum(r['imported'] for r in physical),spent=sum(r['spent'] for r in physical),rejected_import=sum(r['rejected_import'] for r in physical),energy_export=arm['initial']['energy_export'] if sel else 0,removals=len(arm['initial']['removals']) if sel else 0)
    v.same(m['final_energy'],sum(u['energy'] for u in case['initial']['units'] if u is not None)+m['imported']-m['spent']-m['energy_export'],'full energy ledger')
    return m

def independently_check_case(encoding,seed,on_step=lambda:None,budget=lambda:None):
    path=source_path(encoding,seed);case=read(path)
    v.same((case['seed'],case['mode'],case['exchange']),(seed,'random-direction',False),'source identity')
    # Complete saved source observation, including every no-trigger case.
    selected=v.choose_case(case,'homogeneous' if encoding=='homogeneous' else 'heterogeneous',path)
    sel=selected if selected['eligible'] else None
    control=ablation=None
    if sel:
        control=observe_arm(case,sel,'control',case['rows'][sel['t0']:])
        if encoding in ('east','west'):
            saved=read(ROOT/'cases'/f'{encoding}-{seed}.json')
            ablation=v.verify_arm(case,sel,'ablation',on_step)
            v.same(saved['selection'],sel,'new selection')
            v.same(saved['control'],control,'new control saved observations')
            v.same(saved['ablation'],ablation,'new full independent ablation')
            v.same(saved['delta'],{m:ablation['metrics'][m]-control['metrics'][m] for m in v.METRICS},'new branch differences')
        else:
            records=read('data/v4-study-036/records.json')
            matches=[i for i,r in enumerate(records) if r['selection']==sel]
            v.same(len(matches),1,'exact original selection mapping')
            old=read(f'data/v4-study-036/cases/branch-{matches[0]:03d}.json')
            ablation=observe_arm(case,sel,'ablation',old['ablation']['rows'])
            v.same(old['control'],control,'old full control match')
            v.same(old['ablation'],ablation,'old complete ablation observed reconstruction')
            v.same(old['selection'],sel,'old selection')
            for name,arm in [('control',control),('ablation',ablation)]:
                v.same(records[matches[0]][name+'_metrics'],arm['metrics'],'old archived record metrics')
    budget()
    return case,sel,control,ablation

def make_record(encoding,seed,case,sel,control,ablation):
    c=full_metrics(case,sel,control);a=full_metrics(case,sel,ablation)
    return dict(encoding=encoding,seed=seed,source=source_path(encoding,seed),trigger=sel is not None,t0=sel['t0'] if sel else None,remaining=32-sel['t0'] if sel else 0,short_window=sel is not None and sel['t0']>22,applicability={k:sel is not None for k in ('future_window','formation','upper_formation','selected_ancestry')},selection=sel,control_metrics=c,ablation_metrics=a,delta={k:a[k]-c[k] for k in c},control_future_metrics=control['metrics'] if sel else dict.fromkeys(v.METRICS,0),ablation_future_metrics=ablation['metrics'] if sel else dict.fromkeys(v.METRICS,0),control_episodes=control['episodes'] if sel else [],ablation_episodes=ablation['episodes'] if sel else [])

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
        result['paired_persistent10']=[dict(control=c,ablation=a,n=sum(r['control_metrics']['persistent10']==c and r['ablation_metrics']['persistent10']==a for r in rows)) for c in (0,1) for a in (0,1)]
        return result
    groups={e:sorted((r for r in records if r['encoding']==e),key=lambda r:r['seed']) for e in ENCODINGS}
    for e,rows in groups.items():v.same([r['seed'] for r in rows],list(range(120000,120020)),'complete encoding denominator')
    def contrast(e,ref):
        pairs=[];table={(c,a):0 for c in (0,1) for a in (0,1)}
        for x,y in zip(groups[e],groups[ref]):
            pairs.append(dict(seed=x['seed'],delta={k:x['ablation_metrics'][k]-y['ablation_metrics'][k] for k in metrics}))
            table[y['ablation_metrics']['persistent10'],x['ablation_metrics']['persistent10']]+=1
        totals={k:sum(p['delta'][k] for p in pairs) for k in metrics}
        return dict(encoding=e,reference=ref,n=20,pairs=pairs,totals=totals,mean_delta={k:str(Fraction(val,20)) for k,val in totals.items()},**signs([p['delta'] for p in pairs]),paired_persistent10=[dict(reference=c,encoding=a,n=table[c,a]) for c,a in table])
    return dict(cases=100,overall=group(records),cells=[dict(encoding=e,**group(groups[e])) for e in ENCODINGS],north_contrasts=[contrast(e,'north') for e in ENCODINGS[:3]],homogeneous_contrasts=[contrast(e,'homogeneous') for e in ENCODINGS])

def main():
    proof=ROOT/'independent-verification.json'
    v.require(not proof.exists(),'exclusive verification output')
    start=monotonic();result=dict(status='running',author='parent inline fallback independent algorithm',physical_steps=0,completed_cases=0,reused_treatment_observations=0,control_replay_steps=0)
    baseline={};before={};records=[]
    def budget():v.require(monotonic()-start<600 and sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())<134217728,'verification budget')
    def step():result['physical_steps']+=1;budget()
    try:
        before=bindings();result['input_sha256']=before
        baseline={str(p.relative_to(ROOT)):digest(p) for p in ROOT.rglob('*.json')}
        meta=read(ROOT/'metadata.json');v.same(meta['status'],'complete','producer complete');v.same(meta['input_sha256'],before,'producer input binding');v.same(meta['input_sha256_after'],before,'producer final binding')
        for enc in ENCODINGS:
            for seed in range(120000,120020):
                budget();case,sel,c,a=independently_check_case(enc,seed,step,budget)
                records.append(make_record(enc,seed,case,sel,c,a));result['completed_cases']+=1
                if sel and enc in ('north','homogeneous'):result['reused_treatment_observations']+=32-sel['t0']
        v.same(read(ROOT/'records.json'),records,'all100 complete records')
        v.same(read(ROOT/'summary.json'),summary(records),'all policy groups and paired contrasts')
        v.same(read(ROOT/'selection.json'),[dict(encoding=r['encoding'],**r['selection']) for r in records if r['trigger']],'all28 selections')
        v.same(result['physical_steps'],116,'116 independent new replay steps')
        v.same(result['reused_treatment_observations'],274,'274 reused observations')
        after=bindings();result['input_sha256_after']=after;v.same(before,after,'inputs unchanged')
        v.same(baseline,{p:digest(ROOT/p) for p in baseline},'producer outputs unchanged')
        v.same(meta['output_sha256'],{p:h for p,h in baseline.items() if p!='metadata.json'},'producer output binding')
        result.update(status='verified',files_sha256=baseline,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    except BaseException as exc:
        result.update(status='failed',error=repr(exc))
        raise
    finally:
        result['elapsed_seconds']=monotonic()-start
        save(proof,result)
if __name__=='__main__':main()
