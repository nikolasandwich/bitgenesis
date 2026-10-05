"""Study037 inline-fallback verifier: independent components, chains and events.

No production scientific import and no physical simulation or replay.
"""
from copy import deepcopy
from pathlib import Path
import json
import time
from bitgenesis.v4.structure_audit import reconstruct

OUTPUT=Path('data/v4-study-037')
FLAGS=('occupied','material_match','genetic_match','whole_component','root_descendant','all_new','post_birth','selected_ancestry')
FAILURES=('missing','material','program','component','ancestry_root','original_member','pass')
METRICS=('upper_new_copy','upper_selected_post_copy','double_new')


def require(value,message):
    if not value:raise ValueError(message)


def same(actual,expected,message):
    require(json.dumps(actual,sort_keys=True,allow_nan=False)==json.dumps(expected,sort_keys=True,allow_nan=False),message)


def lineage(identity,people,selected):
    chain=[];cursor=identity
    while cursor is not None:
        require(type(cursor) is int and 0<=cursor<len(people),'identity bounds')
        chain.append(cursor);parent=people[cursor]['parent']
        require(parent is None or type(parent) is int and 0<=parent<cursor,'ancestry order')
        cursor=parent
    hit=next((i for i in chain if i in selected),None)
    return chain[-1],chain if hit is None else chain[:chain.index(hit)+1],hit


def spans(values,start):
    result=[]
    for tick,value in enumerate(values,start):
        if value:
            if result and result[-1]['end']==tick-1:
                result[-1]['end']=tick;result[-1]['length']+=1;result[-1]['right_censored']=tick==32
            else:result.append(dict(start=tick,end=tick,length=1,right_censored=tick==32))
    return result


def predicates(row):
    upper=row['slots'][0]
    return dict(upper_new_copy=upper['new_copy'],upper_selected_post_copy=upper['new_copy'] and upper['post_birth'] and upper['selected_ancestry'],double_new=row['new_copy_count']>=2)


def witness(identity,people):
    p=people[identity]
    return dict(identity=identity,site=p['site'],material=p['material'],program=p['program'],birth_tick=p['birth_tick'],parent=p['parent'])


def inspect_state(units,ids,tick,people,selection,source,births,deaths):
    observation=reconstruct(units,ids,16,16,'final');groups=observation['components']['material']
    sites_by_id={i:s for s,i in enumerate(ids) if i is not None};by_member={i:g for g in groups for i in g}
    template=[source['initial']['units'][s] for s in (85,86)];slots=[]
    for sites in ([85,86],[101,102],[117,118]):
        members=[ids[s] for s in sites];present=all(i is not None for i in members)
        ancestry=[None if i is None else lineage(i,people,set(selection['offspring_ids'])) for i in members]
        slot=dict(sites=sites,identities=members,roots=[None if a is None else a[0] for a in ancestry],
            materials=[None if units[s] is None else units[s]['material'] for s in sites],
            programs=[None if units[s] is None else units[s]['program'] for s in sites],
            birth_ticks=[None if i is None else people[i]['birth_tick'] for i in members],
            selected_chains=[[] if a is None else a[1] for a in ancestry],
            selected_ancestors=[None if a is None else a[2] for a in ancestry],
            components=[None if i is None else dict(identities=by_member[i],sites=sorted(sites_by_id[j] for j in by_member[i])) for i in members])
        material=present and all(units[s]['material']==t['material'] for s,t in zip(sites,template))
        genetic=material and all(units[s]['program']==t['program'] for s,t in zip(sites,template))
        whole=present and set(by_member[members[0]])==set(members)
        root=present and all(a[0] in (0,1) for a in ancestry)
        new=present and all(i not in (0,1) for i in members)
        post=present and all(people[i]['birth_tick']>selection['t0'] for i in members)
        chosen=present and all(a[2] is not None for a in ancestry)
        slot.update(dict(zip(FLAGS,(present,material,genetic,whole,root,new,post,chosen))))
        slot.update(copy=genetic and whole and root,new_copy=genetic and whole and root and new);slots.append(slot)
    upper=slots[0];first=next((name for name,flag in zip(FAILURES,('occupied','material_match','genetic_match','whole_component','root_descendant','all_new')) if not upper[flag]),'pass')
    connected=set()
    for c in upper['components']:
        if c is not None:connected.update(set(c['sites']) & {101,102})
    return dict(tick=tick,slots=slots,upper_failure=first,connector_sites=sorted(connected),new_copy_count=sum(s['new_copy'] for s in slots),births=births,deaths=deaths)


def verify_case(branch,source):
    selection=branch['selection'];arm=branch['ablation'];people=arm['final']['individuals'];t0=selection['t0']
    require(selection['mode']=='random-direction' and selection['exchange'] is False,'fixed direction branch')
    same([r['tick'] for r in arm['rows']],list(range(t0+1,33)),'future horizon')
    initial=arm['initial'];diagnostic=inspect_state(initial['units'],initial['site_ids'],t0,people,selection,source,[],[])
    rows=[];previous=initial['site_ids'];events=[];before=diagnostic
    for r in arm['rows']:
        p=r['physical'];birth_ids=[r['site_ids'][v['target']] for v in p['material']['proposals'] if v['reason']=='formed'];death_ids=[previous[s] for s in p['material']['dissolved']]
        births=[witness(i,people) for i in sorted(birth_ids)];deaths=[witness(i,people) for i in sorted(death_ids)]
        same(sorted(birth_ids),[i for i,h in enumerate(people) if h['birth_tick']==r['tick']],'event births/history')
        same(sorted(death_ids),[i for i,h in enumerate(people) if h['death_tick']==r['tick']],'event deaths/history')
        row=inspect_state(p['units'],r['site_ids'],r['tick'],people,selection,source,births,deaths)
        a,b=predicates(before),predicates(row)
        for metric in ('upper_new_copy','double_new'):
            if a[metric]!=b[metric]:events.append(dict(tick=r['tick'],metric=metric,direction='enter' if b[metric] else 'exit',before=deepcopy(before),after=deepcopy(row),births=births,deaths=deaths))
        rows.append(row);before=row;previous=r['site_ids']
    episodes={m:spans([predicates(r)[m] for r in rows],t0+1) for m in METRICS}
    counts=[r['new_copy_count'] for r in rows];oldspans=[[e['start'],e['end']] for e in episodes['double_new']]
    same(counts,arm['new_copy_counts'],'036 future counts');same(oldspans,arm['episodes'],'036 double intervals')
    return dict(selection=selection,diagnostic=diagnostic,rows=rows,transitions=events,episodes=episodes,
        longest={m:max((e['length'] for e in es),default=0) for m,es in episodes.items()},
        prior036=dict(new_copy_counts=counts,episodes=oldspans,matched=True))


def summarize(records):
    def group(chosen):
        rows=[row for r in chosen for row in r['rows']]
        result=dict(n=len(chosen),saved_steps=len(rows),slot_steps=3*len(rows),
            flags={f:sum(slot[f] for row in rows for slot in row['slots']) for f in FLAGS},
            slots=[dict(sites=sites,**{f:sum(row['slots'][j][f] for row in rows) for f in FLAGS}) for j,sites in enumerate(([85,86],[101,102],[117,118]))],
            upper_failure={f:sum(row['upper_failure']==f for row in rows) for f in FAILURES},
            connector_steps=sum(bool(row['connector_sites']) for row in rows),births=sum(len(row['births']) for row in rows),deaths=sum(len(row['deaths']) for row in rows),
            transitions={m:{d:sum(t['metric']==m and t['direction']==d for r in chosen for t in r['transitions']) for d in ('enter','exit')} for m in ('upper_new_copy','double_new')})
        result['persistence']={m:dict(steps=sum(predicates(row)[m] for row in rows),episodes=sum(len(r['episodes'][m]) for r in chosen),right_censored=sum(e['right_censored'] for r in chosen for e in r['episodes'][m]),cases_ever=sum(r['longest'][m]>0 for r in chosen),cases_persistent10=sum(r['longest'][m]>=10 for r in chosen),longest=max((r['longest'][m] for r in chosen),default=0)) for m in METRICS}
        return result
    return dict(cells=[dict(genotype=g,category=c,**group([r for r in records if r['selection']['genotype']==g and r['selection']['category']==c])) for g in ('homogeneous','heterogeneous') for c in ('short_window','remaining_conditional')],overall=group(records))


def main():
    from scripts.reformation_barrier_inputs import bindings,input_paths,read,digest,ROOT
    started=time.monotonic();proof_path=OUTPUT/'independent-verification.json';require(not proof_path.exists(),'proof exists')
    paths=[];bound={};before={};done=0
    names=('metadata.json','records.json','summary.json')
    def budget():
        require(time.monotonic()-started<600,'verification time budget')
        require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'verification storage budget')
    try:
        errors={};paths=input_paths(errors);same(errors,{},'inventory errors');bound=bindings();same(paths,sorted(bound),'inventory coverage')
        before={n:digest(OUTPUT/n) for n in names};meta=read(OUTPUT/'metadata.json')
        same(sorted(p.name for p in OUTPUT.iterdir()),sorted(names),'exclusive output names')
        for k,v in dict(status='complete',planned_cases=20,completed_cases=20,saved_steps=274,slot_steps=822,diagnostic_states=20,new_simulation_steps=0,new_environment_sources=0,new_independent_initial_worlds=0,time_limit_seconds=600,storage_limit_bytes=134217728).items():same(meta[k],v,'metadata '+k)
        same(meta['input_sha256'],bound,'initial input bindings');same(meta['input_sha256_after'],bound,'final input bindings')
        same(meta['output_sha256'],{n:before[n] for n in ('records.json','summary.json')},'output hashes')
        require(0<=meta['elapsed_seconds']<600,'production duration');same(meta['input_paths'],paths,'metadata inventory')
        # Independently select from the complete saved 58 rather than helper's filter.
        cohort=read(ROOT/'records.json');require(len(cohort)==58,'prior full cohort')
        wanted=[(i,r) for i,r in enumerate(cohort) if r['selection']['mode']=='random-direction'];same(len(wanted),20,'20 selected branches')
        records=[]
        for index,record in wanted:
            budget();branch=read(ROOT/'cases'/f'branch-{index:03d}.json');same(branch['selection'],record['selection'],'branch selection')
            records.append(verify_case(branch,read(branch['selection']['source'])));done+=1
        same(sum(len(r['rows']) for r in records),274,'future denominator')
        same([sum(r['selection']['genotype']==g for r in records) for g in ('homogeneous','heterogeneous')],[11,9],'program groups')
        same(sum(r['selection']['category']=='short_window' for r in records),8,'short windows retained')
        same(read(OUTPUT/'records.json'),records,'all records and transitions');same(read(OUTPUT/'summary.json'),summarize(records),'all summary cells')
        same(bindings(),bound,'inputs unchanged');same({n:digest(OUTPUT/n) for n in names},before,'outputs unchanged');budget()
        proof=dict(status='verified',cases=20,saved_steps=274,slot_steps=822,diagnostic_states=20,new_simulation_steps=0,
            review_mode='inline fallback; parent independent algorithm, not fresh independent author',input_files=len(bound),
            input_sha256=bound,input_sha256_after=bound,files_sha256=before,verifier_sha256=digest(Path(__file__)),
            elapsed_seconds=time.monotonic()-started,scope='pairwise components, full root and selected ancestry, physical event witnesses, all slots and transitions; no physical simulation')
        payload=json.dumps(proof,indent=2,allow_nan=False)+'\n'
        require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())+len(payload.encode())<134217728,'proof budget')
        with proof_path.open('x') as f:f.write(payload)
        print('verified 20 cases, 274 future rows, 822 slots; inline fallback algorithm')
    except BaseException as error:
        failure=OUTPUT/'verification-failure.json'
        if OUTPUT.is_dir() and not failure.exists():
            after={};errors={}
            for p in paths:
                try:after[p]=digest(p)
                except Exception as exc:errors[p]=repr(exc)
            with failure.open('x') as f:json.dump(dict(status='failed',error=repr(error),completed_cases=done,input_sha256=bound,input_sha256_after=after,input_read_errors=errors,files_sha256_before=before),f,indent=2)
        raise


if __name__=='__main__':main()
