"""Study036 independent dictionary physics, historical identities and components.

This module deliberately does not import the production continuation or Observer.
"""
from copy import deepcopy
from itertools import product
import json
import math
from pathlib import Path
from time import monotonic
from bitgenesis.v4.exchange_branch_audit import physical_step
from bitgenesis.v4.structure_audit import reconstruct

OUTPUT = Path('data/v4-study-036')
IDENTITY = ('genotype', 'mode', 'exchange', 'seed')
GENOTYPES = ('homogeneous', 'heterogeneous')
MODES = ('random-direction', 'random-feed', 'random-both')
GRID = tuple(product(GENOTYPES, MODES, (False, True), range(120000,120020)))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(actual, expected, message):
    require(json.dumps(actual, sort_keys=True, allow_nan=False) ==
            json.dumps(expected, sort_keys=True, allow_nan=False), message)


def intervals(counts, first_tick):
    runs = []
    for tick, count in enumerate(counts, first_tick):
        if count >= 2:
            if runs and runs[-1][1] == tick-1:
                runs[-1][1] = tick
            else:
                runs.append([tick, tick])
    return runs


def chain_to(identity, targets, parents):
    chain = []
    while identity is not None:
        require(type(identity) is int and 0 <= identity < len(parents), 'ancestry bounds')
        chain.append(identity)
        if identity in targets:
            return chain
        parent = parents[identity]
        require(parent is None or type(parent) is int and 0 <= parent < identity, 'acyclic ancestry')
        identity = parent
    return None


def initial_history(units):
    identities, individuals = [], []
    for site, unit in enumerate(units):
        if unit is None:
            identities.append(None)
        else:
            identity = len(individuals)
            identities.append(identity)
            individuals.append(dict(id=identity, site=site, birth_tick=0, death_tick=None,
                parent=None, founder=identity, generation=0, material=unit['material'],
                program=deepcopy(unit['program']), birth_energy=unit['energy'], mutated=False, offspring=0))
    return identities, individuals


def advance_history(ids, people, physical):
    previous = ids.copy()
    tick = physical['tick']
    deaths = []
    for site in physical['material']['dissolved']:
        identity = ids[site]
        require(identity is not None, 'dissolution identity')
        people[identity]['death_tick'] = tick
        deaths.append(identity)
        ids[site] = None
    births = []
    for proposal in physical['material']['proposals']:
        if proposal['reason'] != 'formed':
            continue
        parent = previous[proposal['source']]
        require(parent is not None and ids[proposal['target']] is None, 'formation identity')
        original = people[parent]
        identity = len(people)
        person = dict(id=identity,site=proposal['target'],birth_tick=tick,death_tick=None,
            parent=parent,founder=original['founder'],generation=original['generation']+1,
            material=proposal['material'],program=deepcopy(proposal['child_program']),
            birth_energy=proposal['child_energy'],mutated=proposal['mutated'],offspring=0)
        people.append(person)
        people[parent]['offspring'] += 1
        ids[proposal['target']] = identity
        births.append(deepcopy(person))
    require(all((u is None)==(i is None) for u,i in zip(physical['units'],ids)), 'occupation identities')
    return births, deaths


def match_copies(source, units, ids, people):
    width, height = source['config']['width'], source['config']['height']
    observation = reconstruct(units, ids, width, height, 'final')
    initial = source['initial']
    target = [(s%width,s//width,u['material'],tuple(u['program']))
              for s,u in enumerate(initial['units']) if initial['site_ids'][s] in (0,1)]
    require(len(target)==2, 'two target founders')
    by_id = {i:s for s,i in enumerate(ids) if i is not None}
    copies = []
    for group in observation['components']['material']:
        if len(group)!=2 or any(people[i]['founder'] not in (0,1) for i in group):
            continue
        sites = [by_id[i] for i in group]
        current = {(s%width,s//width,units[s]['material'],tuple(units[s]['program'])) for s in sites}
        a = target[0]
        matched = False
        for b in current:
            dx,dy = b[0]-a[0], b[1]-a[1]
            if {((p[0]+dx)%width,(p[1]+dy)%height,p[2],p[3]) for p in target} == current:
                matched = True
        if matched:
            copies.append(dict(members=group.copy(), sites=sites,
                all_new=all(i not in (0,1) for i in group)))
    return copies


def choose_case(source, genotype, path):
    """Reconstruct all saved identities/components before selecting the first copy."""
    same(source['config'],dict(width=16,height=16,capacity=64,leak=1,bond_cost=1,
        threshold=16,construction_cost=4,copy_cost=1,mutation_per_thousand=0),'fixed source physics')
    require(len(source['rows'])==32, '32 source steps')
    ids, people = initial_history(source['initial']['units'])
    same(ids,source['initial']['site_ids'],'source founder IDs')
    chosen = None
    for tick,row in enumerate(source['rows'],1):
        same(row['tick'],tick,'source tick'); same(row['physical']['tick'],tick,'physical tick')
        advance_history(ids,people,row['physical'])
        same(ids,row['site_ids'],'reconstructed source identities')
        same(row['observation'],reconstruct(row['physical']['units'],ids,16,16,'final'),'source components')
        copies=match_copies(source,row['physical']['units'],ids,people)
        if chosen is None and any(c['all_new'] for c in copies):
            require(ids[85:87]==[0,1], 'live originals at selection')
            new=[c for c in copies if c['all_new']]
            require(len(new)==1 and sorted(new[0]['sites'])==[117,118], 'single lower copy selection')
            category='horizontal_structural_zero' if source['mode']=='random-feed' else 'short_window' if 32-tick<10 else 'remaining_conditional'
            chosen=dict(t0=tick,remaining_steps=32-tick,category=category,original_sites=[85,86],
                offspring_ids=[ids[117],ids[118]],offspring_sites=[117,118],
                energy_export_preview=sum(row['physical']['units'][s]['energy'] for s in (85,86)))
    same(source['final']['parents'],[p['parent'] for p in people],'all historical parents')
    same(source['final']['site_ids'],ids,'final source identities')
    result=dict(genotype=genotype,**{k:source[k] for k in IDENTITY[1:]},source=str(path),eligible=chosen is not None)
    if chosen is not None:
        result.update(chosen)
    return result


def selection_table(sources, saved, budget=lambda:None):
    """Validate the entire 240-source grid, including every negative selection."""
    from scripts.founder_removal_inputs import read
    result=[]
    for index,(genotype,path) in enumerate(sources):
        budget()
        require(index<len(GRID),'no extra source')
        source=read(path)
        same([genotype,source['mode'],source['exchange'],source['seed']],list(GRID[index]),'source grid order')
        result.append(choose_case(source,genotype,path))
    same(len(result),240,'240 sources')
    same(saved,result,'entire 035 selection independently reconstructed')
    eligible=[r for r in result if r['eligible']]
    same(len(eligible),58,'58 selected')
    same([sum(s['category']==c for s in eligible) for c in CATEGORIES],[36,8,14],'36/8/14 strata')
    same(len({s['seed'] for s in eligible}),19,'19 selected seeds')
    same(sum(s['remaining_steps'] for s in eligible),1260,'1260 treatment steps')
    require(all(s['exchange'] is False for s in eligible),'no exchange comparison')
    return result


def ancestry_witness(identity, people, selected):
    parents=[p['parent'] for p in people]
    found=chain_to(identity,set(selected),parents)
    if found is not None:
        return dict(identity=identity,chain=found,selected_ancestor=found[-1])
    trail=[]
    while identity is not None:
        trail.append(identity); identity=parents[identity]
    return dict(identity=trail[0],chain=trail,selected_ancestor=None)


def summarize_arm(arm, selected):
    rows=arm['rows'];t0=arm['initial']['tick'];people=arm['final']['individuals']
    counts=[sum(c['all_new'] for c in row['copies']) for row in rows]
    spans=intervals(counts,t0+1)
    longest=max((end-start+1 for start,end in spans),default=0)
    formation=[];upper=[]
    def born(i):
        p=people[i]
        return dict(identity=i,birth_tick=p['birth_tick'],parent=p['parent'],site=p['site'])
    for row,count in zip(rows,counts):
        require(row['tick']>t0,'future metric ticks')
        if count<2:continue
        copies=[c for c in row['copies'] if c['all_new']]
        births=[born(i) for c in copies for i in c['members'] if people[i]['birth_tick']>t0]
        if births:
            formation.append(dict(tick=row['tick'],copies=[c['members'] for c in copies],births=births))
        for copy in copies:
            if sorted(copy['sites'])==[85,86] and all(people[i]['birth_tick']>t0 for i in copy['members']):
                upper.append(dict(tick=row['tick'],members=copy['members'],sites=copy['sites'],
                    births=[born(i) for i in copy['members']],
                    selected_ancestry=[ancestry_witness(i,people,selected) for i in copy['members']]))
    supported={w['tick'] for w in upper if all(a['selected_ancestor'] is not None for a in w['selected_ancestry'])}
    def persistent(ticks):
        return int(any(b-a+1>=10 for a,b in intervals([2 if r['tick'] in ticks else 0 for r in rows],t0+1)))
    metrics=dict(births=sum(len(r['births']) for r in rows),deaths=sum(len(r['deaths']) for r in rows),
        living=sum(u is not None for u in arm['final']['units']),
        final_energy=sum(u['energy'] for u in arm['final']['units'] if u is not None),
        imported=sum(r['physical']['imported'] for r in rows),spent=sum(r['physical']['spent'] for r in rows),
        new_copy_ever=int(any(counts)),double_new_ever=int(longest>0),persistent10=int(longest>=10),
        longest_double=longest,formation_supported=int(bool(formation)),upper_formed=int(bool(upper)),
        selected_ancestry_supported=int(bool(supported)),formation_persistent10=persistent({w['tick'] for w in formation}),
        upper_persistent10=persistent({w['tick'] for w in upper}),selected_ancestry_persistent10=persistent(supported))
    return dict(metrics=metrics,new_copy_counts=counts,episodes=spans,formation_witnesses=formation,upper_witnesses=upper)


def verify_arm(source, selection, name, on_step=lambda:None):
    t0=selection['t0']; ids,people=initial_history(source['initial']['units'])
    for row in source['rows'][:t0]:
        advance_history(ids,people,row['physical'])
        same(ids,row['site_ids'],'prefix identities including t0 births')
    anchor=source['rows'][t0-1]['physical']
    units,raw=deepcopy(anchor['units']),anchor['raw'].copy()
    before=sum(u['energy'] for u in units if u is not None)
    removals=[]
    if name=='ablation':
        for identity in (0,1):
            site=ids.index(identity)
            removals.append(dict(identity=identity,site=site,energy=units[site]['energy']))
            units[site]=None;raw[site]+=1;ids[site]=None
    exported=sum(r['energy'] for r in removals)
    same([raw[s]+int(units[s] is not None) for s in range(len(units))],
         [anchor['raw'][s]+int(anchor['units'][s] is not None) for s in range(len(units))],'local t0+ material')
    initial=dict(tick=t0,units=deepcopy(units),raw=raw.copy(),site_ids=ids.copy(),parents=[p['parent'] for p in people],
        individuals=deepcopy(people),observation=reconstruct(units,ids,16,16,'final'),removals=removals,
        energy_before=before,energy_export=exported,energy_after=sum(u['energy'] for u in units if u is not None),
        copies=match_copies(source,units,ids,people))
    same(initial['energy_after'],before-exported,'single immediate export')
    mass=sum(raw)+sum(u is not None for u in units)
    rows=[];imported=spent=0
    for old in source['rows'][t0:]:
        tape=old['physical']
        same([r['site'] for r in tape['driven']['inputs']],list(range(256)),'ordered proposed tape')
        physical=physical_step(units,raw,source['config'],tape,selection['exchange'])
        on_step()
        births,deaths=advance_history(ids,people,physical)
        units,raw=physical['units'],physical['raw']
        imported+=physical['imported'];spent+=physical['spent']
        same(physical['energy_after'],before-exported+imported-spent,'future cumulative export once')
        same(physical['material_before'],mass,'step initial mass');same(physical['material_after'],mass,'step final mass')
        observation=reconstruct(units,ids,16,16,'final')
        if name=='control':
            same(physical,old['physical'],'exact control physics suffix')
            same(ids,old['site_ids'],'exact control IDs suffix');same(observation,old['observation'],'exact control observations suffix')
        parents=[p['parent'] for p in people]
        lineage=[dict(identity=i,alive=i in ids,living_descendants=sorted(j for j in ids if j is not None and chain_to(j,{i},parents) is not None)) for i in selection['offspring_ids']]
        rows.append(dict(tick=old['tick'],site_ids=ids.copy(),physical=physical,observation=observation,
            copies=match_copies(source,units,ids,people),births=births,deaths=deaths,selected_lineage=lineage))
        if name=='ablation' and selection['category']=='horizontal_structural_zero':
            require(units[85] is None and units[86] is None,'structurally unreachable upper row')
    final=dict(tick=32,units=units,raw=raw,site_ids=ids.copy(),parents=[p['parent'] for p in people],individuals=people)
    arm=dict(initial=initial,rows=rows,final=final)
    arm.update(summarize_arm(arm,selection['offspring_ids']))
    return arm


def verify_branch(source, selection, *, on_step=lambda:None):
    same(choose_case(source,selection['genotype'],selection['source']),selection,'branch independent selection')
    require(selection['eligible'] and selection['exchange'] is False,'eligible exchange-off branch')
    if selection['category']=='horizontal_structural_zero':
        same(selection['t0'],6,'structural zero t0')
        require(all(d in (0,1) for r in source['rows'][6:] for d in r['physical']['directions']), 'horizontal-only future directions')
    control=verify_arm(source,selection,'control',on_step)
    ablation=verify_arm(source,selection,'ablation',on_step)
    same(ablation['initial']['energy_export'],selection['energy_export_preview'],'selected export')
    if selection['category']=='horizontal_structural_zero':
        same(ablation['metrics']['double_new_ever'],0,'structural zero double copies')
    return dict(selection=deepcopy(selection),control=control,ablation=ablation,
        delta={k:ablation['metrics'][k]-control['metrics'][k] for k in METRICS})


METRICS=('births','deaths','living','final_energy','imported','spent','new_copy_ever',
    'double_new_ever','persistent10','longest_double','formation_supported','upper_formed',
    'selected_ancestry_supported','formation_persistent10','upper_persistent10','selected_ancestry_persistent10')
CATEGORIES=('horizontal_structural_zero','short_window','remaining_conditional')


def record(branch):
    return dict(selection=deepcopy(branch['selection']),control_metrics=deepcopy(branch['control']['metrics']),
        ablation_metrics=deepcopy(branch['ablation']['metrics']),delta=deepcopy(branch['delta']),
        control_episodes=deepcopy(branch['control']['episodes']),ablation_episodes=deepcopy(branch['ablation']['episodes']))


def summarize(records, selection):
    same([r['selection'] for r in records],[s for s in selection if s['eligible']],'ordered records')
    def group(chosen):
        result={'n':len(chosen)}
        for prefix,key in (('control','control_metrics'),('ablation','ablation_metrics'),('delta','delta')):
            result[prefix+'_totals']={m:sum(r[key][m] for r in chosen) for m in METRICS}
        result['paired_persistent10']=[dict(control=c,ablation=a,n=sum(r['control_metrics']['persistent10']==c and r['ablation_metrics']['persistent10']==a for r in chosen)) for c,a in product((0,1),repeat=2)]
        return result
    cells=[]
    for genotype,mode,exchange in product(GENOTYPES,MODES,(False,True)):
        chosen=[r for r in records if [r['selection'][k] for k in IDENTITY[:3]]==[genotype,mode,exchange]]
        cells.append(dict(genotype=genotype,mode=mode,exchange=exchange,**group(chosen)))
    return dict(source_cases=len(selection),eligible=len(records),noeligible=len(selection)-len(records),cells=cells,
        strata=[dict(category=c,**group([r for r in records if r['selection']['category']==c])) for c in CATEGORIES],overall=group(records))


def main():
    from scripts.founder_removal_inputs import bindings,input_paths,read,digest,source_cases,SELECTION
    root=OUTPUT;proof_path=root/'independent-verification.json'
    require(not proof_path.exists(),'proof already exists')
    started=monotonic();paths=[];before={};input_before={};errors={};completed=steps=0
    names=('metadata.json','records.json','summary.json','selection.json')+tuple(f'cases/branch-{i:03d}.json' for i in range(58))
    def snapshot(mapping, failures):
        result={}
        for name,path in mapping.items():
            try:result[name]=digest(path)
            except Exception as error:failures[name]=f'{type(error).__name__}: {error}'
        return result
    def budget(extra=0):
        require(monotonic()-started<600,'verification time budget')
        require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file())+extra<134217728,'verification storage budget')
    try:
        paths=input_paths(errors)
        input_before=snapshot({p:Path(p) for p in paths},errors)
        before=snapshot({n:root/n for n in names},errors)
        bound=bindings()
        same(errors,{},'readable inputs and outputs');same(paths,sorted(bound),'complete input inventory')
        same(input_before,bound,'input bindings before')
        same(digest(Path(__file__)),bound['scripts/verify_v4_founder_removal.py'],'running verifier binding')
        meta=read(root/'metadata.json')
        fixed=dict(status='complete',planned_cases=58,completed_cases=58,treatment_steps=1260,control_replay_steps=1260,
            new_environment_sources=0,new_independent_initial_worlds=0,reused_environment_sources=20,selected_environment_sources=19,
            time_limit_seconds=600,storage_limit_bytes=134217728)
        require(set(meta)==set(fixed)|{'git_commit','elapsed_seconds','input_paths','input_inventory_errors','input_read_errors_before','input_sha256','input_sha256_after','output_sha256'},'metadata schema')
        for k,v in fixed.items():same(meta[k],v,'metadata '+k)
        same(meta['input_inventory_errors'],{},'inventory errors');same(meta['input_read_errors_before'],{},'input read errors')
        require(type(meta['git_commit']) is str and len(meta['git_commit'])==40 and all(c in '0123456789abcdef' for c in meta['git_commit']),'commit hash')
        require(type(meta['elapsed_seconds']) in (int,float) and math.isfinite(meta['elapsed_seconds']) and 0<=meta['elapsed_seconds']<600,'production duration')
        same(meta['input_paths'],paths,'metadata paths');same(meta['input_sha256'],bound,'metadata before inputs');same(meta['input_sha256_after'],bound,'metadata after inputs')
        same(meta['output_sha256'],{n:before[n] for n in names if n!='metadata.json'},'exact output bindings')
        same(sorted(p.name for p in root.iterdir()),sorted(['metadata.json','records.json','summary.json','selection.json','cases']),'exclusive output inventory')
        same(sorted(p.name for p in (root/'cases').iterdir()),[f'branch-{i:03d}.json' for i in range(58)],'exact 58 case files')
        selection=selection_table(list(source_cases()),read(SELECTION)['cases'],budget)
        same(read(root/'selection.json'),selection,'saved selection')
        saved=read(root/'records.json');same(len(saved),58,'58 saved records')
        records=[]
        def counted():
            nonlocal steps
            steps+=1;budget()
        for index,selected in enumerate(s for s in selection if s['eligible']):
            budget()
            branch=verify_branch(read(selected['source']),selected,on_step=counted)
            same(read(root/f'cases/branch-{index:03d}.json'),branch,'entire independent branch '+str(index))
            result=record(branch);same(saved[index],result,'entire independent record '+str(index))
            records.append(result);completed+=1
        same(steps,2520,'2520 independent physical verification steps')
        same(read(root/'summary.json'),summarize(records,selection),'all cells strata negatives pairs')
        same(bindings(),bound,'inputs unchanged')
        final_errors={};after=snapshot({n:root/n for n in names},final_errors)
        same(final_errors,{},'final output reads');same(after,before,'outputs unchanged')
        proof=dict(status='verified',cases=58,source_cases=240,noeligible=182,independent_verification_steps=steps,
            treatment_steps=1260,control_replay_steps=1260,new_environment_sources=0,new_independent_initial_worlds=0,
            input_files=len(bound),files_sha256=before,files_sha256_after=after,verifier_sha256=digest(Path(__file__)),
            input_paths=paths,input_sha256=input_before,input_sha256_after=bound,elapsed_seconds=monotonic()-started,
            time_limit_seconds=600,storage_limit_bytes=134217728,
            scope='independent 240 source selection; dictionary physics, historical IDs, t0+ accounts, whole genetic components, formed and selected ancestry witnesses, all 58 paired branches and summaries')
        payload=json.dumps(proof,indent=2,allow_nan=False)+'\n';budget(len(payload.encode()))
        try:
            with proof_path.open('x') as stream:stream.write(payload)
            budget()
        except BaseException:
            if proof_path.exists():proof_path.unlink()
            raise
        print('verified 240 selections, 58 paired branches and 2520 dictionary physics steps')
    except BaseException as error:
        failure=root/'verification-failure.json'
        if root.is_dir() and not failure.exists():
            after_errors={}
            evidence=dict(status='failed',error=f'{type(error).__name__}: {error}',completed_cases=completed,
                independent_verification_steps=steps,input_paths=paths,input_sha256=input_before,files_sha256_before=before,
                input_sha256_after=snapshot({p:Path(p) for p in paths},after_errors),
                files_sha256_after=snapshot({n:root/n for n in names},after_errors),read_errors_before=errors,read_errors_after=after_errors)
            with failure.open('x') as stream:stream.write(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
        raise


if __name__=='__main__':main()
