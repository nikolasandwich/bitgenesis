"""Independent Study028 dictionary physics, identities and copy recount."""
from copy import deepcopy
import json
import math
from pathlib import Path
from time import monotonic
from bitgenesis.v4.exchange_branch_audit import physical_step
from bitgenesis.v4.structure_audit import reconstruct
from scripts.verify_v4_structure_copies import recount
from scripts import verify_v4_north_energy as prior

OUTPUT = Path('data/v4-study-028')
METRICS = ('births', 'deaths', 'living', 'final_energy', 'imported', 'spent',
           'genetic_ever', 'genetic_persistent10', 'longest_genetic', 'material_ever')
RECORD_KEYS = ('selection', 'added_energy', 'metrics', 'control_metrics', 'delta', 'child_fate')
require, same = prior.require, prior.same


def verify_branch(source, probe, *, on_step=None):
    selection = {k: probe[k] for k in prior.KEYS}
    require(selection['genotype'] in prior.prior.GENOTYPES and selection['mode']=='random-both' and type(selection['exchange']) is bool, 'selection cell')
    require(all(type(selection[k]) is int for k in prior.KEYS[2:] if k!='exchange'), 'selection integers')
    same(probe, prior.verify_probe(source, selection), 'complete 027 stage record')
    same(source['config'], dict(width=16, height=16, capacity=64, leak=1, bond_cost=1,
        threshold=16, construction_cost=4, copy_cost=1, mutation_per_thousand=0), 'fixed physics')
    require(len(source['rows']) == 32, '32 source rows')
    ids = []; parents = []
    for unit in source['initial']['units']:
        ids.append(None if unit is None else len(parents))
        if unit is not None: parents.append(None)
    same(source['initial']['site_ids'], ids, 'founder identities')
    same(source['initial']['observation'], reconstruct(source['initial']['units'], ids, 16, 16, 'final'), 'initial components')
    def accept(material):
        old = ids.copy()
        for site in material['dissolved']:
            require(ids[site] is not None, 'dissolution identity')
            ids[site] = None
        created = {}
        for proposal in material['proposals']:
            if proposal['reason'] == 'formed':
                a, b = proposal['source'], proposal['target']
                require(old[a] is not None and ids[b] is None, 'birth ancestry and vacancy')
                created[a] = len(parents)
                ids[b] = len(parents); parents.append(old[a])
        return created
    tick = selection['tick']
    observation_rows = deepcopy(source['rows'][:tick-1])
    for expected_tick, row in enumerate(source['rows'], 1):
        same(row['tick'], expected_tick, 'source tick order')
        same(row['physical']['tick'], expected_tick, 'source physical tick order')
    for row in observation_rows:
        accept(row['physical']['material'])
        same(row['site_ids'], ids, 'prefix identities')
        same(row['observation'], reconstruct(row['physical']['units'], ids, 16, 16, 'final'), 'prefix components')
    created = accept(probe['treated']['material'])
    require(selection['site'] in created, 'injected child formed')
    child = created[selection['site']]
    units, raw = deepcopy(probe['treated']['units']), deepcopy(probe['treated']['raw'])
    same(sum(raw)+sum(u is not None for u in units), 7, 'treated initial mass')
    observed = reconstruct(units, ids, 16, 16, 'final')
    initial = dict(tick=tick, units=deepcopy(units), raw=deepcopy(raw), site_ids=ids.copy(),
                   parents=parents.copy(), observation=observed, injected_child=child)
    observation_rows.append(dict(tick=tick, site_ids=ids.copy(), physical=dict(units=deepcopy(units)), observation=observed))
    rows = []; death = None; alive_finals = 1
    start_energy = sum(u['energy'] for u in units if u is not None)
    imported = spent = 0
    for row in source['rows'][tick:]:
        physical = physical_step(units, raw, source['config'], row['physical'], selection['exchange'])
        if on_step is not None: on_step()
        same(physical['energy_after'], physical['energy_before']+physical['imported']-physical['spent'], 'step energy balance')
        same(physical['material_before'], 7, 'initial mass'); same(physical['material_after'], 7, 'final mass')
        if child in [ids[site] for site in physical['material']['dissolved']]: death = row['tick']
        accept(physical['material'])
        units, raw = physical['units'], physical['raw']
        imported += physical['imported']; spent += physical['spent']
        same(sum(u['energy'] for u in units if u is not None), start_energy+imported-spent, 'continuation ledger without repeated external energy')
        observed = reconstruct(units, ids, 16, 16, 'final')
        rows.append(dict(tick=row['tick'], site_ids=ids.copy(), physical=physical, observation=observed))
        alive_finals += child in ids
    final = dict(tick=32, units=units, raw=raw, site_ids=ids.copy(), parents=parents.copy())
    copies = recount(source['initial'], observation_rows+rows, final)
    treated = metrics(rows, final, copies)
    control = metrics(source['rows'][tick:], source['final'], source['copy_parents'])
    descendants = {child}
    for identity, parent in enumerate(parents):
        if parent in descendants: descendants.add(identity)
    fate = dict(identity=child, birth_tick=tick, death_tick=death, alive_final=child in ids,
        direct_offspring=parents.count(child), descendants_born=len(descendants)-1,
        lineage_living_final=sum(i in descendants for i in ids if i is not None), observed_alive_finals=alive_finals)
    return dict(selection=selection, added_energy=probe['added_energy'], initial=initial, rows=rows,
        final=final, copy_parents=copies, metrics=treated, control_metrics=control,
        delta={k:treated[k]-control[k] for k in METRICS}, child_fate=fate)


def metrics(rows, final, copies):
    return dict(births=sum(p['reason']=='formed' for r in rows for p in r['physical']['material']['proposals']),
        deaths=sum(len(r['physical']['material']['dissolved']) for r in rows),
        living=sum(u is not None for u in final['units']),
        final_energy=sum(u['energy'] for u in final['units'] if u is not None),
        imported=sum(r['physical']['imported'] for r in rows), spent=sum(r['physical']['spent'] for r in rows),
        genetic_ever=sum(p['longest']['descendant_genetic']>=1 for p in copies),
        genetic_persistent10=sum(p['longest']['descendant_genetic']>=10 for p in copies),
        longest_genetic=max((p['longest']['descendant_genetic'] for p in copies), default=0),
        material_ever=sum(p['longest']['descendant_material']>=1 for p in copies))


def record(branch):
    return deepcopy({k:branch[k] for k in RECORD_KEYS})


def aggregate(records):
    require(type(records) is list, 'record list')
    prior.validate_selection([r['selection'] for r in records])
    for r in records:
        require(set(r) == set(RECORD_KEYS), 'record schema')
        same(r['added_energy'], 16-r['selection']['energy_before'], 'historical external energy')
        for label in ('metrics', 'control_metrics', 'delta'):
            require(set(r[label]) == set(METRICS), 'metric schema')
            require(all(type(v) is int and (label=='delta' or v>=0) for v in r[label].values()), 'metric integers')
        for label in ('metrics', 'control_metrics'):
            m=r[label]
            require(0<=m['genetic_persistent10']<=m['genetic_ever']<=m['material_ever']<=1, 'copy indicator bounds')
            require(0<=m['longest_genetic']<=32 and m['genetic_ever']==int(m['longest_genetic']>=1) and m['genetic_persistent10']==int(m['longest_genetic']>=10), 'copy interval indicators')
            require(m['living']<=7 and m['final_energy']<=64*m['living'], 'final world bounds')
        same(r['delta'], {k:r['metrics'][k]-r['control_metrics'][k] for k in METRICS}, 'metric differences')
        f = r['child_fate']
        require(set(f) == {'identity','birth_tick','death_tick','alive_final','direct_offspring','descendants_born','lineage_living_final','observed_alive_finals'}, 'fate schema')
        require(type(f['alive_final']) is bool, 'fate boolean')
        require(all(type(f[k]) is int and f[k]>=0 for k in f if k not in ('alive_final','death_tick')), 'fate integers')
        same(f['birth_tick'], r['selection']['tick'], 'child birth tick')
        require((f['death_tick'] is None and f['alive_final']) or (type(f['death_tick']) is int and f['birth_tick'] < f['death_tick'] <= 32 and not f['alive_final']), 'death censoring')
        same(f['observed_alive_finals'], (33 if f['death_tick'] is None else f['death_tick'])-f['birth_tick'], 'alive observation count')
        require(f['direct_offspring']<=f['descendants_born'] and int(f['alive_final'])<=f['lineage_living_final']<=min(r['metrics']['living'],7,f['descendants_born']+int(f['alive_final'])), 'lineage bounds')
    cells=[]
    for g in prior.prior.GENOTYPES:
        for e in (False, True):
            selected=[r for r in records if r['selection']['genotype']==g and r['selection']['exchange']==e]
            cell=dict(genotype=g, exchange=e, n=len(selected))
            for name, key in (('totals','metrics'),('control_totals','control_metrics'),('delta_totals','delta')):
                cell[name]={k:sum(r[key][k] for r in selected) for k in METRICS}
            for name, sign in (('positive',1),('negative',-1),('tie',0)):
                cell[name]={k:sum(((r['delta'][k]>0)-(r['delta'][k]<0))==sign for r in selected) for k in METRICS}
            cell.update(child_alive_final=sum(r['child_fate']['alive_final'] for r in selected),
                child_reproduced=sum(r['child_fate']['direct_offspring']>0 for r in selected),
                lineage_alive_final=sum(r['child_fate']['lineage_living_final']>0 for r in selected))
            cells.append(cell)
    return cells


def main():
    from scripts.energy_continuation_inputs import bindings, read, digest, input_paths, source_cases
    root=OUTPUT; proof_path=root/'independent-verification.json'
    require(not proof_path.exists(), 'proof already exists')
    started=monotonic(); paths=[]; before={}; input_before={}; errors={}; completed=0; steps=0
    names=('metadata.json','records.json','summary.json')+tuple(f'cases/branch-{i:03d}.json' for i in range(52))
    def snapshot(mapping, failures):
        result={}
        for name,path in mapping.items():
            try: result[name]=digest(path)
            except Exception as error: failures[name]=f'{type(error).__name__}: {error}'
        return result
    def budget(extra=0):
        require(monotonic()-started<600, 'verification time budget')
        require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file())+extra<134217728, 'verification storage budget')
    try:
        paths=input_paths(errors)
        input_before=snapshot({p:Path(p) for p in paths}, errors)
        before=snapshot({n:root/n for n in names}, errors)
        bound=bindings(); require(len(bound)==413, '413 bound inputs')
        same(paths, sorted(bound), 'complete input paths'); same(input_before,bound,'readable input inventory')
        same(digest(Path(__file__)),bound['scripts/verify_v4_energy_continuation.py'],'running verifier binding')
        meta=read(root/'metadata.json')
        fixed=dict(status='complete',planned_branches=52,completed_branches=52,new_full_world_steps=996,
            new_phase_transitions=0,new_environment_sources=0,reused_environment_sources=20,
            selected_environment_sources=11,new_independent_initial_worlds=0,time_limit_seconds=600,storage_limit_bytes=134217728)
        require(set(meta)==set(fixed)|{'git_commit','elapsed_seconds','input_paths','input_sha256','input_sha256_after','output_sha256','input_inventory_errors','input_read_errors_before'}, 'metadata schema')
        same(meta['input_inventory_errors'],{},'successful input inventory')
        same(meta['input_read_errors_before'],{},'successful input reads')
        for key,value in fixed.items(): same(meta[key],value,'metadata '+key)
        require(type(meta['git_commit']) is str and len(meta['git_commit'])==40 and all(c in '0123456789abcdef' for c in meta['git_commit']), 'recorded commit')
        require(type(meta['elapsed_seconds']) in (int,float) and math.isfinite(meta['elapsed_seconds']) and 0<=meta['elapsed_seconds']<600,'run time budget')
        same(meta['input_paths'],paths,'metadata paths'); same(meta['input_sha256'],bound,'before bindings'); same(meta['input_sha256_after'],bound,'after bindings')
        same(meta['output_sha256'],{n:before[n] for n in names if n!='metadata.json'},'output hashes')
        require({p.name for p in root.iterdir()}=={'metadata.json','records.json','summary.json','cases'},'exclusive root inventory')
        require({p.name for p in (root/'cases').iterdir()}=={Path(n).name for n in names[3:]},'52 case inventory')
        probes=read(Path('data/v4-study-027/records.json'))
        prior.aggregate(probes)
        sources=list(source_cases()); require(len(sources)==240,'240 sources')
        cases={}
        for index,(genotype,path) in enumerate(sources):
            # Source ordering is fixed by the already bound 026/027 queue proof.
            expected=prior.prior.GRID[index]
            same(genotype,expected[0],'source genotype order')
            expected_name=f'seed-{expected[3]}-{expected[1]}-exchange-{str(expected[2]).lower()}.json'
            same(path.name,expected_name,'source case order')
            cases[expected]=path
        saved=read(root/'records.json'); require(type(saved) is list and len(saved)==52,'52 saved records')
        records=[]
        def counted_step():
            nonlocal steps
            steps+=1
            budget()
        for index,probe in enumerate(probes):
            budget()
            key=tuple(probe[k] for k in ('genotype','mode','exchange','seed'))
            source=read(cases[key])
            branch=verify_branch(source,probe,on_step=counted_step)
            same(read(root/f'cases/branch-{index:03d}.json'),branch,'entire independent branch')
            result=record(branch); same(saved[index],result,'entire independent record')
            records.append(result); completed+=1
        same(steps,996,'996 subsequent full world steps')
        same(read(root/'summary.json'),aggregate(records),'all four summary cells')
        same(bindings(),bound,'inputs unchanged'); same(snapshot({n:root/n for n in names},{}),before,'outputs unchanged')
        proof=dict(status='verified',input_files=413,branches=52,new_full_world_steps=steps,new_phase_transitions=0,
            new_environment_sources=0,reused_environment_sources=20,selected_environment_sources=11,new_independent_initial_worlds=0,
            files_sha256=before,verifier_sha256=digest(Path(__file__)),input_paths=paths,input_sha256=input_before,
            input_sha256_after=bound,elapsed_seconds=monotonic()-started,time_limit_seconds=600,storage_limit_bytes=134217728,
            scope='independent 027 stage validation, subsequent dictionary physics, plain identities, copy matching, metrics and child fate')
        payload=json.dumps(proof,indent=2,allow_nan=False)+'\n'; budget(len(payload.encode()))
        with proof_path.open('x') as stream: stream.write(payload)
        budget()
        print('verified 52 continuation branches, 996 complete steps, 413 inputs and 55 outputs')
    except BaseException as error:
        failure=root/'verification-failure.json'
        if root.is_dir() and not failure.exists():
            after_errors={}
            evidence=dict(status='failed',error=f'{type(error).__name__}: {error}',completed_branches=completed,
                new_full_world_steps=steps,input_paths=paths,input_sha256=input_before,files_sha256_before=before,
                input_sha256_after=snapshot({p:Path(p) for p in paths},after_errors),
                files_sha256_after=snapshot({n:root/n for n in names},after_errors),read_errors_before=errors,read_errors_after=after_errors)
            with failure.open('x') as stream: stream.write(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
        raise


if __name__=='__main__':
    main()
