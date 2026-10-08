"""Study044 parent inline fallback, independent saved-state observer and timing."""
from copy import deepcopy
from pathlib import Path
from time import monotonic
import math
import json
from scripts import verify_v4_reformation_barriers as old
from scripts.policy_component_timing_inputs import bindings,input_paths,capture,read,save,digest
OUTPUT=Path('data/v4-study-044')
ENCODINGS=('east','west','south','north','homogeneous')
ARMS=('control','ablation')
CATEGORIES=('short_window','remaining_conditional')
DELTA_KEYS=('flags','upper_failure','connector_steps','births','deaths','transitions','persistence')

def pair_history(diagnostic,rows):
    states=[diagnostic]+rows;keys=[]
    for state in states:
        key=tuple(state['slots'][0]['identities'])
        if all(i is not None for i in key) and key not in keys:keys.append(key)
    pairs=[]
    for key in keys:
        all_matches=[s for s in states if tuple(s['slots'][0]['identities'])==key]
        matches=[s for s in rows if tuple(s['slots'][0]['identities'])==key]
        def first(chosen):return chosen[0]['tick'] if chosen else None
        pairs.append(dict(identities=list(key),birth_ticks=deepcopy(all_matches[0]['slots'][0]['birth_ticks']),first_copresence_tick=first(all_matches),first_future_copresence_tick=first(matches),first_upper_new_copy_tick=first([s for s in matches if s['slots'][0]['new_copy']]),first_double_new_tick=first([s for s in matches if s['new_copy_count']>=2])))
    changes=[dict(tick=b['tick'],before=deepcopy(a),after=deepcopy(b),births=deepcopy(b['births']),deaths=deepcopy(b['deaths'])) for a,b in zip(states,states[1:]) if a['slots'][0]['identities']!=b['slots'][0]['identities']]
    return dict(upper_identity_changes=changes,upper_identity_pairs=pairs)

def verify_pair(encoding,branch,source):
    old.same(branch['control']['initial'],branch['ablation']['initial'],'paired diagnostic state')
    arms={}
    for name in ARMS:
        result=old.verify_case(dict(selection=branch['selection'],ablation=branch[name]),source)
        result['prior043']=result.pop('prior036')
        result.update(pair_history(result['diagnostic'],result['rows']))
        m=branch[name]['metrics'];old.same(int(result['longest']['double_new']>=10),m['persistent10'],'prior persistence')
        old.same(int(result['longest']['double_new']>0),m['double_new_ever'],'prior ever')
        old.same(result['longest']['double_new'],m['longest_double'],'prior length')
        arms[name]=result
    return dict(encoding=encoding,selection=deepcopy(branch['selection']),arms=arms)

def difference(new,prior):
    if isinstance(new,dict):return {k:difference(new[k],prior[k]) for k in new}
    return new-prior

def summarize(records,index):
    old.same(len(index),100,'full index')
    for e in ENCODINGS:old.same(sorted(r['seed'] for r in index if r['encoding']==e),list(range(120000,120020)),'index seeds')
    old.same([(r['encoding'],r['selection']['seed']) for r in records],[(i['encoding'],i['seed']) for i in index if i['trigger']],'ordered trigger cohort')
    def group(chosen,arm):return old.summarize([r['arms'][arm] for r in chosen])['overall']
    cells=[]
    for e in ENCODINGS:
        for c in CATEGORIES:
            for arm in ARMS:
                chosen=[r for r in records if r['encoding']==e and r['selection']['category']==c]
                cells.append(dict(encoding=e,category=c,arm=arm,policy_denominator=20,triggered_encoding_count=sum(i['trigger'] for i in index if i['encoding']==e),**group(chosen,arm)))
    pairs=[]
    for r in records:
        a=group([r],'ablation');c=group([r],'control')
        pairs.append(dict(encoding=r['encoding'],seed=r['selection']['seed'],delta={k:difference(a[k],c[k]) for k in DELTA_KEYS}))
    return dict(index_cases=100,triggered=len(records),no_trigger=100-len(records),cells=cells,overall={arm:group(records,arm) for arm in ARMS},paired=pairs)

def make_index(policy):
    result=[]
    for r in policy:
        x={k:r[k] for k in ('encoding','seed','trigger','t0','remaining','short_window','source')}
        x.update(branch=f"data/v4-study-043/cases/{r['encoding']}-{r['seed']}.json" if r['trigger'] else None,applicability='observed' if r['trigger'] else 'not_applicable')
        result.append(x)
    return result

def main():
    proof=OUTPUT/'independent-verification.json';old.require(not proof.exists() and not (OUTPUT/'verification-failure.json').exists(),'exclusive proof')
    start=monotonic();result=dict(status='running',completed_cases=0,new_simulation_steps=0,review_mode='parent inline fallback independent algorithm');paths=[];before={}
    def budget():old.require(monotonic()-start<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'audit budget')
    try:
        paths=input_paths();result['input_sha256'],result['input_read_errors_before']=capture(paths);bound=bindings();old.same(result['input_sha256'],bound,'validated inputs')
        names=('metadata.json','records.json','summary.json','index.json');before={n:digest(OUTPUT/n) for n in names}
        old.same(sorted(p.name for p in OUTPUT.iterdir()),sorted(names),'exclusive outputs')
        meta=read(OUTPUT/'metadata.json')
        fixed=dict(status='complete',planned_cases=28,completed_cases=28,planned_arms=56,completed_arms=56,index_cases=100,no_trigger_cases=72,new_environment_sources=0,new_independent_initial_worlds=0,saved_steps=780,slot_steps=2340,diagnostic_states=56,new_simulation_steps=0,time_limit_seconds=600,storage_limit_bytes=134217728)
        for k,val in fixed.items():old.same(meta[k],val,'metadata '+k)
        old.same(meta['input_inventory_errors'],{},'inventory errors');old.same(meta['input_read_errors_before'],{},'source errors')
        old.require(len(meta['git_commit'])==40 and all(c in '0123456789abcdef' for c in meta['git_commit']),'commit hash')
        old.require(math.isfinite(meta['elapsed_seconds']) and 0<=meta['elapsed_seconds']<600,'producer duration')
        old.same(meta['input_sha256'],bound,'before binding');old.same(meta['input_sha256_after'],bound,'after binding');old.same(meta['input_paths'],paths,'inventory')
        old.same(meta['output_sha256'],{n:before[n] for n in names if n!='metadata.json'},'output binding')
        policy=read('data/v4-study-043/records.json');index=make_index(policy);old.same(read(OUTPUT/'index.json'),index,'all100 index including N/A')
        records=[]
        for r,i in zip(policy,index):
            budget()
            if not i['trigger']:continue
            branch=read(i['branch']);old.same(branch['selection'],r['selection'],'selection')
            for arm in ARMS:
                old.same(branch[arm]['metrics'],r[arm+'_future_metrics'],'arm baseline');old.same(branch[arm]['episodes'],r[arm+'_episodes'],'arm episodes')
            records.append(verify_pair(r['encoding'],branch,read(r['source'])));result['completed_cases']+=1
        old.same(sum(len(r['arms'][a]['rows']) for r in records for a in ARMS),780,'full future budget')
        old.same(read(OUTPUT/'records.json'),records,'all records timing predicates and transitions')
        old.same(read(OUTPUT/'summary.json'),summarize(records,index),'all cells and paired deltas')
        old.same(bindings(),bound,'unchanged sources');old.same({n:digest(OUTPUT/n) for n in names},before,'unchanged outputs');budget()
        result.update(status='verified',saved_steps=780,slot_steps=2340,diagnostic_states=56,files_sha256=before)
    except BaseException as exc:result.update(status='failed',error=repr(exc));raise
    finally:
        result['elapsed_seconds']=monotonic()-start
        result['input_sha256_after'],result['input_read_errors_after']=capture(paths)
        if result['status']=='verified':
            try:
                old.same(result['input_sha256_after'],result['input_sha256'],'final bindings');budget()
                old.require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())+len(json.dumps(result).encode())<134217728,'proof storage')
            except BaseException as exc:result.update(status='failed',error=repr(exc));save(OUTPUT/'verification-failure.json',result);raise
        save(proof if result['status']=='verified' else OUTPUT/'verification-failure.json',result)
if __name__=='__main__':main()
