"""Study037 passive barriers and transitions on saved removal states."""
from copy import deepcopy
from pathlib import Path
import subprocess
import time

from bitgenesis.v4.structure import snapshot

OUTPUT = Path('data/v4-study-037')
SITES = ((85,86),(101,102),(117,118))
FLAGS = ('occupied','material_match','genetic_match','whole_component','root_descendant','all_new','post_birth','selected_ancestry')
FAILURES = ('missing','material','program','component','ancestry_root','original_member','pass')
METRICS = ('upper_new_copy','upper_selected_post_copy','double_new')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def lineage(identity, people, selected):
    chain=[]; current=identity; selected_ancestor=None
    while current is not None:
        require(type(current) is int and 0 <= current < len(people) and current not in chain,'valid ancestry')
        chain.append(current)
        if current in selected and selected_ancestor is None:
            selected_ancestor=current; selected_chain=list(chain)
        parent=people[current]['parent']
        require(parent is None or type(parent) is int and 0 <= parent < current,'ordered parent')
        current=parent
    return chain[-1], selected_chain if selected_ancestor is not None else chain, selected_ancestor


def witness(p):
    return dict(identity=p['id'],site=p['site'],material=p['material'],program=list(p['program']),birth_tick=p['birth_tick'],parent=p['parent'])


def observe(tick, units, ids, people, template, selected, t0, diagnostic=False):
    groups=snapshot(units,ids,16,16,phase='final')['components']['material']
    sites_by_id={i:s for s,i in enumerate(ids) if i is not None}
    components={i:dict(identities=list(g),sites=sorted(sites_by_id[j] for j in g)) for g in groups for i in g}
    slots=[]
    for sites in SITES:
        members=[ids[s] for s in sites]
        roots=[];chains=[];ancestors=[]
        for i in members:
            r,c,a=(None,[],None) if i is None else lineage(i,people,selected)
            roots.append(r);chains.append(c);ancestors.append(a)
        occupied=all(i is not None for i in members)
        material=occupied and all(units[s]['material']==t['material'] for s,t in zip(sites,template))
        genetic=material and all(units[s]['program']==t['program'] for s,t in zip(sites,template))
        whole=occupied and all(set(components[i]['identities'])==set(members) for i in members)
        root=occupied and all(r in (0,1) for r in roots)
        new=occupied and all(i not in (0,1) for i in members)
        slots.append(dict(sites=list(sites),identities=members,roots=roots,
            materials=[None if units[s] is None else units[s]['material'] for s in sites],
            programs=[None if units[s] is None else list(units[s]['program']) for s in sites],
            birth_ticks=[None if i is None else people[i]['birth_tick'] for i in members],
            selected_chains=chains,selected_ancestors=ancestors,components=[components.get(i) for i in members],
            occupied=occupied,material_match=material,genetic_match=genetic,whole_component=whole,
            root_descendant=root,all_new=new,post_birth=occupied and all(people[i]['birth_tick']>t0 for i in members),
            selected_ancestry=occupied and all(a is not None for a in ancestors),copy=genetic and whole and root,new_copy=genetic and whole and root and new))
    upper=slots[0]
    failure=next((name for name,flag in zip(FAILURES,FLAGS[:6]) if not upper[flag]),'pass')
    connector=sorted({s for c in upper['components'] if c for s in c['sites'] if s in SITES[1]})
    return dict(tick=tick,slots=slots,upper_failure=failure,connector_sites=connector,
                new_copy_count=sum(s['new_copy'] for s in slots),
                births=[] if diagnostic else [witness(p) for p in people if p['birth_tick']==tick],
                deaths=[] if diagnostic else [witness(p) for p in people if p['death_tick']==tick])


def values(row):
    upper=row['slots'][0]
    return dict(upper_new_copy=upper['new_copy'],upper_selected_post_copy=upper['new_copy'] and upper['post_birth'] and upper['selected_ancestry'],double_new=row['new_copy_count']>=2)


def spans(observations):
    result=[];start=None;last=None
    for tick,active in observations:
        if last is not None:require(tick==last+1,'consecutive observations')
        if active and start is None:start=tick
        if not active and start is not None:
            result.append(dict(start=start,end=tick-1,length=tick-start,right_censored=False));start=None
        last=tick
    if start is not None:result.append(dict(start=start,end=last,length=last-start+1,right_censored=True))
    return result


def analyze_case(branch, source):
    selection=deepcopy(branch['selection']);arm=branch['ablation'];t0=selection['t0']
    require(selection['mode']=='random-direction' and selection['exchange'] is False,'fixed direction cohort')
    require(selection['category'] in ('short_window','remaining_conditional'),'fixed strata')
    require(source['initial']['site_ids'][85:87]==[0,1],'original template identities')
    template=[source['initial']['units'][s] for s in SITES[0]]
    people=arm['final']['individuals'];selected=selection['offspring_ids']
    initial=arm['initial']
    require(initial['tick']==t0,'diagnostic tick')
    diagnostic=observe(t0,initial['units'],initial['site_ids'],people,template,selected,t0,True)
    rows=[];transitions=[];before=diagnostic
    for expected,saved in enumerate(arm['rows'],t0+1):
        require(saved['tick']==expected,'ordered future ticks')
        row=observe(expected,saved['physical']['units'],saved['site_ids'],people,template,selected,t0)
        require([p['identity'] for p in row['births']]==[p['id'] for p in saved['births']],'saved births agree')
        require([p['identity'] for p in row['deaths']]==sorted(saved['deaths']),'saved natural deaths agree')
        for metric in ('upper_new_copy','double_new'):
            if values(before)[metric]!=values(row)[metric]:
                transitions.append(dict(tick=expected,metric=metric,direction='enter' if values(row)[metric] else 'exit',before=deepcopy(before),after=deepcopy(row),births=deepcopy(row['births']),deaths=deepcopy(row['deaths'])))
        rows.append(row);before=row
    require(len(rows)==selection['remaining_steps']==32-t0,'fixed future window')
    episodes={m:spans([(r['tick'],values(r)[m]) for r in rows]) for m in METRICS}
    counts=[r['new_copy_count'] for r in rows];double=[[e['start'],e['end']] for e in episodes['double_new']]
    require(counts==arm['new_copy_counts'] and double==arm['episodes'],'036 per-case agreement')
    return dict(selection=selection,diagnostic=diagnostic,rows=rows,transitions=transitions,episodes=episodes,
                longest={m:max((e['length'] for e in episodes[m]),default=0) for m in METRICS},
                prior036=dict(new_copy_counts=counts,episodes=double,matched=True))


def summarize(records):
    def group(chosen):
        rows=[r for c in chosen for r in c['rows']];slots=[s for r in rows for s in r['slots']]
        events=[e for c in chosen for e in c['transitions']]
        return dict(n=len(chosen),saved_steps=len(rows),slot_steps=len(slots),
            flags={f:sum(s[f] for s in slots) for f in FLAGS},
            slots=[dict(sites=list(sites),**{f:sum(r['slots'][i][f] for r in rows) for f in FLAGS}) for i,sites in enumerate(SITES)],
            upper_failure={f:sum(r['upper_failure']==f for r in rows) for f in FAILURES},
            connector_steps=sum(bool(r['connector_sites']) for r in rows),births=sum(len(r['births']) for r in rows),deaths=sum(len(r['deaths']) for r in rows),
            transitions={m:{d:sum(e['metric']==m and e['direction']==d for e in events) for d in ('enter','exit')} for m in ('upper_new_copy','double_new')},
            persistence={m:dict(steps=sum(values(r)[m] for r in rows),episodes=sum(len(c['episodes'][m]) for c in chosen),right_censored=sum(e['right_censored'] for c in chosen for e in c['episodes'][m]),cases_ever=sum(c['longest'][m]>0 for c in chosen),cases_persistent10=sum(c['longest'][m]>=10 for c in chosen),longest=max((c['longest'][m] for c in chosen),default=0)) for m in METRICS})
    return dict(cells=[dict(genotype=g,category=k,**group([r for r in records if r['selection']['genotype']==g and r['selection']['category']==k])) for g in ('homogeneous','heterogeneous') for k in ('short_window','remaining_conditional')],overall=group(records))


def main():
    from scripts.reformation_barrier_inputs import bindings,input_paths,read,save,digest,source_branches
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();records=[];inventory=[]
    meta=dict(status='running',planned_cases=20,completed_cases=0,saved_steps=0,slot_steps=0,diagnostic_states=0,new_simulation_steps=0,new_environment_sources=0,new_independent_initial_worlds=0,time_limit_seconds=600,storage_limit_bytes=134217728)
    def budget():require(time.monotonic()-started<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'bounded execution')
    def hashes():return {str(p.relative_to(OUTPUT)):digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p.name!='metadata.json'}
    def input_hashes(key):
        result={};meta[key]={}
        for p in inventory:
            try:result[p]=digest(p)
            except BaseException as e:meta[key][p]=repr(e)
        return result
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        meta['input_inventory_errors']={};inventory=input_paths(meta['input_inventory_errors']);meta['input_paths']=inventory
        meta['input_sha256']=input_hashes('input_read_errors_before');save(OUTPUT/'metadata.json',meta);save(OUTPUT/'records.json',records)
        before=bindings();require(before==meta['input_sha256'],'validated initial inputs')
        sources=list(source_branches());require(len(sources)==20,'all20 direction branches')
        for path in sources:
            budget();branch=read(path);records.append(analyze_case(branch,read(branch['selection']['source'])))
            meta.update(completed_cases=len(records),saved_steps=sum(len(r['rows']) for r in records),slot_steps=3*sum(len(r['rows']) for r in records),diagnostic_states=len(records),elapsed_seconds=time.monotonic()-started)
            save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta);budget()
        require(meta['saved_steps']==274 and meta['slot_steps']==822,'fixed observation denominator')
        require([sum(r['selection']['genotype']==g for r in records) for g in ('homogeneous','heterogeneous')]==[11,9],'fixed programs')
        require(sum(r['selection']['category']=='short_window' for r in records)==8,'all short windows')
        save(OUTPUT/'summary.json',summarize(records));meta['input_sha256_after']=bindings();require(before==meta['input_sha256_after'],'unchanged inputs')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256=hashes());budget();save(OUTPUT/'metadata.json',meta);budget()
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
