"""Fixed formation-stage energy intervention on saved north opportunities."""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import subprocess
import time

from bitgenesis.v4 import heredity
from scripts import analyze_v4_north_opportunities as opportunities
from scripts.run_v4_copy_control import CONFIG, normalize

_phase_transitions = 0
SELECTION_KEYS = ('genotype', 'mode', 'seed', 'exchange', 'tick', 'site', 'identity', 'root', 'energy_before')
REASONS = ('energy', 'occupied', 'raw_material', 'collision', 'formed')
OUTPUT = Path('data/v4-study-027')


def require(value, message):
    if not value:
        raise ValueError(message)


def eligible(actor):
    return (actor['root'] in (0, 1) and actor['direction'] == 3 and actor['reason'] != 'dissolved'
            and 0 < actor['energy_interaction'] < 16 and actor['target_occupied'] is False and actor['raw_available'] >= 1)


def selection(record, actor):
    return dict(genotype=record['genotype'], mode=record['mode'], seed=record['seed'], exchange=record['exchange'],
                **{k: actor[k] for k in ('tick', 'site', 'identity', 'root')}, energy_before=actor['energy_interaction'])


def ordered_selection(records):
    require(len(records) == 52, 'complete52 probes')
    keys = []
    for s in records:
        require(s['genotype'] in opportunities.GENOTYPES and s['mode'] == 'random-both' and
                type(s['exchange']) is bool and all(type(s[k]) is int for k in ('seed','tick','site','identity','root','energy_before')),
                'strict probe identity')
        require(120000 <= s['seed'] < 120020 and 1 <= s['tick'] <= 32 and 0 <= s['site'] < 256 and
                s['identity'] >= 0 and s['root'] in (0,1) and 0 < s['energy_before'] < 16, 'valid probe identity')
        keys.append((opportunities.GENOTYPES.index(s['genotype']), s['exchange'], s['seed'], s['tick'], s['site']))
    require(keys == sorted(set(keys)), 'ordered unique52 probes')
    require(Counter((s['genotype'],s['exchange']) for s in records) ==
            {(g,e): 5 if e else 21 for g in opportunities.GENOTYPES for e in (False,True)}, 'fixed four cells')


def select(records):
    opportunities.summarize(records)  # Validate the entire ordered 240-case saved ledger.
    selected = [selection(r,a) for r in records for step in r['steps'] for a in step if eligible(a)]
    ordered_selection(selected)
    return selected


def phase(initial):
    require(set(initial) == {'units','raw','directions','mutation_tickets'}, 'phase input fields')
    units = [None if u is None else heredity.HeritableUnit(u['material'],u['energy'],tuple(u['program'])) for u in initial['units']]
    global _phase_transitions
    _phase_transitions += 1
    after, raw, material = heredity.convert(units, list(initial['raw']), 16, 16, list(initial['directions']),
        [tuple(t) for t in initial['mutation_tickets']], threshold=16, construction_cost=4, copy_cost=1, mutation_per_thousand=0)
    result = normalize(dict(units=[None if u is None else asdict(u) for u in after],raw=raw,material=material))
    check_ledger(initial, result, 0)
    return result


def check_ledger(initial, arm, added):
    before = sum(u['energy'] for u in initial['units'] if u is not None)
    after = sum(u['energy'] for u in arm['units'] if u is not None)
    mass = sum(initial['raw']) + sum(u is not None for u in initial['units'])
    material = arm['material']
    formed = sum(p['reason'] == 'formed' for p in material['proposals'])
    require(material['spent'] == 5*formed and material['construction_spent'] == 4*formed and material['copy_spent'] == formed,
            'formation expenditure')
    require(material['energy_before'] == before+added and material['energy_after'] == after == before+added-material['spent'], 'phase energy ledger')
    require(material['material_before'] == material['material_after'] == mass ==
            sum(arm['raw'])+sum(u is not None for u in arm['units']), 'phase mass ledger')


def run_probe(case, selected):
    require(set(selected) == set(SELECTION_KEYS), 'selection fields')
    require(case['config'] == CONFIG and all(case[k] == selected[k] for k in ('mode','seed','exchange')), 'source case identity')
    require(all(type(selected[k]) is int for k in ('seed','tick','site','identity','root','energy_before')) and
            type(selected['exchange']) is bool and 1 <= selected['tick'] <= 32, 'strict selection identity')
    ledger = opportunities.analyze_case(case, selected['genotype'])
    actors = ledger['steps'][selected['tick']-1]
    require(any(eligible(a) and selection(ledger,a) == selected for a in actors), 'selected saved actor')
    p = case['rows'][selected['tick']-1]['physical']
    previous = case['initial'] if selected['tick'] == 1 else case['rows'][selected['tick']-2]['physical']
    initial = deepcopy(dict(units=p['interaction_units'],raw=previous['raw'],directions=p['directions'],mutation_tickets=p['mutation_tickets']))
    control = phase(initial)
    require(control == {k:p[k] for k in ('units','raw','material')}, 'saved control mismatch')
    added = 16-selected['energy_before']
    augmented = deepcopy(initial); augmented['units'][selected['site']]['energy'] = 16
    treated = phase(augmented)
    check_ledger(initial, control, 0); check_ledger(initial, treated, added)
    return dict(selected,added_energy=added,initial=initial,control=control,treated=treated)


def summarize(records):
    ordered_selection(records)
    for r in records:
        require(set(r) == set(SELECTION_KEYS)|{'added_energy','initial','control','treated'}, 'probe record fields')
        require(r['added_energy'] == 16-r['energy_before'] and
                r['initial']['units'][r['site']]['energy'] == r['energy_before'], 'external energy accounting')
        for arm, added in (('control',0),('treated',r['added_energy'])):
            check_ledger(r['initial'],r[arm],added)
    result = []
    for genotype in opportunities.GENOTYPES:
        for exchange in (False,True):
            cell = dict(genotype=genotype,exchange=exchange,probes=0,control_formed=0,treated_formed=0,nonzero_treated=0,
                        added_energy=0,treated_reasons={k:0 for k in REASONS},total_formed_delta=0,spent_delta=0,energy_after_delta=0,other_reason_changes=0)
            for r in records:
                if (r['genotype'],r['exchange']) != (genotype,exchange): continue
                c,t = r['control']['material'],r['treated']['material']
                cp,tp = ({p['source']:p for p in arm['proposals']} for arm in (c,t))
                require(cp.keys() == tp.keys() and r['site'] in cp, 'all original proposals retained')
                source = r['site']; reason = tp[source]['reason']
                require(reason in REASONS and cp[source]['reason']=='energy', 'probe source reasons')
                cell['probes'] += 1; cell['control_formed'] += cp[source]['reason']=='formed'
                cell['treated_formed'] += reason=='formed'; cell['nonzero_treated'] += reason=='formed' and tp[source]['material'] != 0
                cell['added_energy'] += r['added_energy']; cell['treated_reasons'][reason] += 1
                cell['total_formed_delta'] += sum(p['reason']=='formed' for p in tp.values())-sum(p['reason']=='formed' for p in cp.values())
                cell['spent_delta'] += t['spent']-c['spent']; cell['energy_after_delta'] += t['energy_after']-c['energy_after']
                cell['other_reason_changes'] += sum(cp[s]['reason'] != tp[s]['reason'] for s in cp if s != source)
            result.append(cell)
    return result


def main():
    from scripts.north_energy_inputs import bindings, source_cases, input_paths, read, save, digest
    require(not subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip(), 'clean launch')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic(); records = []; inventory = []; phase_start = _phase_transitions
    meta = dict(status='running', planned_probes=52, completed_probes=0, new_phase_transitions=0, new_full_world_steps=0,
                new_environment_sources=0, reused_environment_sources=20, new_independent_initial_worlds=0,
                time_limit_seconds=300, storage_limit_bytes=33554432,
                git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip())
    def budget():
        require(time.monotonic()-started < 300 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file()) < 33554432, 'bounded execution')
    def hashes():
        return {str(p.relative_to(OUTPUT)): digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p.name != 'metadata.json'}
    def input_hashes(error_key):
        values = {}; meta[error_key] = {}
        for path in inventory:
            try: values[path] = digest(path)
            except BaseException as exc: meta[error_key][path] = repr(exc)
        return values
    try:
        meta['input_inventory_errors'] = {}
        inventory = input_paths(meta['input_inventory_errors']); meta['input_paths'] = inventory
        meta['input_sha256'] = input_hashes('input_read_errors_before')
        save(OUTPUT/'metadata.json', meta); save(OUTPUT/'records.json', records)
        before = bindings(); require(before == meta['input_sha256'], 'validated initial inputs'); budget()
        selected = select(read(Path('data/v4-study-026/records.json')))
        cases = {}; source_order = []
        wanted = {(s['genotype'],s['mode'],s['exchange'],s['seed']) for s in selected}
        for genotype, path in source_cases():
            budget(); case = read(path)
            key = (genotype,case['mode'],case['exchange'],case['seed'])
            source_order.append(key)
            if key in wanted: cases[key] = case
        require(source_order == opportunities.GRID, 'complete ordered source cases')
        for s in selected:
            budget(); case = cases[(s['genotype'],s['mode'],s['exchange'],s['seed'])]
            records.append(run_probe(case,s))
            meta.update(completed_probes=len(records),new_phase_transitions=_phase_transitions-phase_start,elapsed_seconds=time.monotonic()-started)
            save(OUTPUT/'records.json',records); save(OUTPUT/'metadata.json',meta)
        save(OUTPUT/'summary.json',summarize(records))
        meta['input_sha256_after'] = bindings(); require(before == meta['input_sha256_after'], 'unchanged inputs')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256=hashes())
        budget(); save(OUTPUT/'metadata.json',meta); budget()
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc),elapsed_seconds=time.monotonic()-started,
                    new_phase_transitions=_phase_transitions-phase_start)
        try:
            meta['input_sha256_after'] = bindings()
            if meta.get('input_sha256') != meta['input_sha256_after']: meta['finalization_error'] = 'inputs changed during failure'
        except BaseException as err:
            meta['finalization_error'] = repr(err); meta['input_sha256_after'] = input_hashes('input_read_errors')
        try: meta['output_sha256'] = hashes()
        except BaseException as err: meta['output_hash_error'] = repr(err)
        save(OUTPUT/'metadata.json',meta)
        raise


if __name__ == '__main__':
    main()
