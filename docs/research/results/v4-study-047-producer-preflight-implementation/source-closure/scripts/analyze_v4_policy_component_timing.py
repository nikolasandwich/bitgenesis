"""Study044 read-only paired component/ancestry timing, adapting Study037."""
from copy import deepcopy
from pathlib import Path
import subprocess
import time

from scripts import analyze_v4_reformation_barriers as prior

OUTPUT=Path('data/v4-study-044')
ENCODINGS=('east','west','south','north','homogeneous')
ARMS=('control','ablation')
CATEGORIES=('short_window','remaining_conditional')
DELTA_KEYS=('flags','upper_failure','connector_steps','births','deaths','transitions','persistence')
require=prior.require


def identity_timing(diagnostic, rows):
    """Track every identity change; qualification dates exclude t0+ diagnostics."""
    changes=[];pairs={};before=diagnostic
    for position,row in enumerate([diagnostic]+rows):
        upper=row['slots'][0];key=tuple(upper['identities']);tick=row['tick']
        if position and key!=tuple(before['slots'][0]['identities']):
            changes.append(dict(tick=tick,before=deepcopy(before),after=deepcopy(row),births=deepcopy(row['births']),deaths=deepcopy(row['deaths'])))
        if all(i is not None for i in key):
            if key not in pairs:
                pairs[key]=dict(identities=list(key),birth_ticks=list(upper['birth_ticks']),first_copresence_tick=tick,
                    first_future_copresence_tick=None,first_upper_new_copy_tick=None,first_double_new_tick=None)
            pair=pairs[key]
            if position:
                for field,active in (('first_future_copresence_tick',True),('first_upper_new_copy_tick',upper['new_copy']),('first_double_new_tick',row['new_copy_count']>=2)):
                    if active and pair[field] is None:pair[field]=tick
        before=row
    return changes,list(pairs.values())


def analyze_arm(branch,source,arm_name):
    require(arm_name in ARMS,'known043 arm')
    arm=branch[arm_name]
    record=prior.analyze_case(dict(selection=branch['selection'],ablation=arm),source)
    record['prior043']=record.pop('prior036')
    longest=record['longest']['double_new'];m=arm['metrics']
    require(m['double_new_ever']==int(longest>0) and m['persistent10']==int(longest>=10) and m['longest_double']==longest,'043 persistence agreement')
    record['upper_identity_changes'],record['upper_identity_pairs']=identity_timing(record['diagnostic'],record['rows'])
    return record


def analyze_pair(encoding,branch,source):
    require(encoding in ENCODINGS,'known encoding')
    require(branch['control']['initial']==branch['ablation']['initial'],'identical paired diagnostic states')
    return dict(encoding=encoding,selection=deepcopy(branch['selection']),arms={a:analyze_arm(branch,source,a) for a in ARMS})


def make_index(source_records):
    result=[]
    for record in source_records:
        item={k:deepcopy(record[k]) for k in ('encoding','seed','trigger','t0','remaining','short_window','source')}
        item['branch']=f"data/v4-study-043/cases/{item['encoding']}-{item['seed']}.json" if item['trigger'] else None
        item['applicability']='observed' if item['trigger'] else 'not_applicable'
        result.append(item)
    return result


def group(records):
    return prior.summarize(records)['overall']


def difference(new,old):
    if isinstance(new,dict):
        require(new.keys()==old.keys(),'matching aggregate fields')
        return {k:difference(new[k],old[k]) for k in new}
    return new-old


def summarize(records,index):
    cells=[]
    for encoding in ENCODINGS:
        for category in CATEGORIES:
            for arm in ARMS:
                chosen=[r['arms'][arm] for r in records if r['encoding']==encoding and r['selection']['category']==category]
                cells.append(dict(encoding=encoding,category=category,arm=arm,policy_denominator=20,
                    triggered_encoding_count=sum(i['trigger'] for i in index if i['encoding']==encoding),**group(chosen)))
    paired=[]
    for record in records:
        old,new=(group([record['arms'][a]]) for a in ARMS)
        paired.append(dict(encoding=record['encoding'],seed=record['selection']['seed'],delta={k:difference(new[k],old[k]) for k in DELTA_KEYS}))
    return dict(index_cases=len(index),triggered=sum(i['trigger'] for i in index),no_trigger=sum(not i['trigger'] for i in index),
        cells=cells,overall={a:group([r['arms'][a] for r in records]) for a in ARMS},paired=paired)


def main():
    from scripts.policy_component_timing_inputs import bindings,input_paths,read,save,digest,capture
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();records=[];inventory=[]
    meta=dict(status='running',planned_cases=28,completed_cases=0,planned_arms=56,completed_arms=0,saved_steps=0,slot_steps=0,diagnostic_states=0,
              index_cases=100,no_trigger_cases=72,new_simulation_steps=0,new_environment_sources=0,new_independent_initial_worlds=0,time_limit_seconds=600,storage_limit_bytes=134217728)
    def budget():
        require(time.monotonic()-started<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'bounded execution')
    def hashes():return {str(p.relative_to(OUTPUT)):digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p.name!='metadata.json'}
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        meta['input_inventory_errors']={};inventory=input_paths(meta['input_inventory_errors']);meta['input_paths']=inventory
        meta['input_sha256'],meta['input_read_errors_before']=capture(inventory)
        save(OUTPUT/'metadata.json',meta);save(OUTPUT/'records.json',records)
        before=bindings();require(before==meta['input_sha256'] and not meta['input_inventory_errors'] and not meta['input_read_errors_before'],'validated initial inputs');budget()
        index=make_index(read('data/v4-study-043/records.json'))
        require(len(index)==100 and sum(r['trigger'] for r in index)==28,'full100 index and28 triggered')
        require(all(sorted(r['seed'] for r in index if r['encoding']==e)==list(range(120000,120020)) for e in ENCODINGS),'five complete encoding cohorts')
        require(sum(r['short_window'] for r in index)==10,'retain ten short windows')
        save(OUTPUT/'index.json',index)
        for item in index:
            if not item['trigger']:continue
            budget();branch=read(item['branch']);require(branch['selection']['source']==item['source'] and branch['selection']['seed']==item['seed'],'indexed branch identity')
            records.append(analyze_pair(item['encoding'],branch,read(item['source'])))
            steps=sum(len(r['arms'][a]['rows']) for r in records for a in ARMS)
            meta.update(completed_cases=len(records),completed_arms=2*len(records),saved_steps=steps,slot_steps=3*steps,diagnostic_states=2*len(records),elapsed_seconds=time.monotonic()-started)
            save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta);budget()
        require((meta['completed_cases'],meta['saved_steps'],meta['slot_steps'],meta['diagnostic_states'])==(28,780,2340,56),'fixed complete audit denominator')
        save(OUTPUT/'summary.json',summarize(records,index));meta['input_sha256_after']=bindings();require(before==meta['input_sha256_after'],'unchanged inputs')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256=hashes());budget();save(OUTPUT/'metadata.json',meta);budget()
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc),elapsed_seconds=time.monotonic()-started)
        try:
            meta['input_sha256_after']=bindings()
            if meta.get('input_sha256')!=meta['input_sha256_after']:meta['finalization_error']='inputs changed during failure'
        except BaseException as err:
            meta['finalization_error']=repr(err);meta['input_sha256_after'],meta['input_read_errors']=capture(inventory)
        try:meta['output_sha256']=hashes()
        except BaseException as err:meta['output_hash_error']=repr(err)
        save(OUTPUT/'metadata.json',meta);raise


if __name__=='__main__':main()
