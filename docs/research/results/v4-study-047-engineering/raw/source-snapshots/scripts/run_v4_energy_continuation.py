"""Fixed-window continuation of the saved one-time energy intervention."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import subprocess
import time

from bitgenesis.v4.hereditary_growing import step
from bitgenesis.v4.heredity import HeritableUnit
from bitgenesis.v4.lineage import Observer
from bitgenesis.v4.structure import snapshot
from scripts.analyze_v4_structure_copies import analyze
from scripts.run_v4_copy_control import CONFIG, normalize
from scripts.run_v4_north_energy import SELECTION_KEYS, ordered_selection, require
from scripts import analyze_v4_north_opportunities as opportunities

_full_world_steps = 0
OUTPUT = Path('data/v4-study-028')
METRICS = ('births','deaths','living','final_energy','imported','spent','genetic_ever',
           'genetic_persistent10','longest_genetic','material_ever')
RECORD_KEYS = ('selection','added_energy','metrics','control_metrics','delta','child_fate')


def metrics(rows, final, copies):
    require(len(copies)==1 and copies[0]['anchor_members']==[0,1], 'original copy parent')
    longest = copies[0]['longest']
    return dict(births=sum(p['reason']=='formed' for r in rows for p in r['physical']['material']['proposals']),
                deaths=sum(len(r['physical']['material']['dissolved']) for r in rows),
                living=sum(u is not None for u in final['units']),
                final_energy=sum(u['energy'] for u in final['units'] if u is not None),
                imported=sum(r['physical']['imported'] for r in rows),
                spent=sum(r['physical']['spent'] for r in rows),
                genetic_ever=int(longest['descendant_genetic']>0),
                genetic_persistent10=int(longest['descendant_genetic']>=10),
                longest_genetic=longest['descendant_genetic'],material_ever=int(longest['descendant_material']>0))


def run_branch(source, probe):
    selected = {k:probe[k] for k in SELECTION_KEYS}
    tick = selected['tick']
    require(source['config']==CONFIG and all(source[k]==selected[k] for k in ('mode','seed','exchange')), 'source identity')
    require(type(tick) is int and 1<=tick<=32 and len(source['rows'])==32, 'fixed source horizon')
    require(type(probe['added_energy']) is int and probe['added_energy']==16-selected['energy_before'], 'historical added energy')
    observer = Observer(source['initial']['units'])
    for row in source['rows'][:tick-1]:
        observer.accept(row['physical'])
        require(observer.alive==row['site_ids'], 'saved pre-intervention identities')
    require(observer.alive[selected['site']]==selected['identity'], 'selected parent identity')
    require(observer.individuals[selected['identity']]['founder']==selected['root'], 'selected ancestry')
    treated = deepcopy(probe['treated'])
    observer.accept(dict(tick=tick, **treated))
    formed = [p for p in treated['material']['proposals'] if p['source']==selected['site'] and p['reason']=='formed']
    require(len(formed)==1, 'selected child formed')
    child = observer.alive[formed[0]['target']]
    initial = dict(tick=tick,units=deepcopy(treated['units']),raw=list(treated['raw']),site_ids=list(observer.alive),
                   parents=[p['parent'] for p in observer.individuals],
                   observation=snapshot(treated['units'],observer.alive,16,16,phase='final'),injected_child=child)
    units = [None if u is None else HeritableUnit(u['material'],u['energy'],tuple(u['program'])) for u in initial['units']]
    raw = list(initial['raw']); rows = []
    require(sum(raw)+sum(u is not None for u in units)==7, 'initial mass seven')
    for next_tick in range(tick+1,33):
        saved = source['rows'][next_tick-1]['physical']
        inputs = saved['driven']['inputs']
        require([v['site'] for v in inputs]==list(range(256)), 'ordered saved proposals')
        directions = list(saved['directions']); tickets = [tuple(v) for v in saved['mutation_tickets']]
        before_energy = sum(u.energy for u in units if u is not None)
        units, raw, event = step(units,raw,proposals=[v['proposed'] for v in inputs],directions=directions,
                                 mutation_tickets=tickets,exchange=selected['exchange'],**CONFIG)
        global _full_world_steps
        _full_world_steps += 1
        physical = normalize(dict(tick=next_tick,units=[None if u is None else asdict(u) for u in units],
                                  raw=list(raw),energy=sum(u.energy for u in units if u is not None),
                                  directions=directions,mutation_tickets=tickets,**event))
        require(physical['energy']==before_energy+event['imported']-event['spent'], 'step energy ledger')
        require(event['material_before']==event['material_after']==sum(raw)+sum(u is not None for u in units)==7, 'step mass seven')
        observer.accept(physical)
        rows.append(dict(tick=next_tick,site_ids=list(observer.alive),physical=physical,
                         observation=snapshot(physical['units'],observer.alive,16,16,phase='final')))
    final = dict(tick=32,units=normalize([None if u is None else asdict(u) for u in units]),raw=list(raw),
                 site_ids=list(observer.alive),parents=[p['parent'] for p in observer.individuals])
    projection = dict(tick=tick,site_ids=initial['site_ids'],physical=dict(units=initial['units']),observation=initial['observation'])
    observed = source['rows'][:tick-1]+[projection]+rows
    copies = analyze(source['initial'],observed,final)
    result = metrics(rows,final,copies)
    control = metrics(source['rows'][tick:],source['final'],source['copy_parents'])
    initial_energy = sum(u['energy'] for u in initial['units'] if u is not None)
    require(result['final_energy']==initial_energy+result['imported']-result['spent'], 'continuation energy ledger')
    descendants = {child}
    for person in observer.individuals:
        if person['parent'] in descendants: descendants.add(person['id'])
    person = observer.individuals[child]
    alive = set(observer.alive)-{None}
    fate = dict(identity=child,birth_tick=tick,death_tick=person['death_tick'],alive_final=child in alive,
                direct_offspring=person['offspring'],descendants_born=len(descendants)-1,
                lineage_living_final=len(descendants & alive),
                observed_alive_finals=sum(child in row['site_ids'] for row in observed[tick-1:]))
    return dict(selection=selected,added_energy=probe['added_energy'],initial=initial,rows=rows,final=final,
                copy_parents=copies,metrics=result,control_metrics=control,
                delta={k:result[k]-control[k] for k in METRICS},child_fate=fate)


def record(branch):
    return deepcopy({k:branch[k] for k in RECORD_KEYS})


def summarize(records):
    ordered_selection([r['selection'] for r in records])
    for r in records:
        require(set(r)==set(RECORD_KEYS) and set(r['selection'])==set(SELECTION_KEYS), 'record fields')
        require(type(r['added_energy']) is int and r['added_energy']==16-r['selection']['energy_before'], 'record energy')
        for field in ('metrics','control_metrics','delta'):
            require(set(r[field])==set(METRICS) and all(type(v) is int for v in r[field].values()), 'ten integer metrics')
        for field in ('metrics','control_metrics'):
            m = r[field]
            require(all(v>=0 for v in m.values()) and m['living']<=7 and m['final_energy']<=64*m['living'], 'bounded nonnegative metrics')
            require(m['genetic_ever']==int(m['longest_genetic']>0) and
                    m['genetic_persistent10']==int(m['longest_genetic']>=10) and
                    0<=m['longest_genetic']<=32 and m['material_ever'] in (0,1) and
                    m['genetic_ever']<=m['material_ever'], 'copy event consistency')
        require(r['delta']=={k:r['metrics'][k]-r['control_metrics'][k] for k in METRICS}, 'exact delta')
        f = r['child_fate']; tick = r['selection']['tick']
        require(set(f)=={'identity','birth_tick','death_tick','alive_final','direct_offspring','descendants_born',
                         'lineage_living_final','observed_alive_finals'}, 'child fate fields')
        require(all(type(f[k]) is int and f[k]>=0 for k in ('identity','birth_tick','direct_offspring','descendants_born',
                                                        'lineage_living_final','observed_alive_finals')) and
                type(f['alive_final']) is bool, 'child fate types')
        death = f['death_tick']
        require(f['birth_tick']==tick and (death is None or type(death) is int and tick<death<=32), 'child fate ticks')
        require(f['alive_final']==(death is None) and f['observed_alive_finals']==(33 if death is None else death)-tick,
                'child fate right censor and exposure')
        require(f['direct_offspring']<=f['descendants_born'] and
                int(f['alive_final'])<=f['lineage_living_final']<=min(7,f['descendants_born']+int(f['alive_final'])) and
                f['lineage_living_final']<=r['metrics']['living'], 'child lineage counts')
    cells = []
    for genotype in opportunities.GENOTYPES:
        for exchange in (False,True):
            rows = [r for r in records if (r['selection']['genotype'],r['selection']['exchange'])==(genotype,exchange)]
            cell = dict(genotype=genotype,exchange=exchange,n=len(rows))
            for name,field in (('totals','metrics'),('control_totals','control_metrics'),('delta_totals','delta')):
                cell[name] = {k:sum(r[field][k] for r in rows) for k in METRICS}
            for name,sign in (('positive',1),('negative',-1),('tie',0)):
                cell[name] = {k:sum(((r['delta'][k]>0)-(r['delta'][k]<0))==sign for r in rows) for k in METRICS}
            cell.update(child_alive_final=sum(r['child_fate']['alive_final'] for r in rows),
                        child_reproduced=sum(r['child_fate']['direct_offspring']>0 for r in rows),
                        lineage_alive_final=sum(r['child_fate']['lineage_living_final']>0 for r in rows))
            cells.append(cell)
    return cells


def main():
    from scripts.energy_continuation_inputs import bindings, source_cases, input_paths, read, save, digest
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(), 'clean launch')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic(); records = []; inventory = []; step_start = _full_world_steps
    meta = dict(status='running',planned_branches=52,completed_branches=0,new_full_world_steps=0,new_phase_transitions=0,
                new_environment_sources=0,reused_environment_sources=20,selected_environment_sources=11,
                new_independent_initial_worlds=0,time_limit_seconds=600,storage_limit_bytes=134217728)
    def budget():
        require(time.monotonic()-started<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728, 'bounded execution')
    def hashes():
        return {str(p.relative_to(OUTPUT)):digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p != OUTPUT/'metadata.json'}
    def input_hashes(error_key):
        values = {}; meta[error_key] = {}
        for path in inventory:
            try: values[path] = digest(path)
            except BaseException as exc: meta[error_key][path] = repr(exc)
        return values
    try:
        meta['git_commit'] = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        meta['input_inventory_errors'] = {}
        inventory = input_paths(meta['input_inventory_errors']); meta['input_paths'] = inventory
        meta['input_sha256'] = input_hashes('input_read_errors_before')
        save(OUTPUT/'metadata.json',meta); save(OUTPUT/'records.json',records); (OUTPUT/'cases').mkdir()
        before = bindings(); require(before==meta['input_sha256'], 'validated initial inputs'); budget()
        probes = read(Path('data/v4-study-027/records.json'))
        ordered_selection(probes)
        require(sum(32-p['tick'] for p in probes)==996, 'fixed996 planned steps')
        wanted = {(p['genotype'],p['mode'],p['exchange'],p['seed']) for p in probes}
        cases = {}; order = []
        for genotype,path in source_cases():
            budget(); case = read(path); key = (genotype,case['mode'],case['exchange'],case['seed']); order.append(key)
            if key in wanted: cases[key] = case
        require(order==opportunities.GRID, 'complete ordered source cases')
        for index,probe in enumerate(probes):
            budget(); source = cases[(probe['genotype'],probe['mode'],probe['exchange'],probe['seed'])]
            branch = run_branch(source,probe)
            save(OUTPUT/'cases'/f'branch-{index:03d}.json',branch)
            records.append(record(branch))
            meta.update(completed_branches=len(records),new_full_world_steps=_full_world_steps-step_start,elapsed_seconds=time.monotonic()-started)
            save(OUTPUT/'records.json',records); save(OUTPUT/'metadata.json',meta); budget()
        require(_full_world_steps-step_start==996, 'fixed996 completed steps')
        save(OUTPUT/'summary.json',summarize(records))
        meta['input_sha256_after'] = bindings(); require(before==meta['input_sha256_after'], 'unchanged inputs')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256=hashes())
        budget(); save(OUTPUT/'metadata.json',meta); budget()
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc),elapsed_seconds=time.monotonic()-started,new_full_world_steps=_full_world_steps-step_start)
        try:
            meta['input_sha256_after'] = bindings()
            if meta.get('input_sha256')!=meta['input_sha256_after']: meta['finalization_error'] = 'inputs changed during failure'
        except BaseException as err:
            meta['finalization_error'] = repr(err); meta['input_sha256_after'] = input_hashes('input_read_errors')
        try: meta['output_sha256'] = hashes()
        except BaseException as err: meta['output_hash_error'] = repr(err)
        save(OUTPUT/'metadata.json',meta)
        raise


if __name__=='__main__':
    main()
