"""Study047 independent continuous-stream, dictionary-physics verifier.

Only immutable source contracts are shared with the producer. This module never
imports a producer scientific function or treats a saved scientific value as an
oracle. Saved objects are compared after independent reconstruction.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
from math import gcd
import os
import pickle
from pathlib import Path
import random
import re
import shlex
import signal
import subprocess
import sys
import time
import traceback
from types import MappingProxyType

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bitgenesis.v4.exchange_branch_audit import physical_step
from bitgenesis.v4.structure_audit import reconstruct as partition
from scripts import middle_withdrawal_inputs as inputs

ARMS = ('continue_north', 'withdraw_to_natural')
ENCODINGS = ('east', 'west', 'south', 'north', 'homogeneous')
REASONS = ('energy', 'occupied', 'raw_material', 'collision', 'formed')
SUPPORT = ('formation_supported', 'upper_formed', 'selected_ancestry_supported',
           'formation_persistent10', 'upper_persistent10', 'selected_ancestry_persistent10')
BINARY = ('new_copy_ever', 'double_new_ever', 'persistent10', 'future_persistent10',
          *SUPPORT, *('after32_' + k for k in SUPPORT))
METRICS = ('births', 'deaths', 'living', 'final_energy', 'imported', 'rejected_import',
           'spent', 'leakage', 'bond_spent', 'construction_spent', 'copy_spent',
           'new_copy_ever', 'double_new_ever', 'persistent10', 'future_persistent10',
           'longest_double', *SUPPORT, *('after32_' + k for k in SUPPORT))
INTERPRETATION = ('既定北向前缀后的完整方向政策撤除效果；方向同时影响程序材料表达；'
                  '人工初态与外部供能保持，不估计从未干预或自主生命出现；同seed编码相关。')
require, same = inputs.require, inputs.same


def json_value(value):
    if isinstance(value, MappingProxyType): value = dict(value)
    if type(value) is dict: return {k: json_value(v) for k, v in value.items()}
    if type(value) in (tuple, list): return [json_value(v) for v in value]
    return value


def compare_artifact(saved, rebuilt, label):
    """Concrete-type equality of every field, not merely a summary or digest."""
    same(saved, rebuilt, label)


def restore_environment(boundary, originals, frozen_runtime, budget=lambda: None):
    same(inputs.runtime(), frozen_runtime, 'independent frozen runtime')
    seed = boundary['seed']
    require(type(seed) is int, 'integer environment seed')
    same(sorted(originals), ['random-both', 'random-direction'], 'two original streams')
    rng = {}
    for kind in ('directions', 'feeds'):
        digest = hashlib.sha256(('v4-copy-ablation-1:%d:%s' % (seed, kind)).encode('ascii')).digest()
        rng[kind] = random.Random(int.from_bytes(digest, byteorder='big'))
    for mode, case in originals.items():
        same([case['seed'], case['mode'], case['exchange'], case['config'], len(case['rows'])],
             [seed, mode, False, inputs.CONFIG, 32], 'past source identity')
    replay = []
    for offset in range(32):
        budget()
        row = dict(tick=offset + 1, directions=[], feed_sites_draw_order=[])
        for site in range(256): row['directions'].append(rng['directions'].randrange(4))
        row['feed_sites_draw_order'] = rng['feeds'].sample(range(256), k=4)
        for mode in originals:
            saved = originals[mode]['rows'][offset]['physical']
            feed_sites = (85, 86, 117, 118) if mode == 'random-direction' else row['feed_sites_draw_order']
            same(saved['tick'], offset + 1, 'past tick')
            same(saved['directions'], row['directions'], 'past directions')
            same(saved['mutation_tickets'], [[999, 0, 1] for _ in range(256)], 'past mutation')
            same([x['site'] for x in saved['driven']['inputs']], list(range(256)), 'past feed positions')
            same([x['proposed'] for x in saved['driven']['inputs']],
                 [8 * int(s in feed_sites) for s in range(256)], 'past feed amounts')
        replay.append(row)
    same(boundary['past_ticks'], len(replay), 'exact past window')
    same(boundary['tape_sha256'], inputs.object_hash(replay), 'past tape digest')
    same(boundary['past_feed_sites_draw_order'], [r['feed_sites_draw_order'] for r in replay], 'past ordered samples')
    for kind, stream in rng.items():
        state = json_value(stream.getstate())
        same(state, boundary['states_after_tick32'][kind], 'full independently consumed RNG state')
        same(inputs.object_hash(state), boundary['state_sha256'][kind], 'state digest')
    # Continue these exact independently consumed streams; no replacement seed or
    # speculative future draw, and no reliance on setstate as proof of history.
    return rng


def draw_future(streams, budget=lambda: None, progress=None, partial=None):
    progress = {} if progress is None else progress
    partial = {} if partial is None else partial
    require(not partial, 'fresh environment checkpoint')
    partial.update(status='running', natural_tape=[], pending_tick=None)
    first = None
    try:
        for tick in range(33, 65):
            budget()
            row = dict(tick=tick, directions=[], feed_sites_draw_order=None)
            partial['pending_tick'] = row
            for site in range(256):
                row['directions'].append(streams['directions'].randrange(4))
                progress['future_direction_values'] = progress.get('future_direction_values', 0) + 1
            row['feed_sites_draw_order'] = streams['feeds'].sample(range(256), 4)
            partial['natural_tape'].append(MappingProxyType(dict(tick=tick, directions=tuple(row['directions']),
                                               feed_sites_draw_order=tuple(row['feed_sites_draw_order']))))
            partial['pending_tick'] = None
            progress['future_generator_ticks'] = progress.get('future_generator_ticks', 0) + 1
        partial['status'] = 'complete'
    except BaseException as error:
        first = error
    partial['current_stream_states'], partial['state_capture_errors'] = {}, {}
    for kind in ('directions', 'feeds'):
        try: partial['current_stream_states'][kind] = json_value(streams[kind].getstate())
        except BaseException as error:
            partial['state_capture_errors'][kind] = repr(error)
            if first is None: first = error
    if first is not None:
        partial['status'] = 'failed'
        raise first
    return tuple(partial['natural_tape'])


def directions_for(natural, name):
    require(name in ARMS, 'fixed policy name')
    require(len(natural) == 256 and all(type(v) is int and 0 <= v < 4 for v in natural), '256 integer directions')
    return [3 if name == ARMS[0] and s in (101, 102) else v for s, v in enumerate(natural)]


def restore_state(saved):
    inputs.validate_state(saved)
    return deepcopy(saved)


def advance_identities(ids, people, physical):
    """Replay only the passive identity ledger; IDs are never recycled."""
    old_ids = tuple(ids)
    births, deaths = [], []
    for site in physical['material']['dissolved']:
        identity = old_ids[site]
        require(identity is not None and people[identity]['death_tick'] is None, 'live natural death')
        people[identity]['death_tick'] = physical['tick']
        deaths.append(identity)
        ids[site] = None
    for event in physical['material']['proposals']:
        if event['reason'] != 'formed': continue
        parent_id = old_ids[event['source']]
        require(parent_id is not None and ids[event['target']] is None, 'old parent, empty birth target')
        parent = people[parent_id]
        child = dict(id=len(people), site=event['target'], birth_tick=physical['tick'], death_tick=None,
                     parent=parent_id, founder=parent['founder'], generation=parent['generation'] + 1,
                     material=event['material'], program=list(event['child_program']),
                     birth_energy=event['child_energy'], mutated=event['mutated'], offspring=0)
        require(parent['birth_tick'] < physical['tick'], 'no newborn cascade')
        ids[event['target']] = child['id']
        parent['offspring'] += 1
        people.append(child)
        births.append(deepcopy(child))
    same([u is None for u in physical['units']], [i is None for i in ids], 'full identity occupation')
    return births, deaths


def ancestry(identity, people, selected):
    trail = []
    while identity is not None:
        require(type(identity) is int and 0 <= identity < len(people), 'ancestry identity')
        trail.append(identity)
        if identity in selected:
            return dict(identity=trail[0], chain=trail, selected_ancestor=identity)
        parent = people[identity]['parent']
        require(parent is None or type(parent) is int and 0 <= parent < identity, 'ancestry decreases')
        identity = parent
    return dict(identity=trail[0], chain=trail, selected_ancestor=None)


@lru_cache(maxsize=4096)
def translation_signature(points):
    """Enumerate every torus translation, independent of production anchoring."""
    best = None
    for dx in range(16):
        for dy in range(16):
            shifted = tuple(sorted(((x + dx) % 16, (y + dy) % 16, *attributes)
                                   for x, y, *attributes in points))
            if best is None or shifted < best: best = shifted
    return best


def observe(template, units, ids, people, original_t0):
    observed = partition(units, ids, 16, 16, 'final')
    locations = {identity: site for site, identity in enumerate(ids) if identity is not None}
    target_locations = {identity: site for site, identity in enumerate(template['site_ids']) if identity in (0, 1)}
    same(sorted(target_locations), [0, 1], 'original two-member template')
    def signature(members, positions, population, genetic):
        points = []
        for i in members:
            s = positions[i]; u = population[s]
            points.append((s % 16, s // 16, u['material'], *((tuple(u['program']),) if genetic else ())))
        return translation_signature(tuple(points))
    full_target = signature((0, 1), target_locations, template['units'], True)
    material_target = signature((0, 1), target_locations, template['units'], False)
    components, copies = [], []
    for index, members in enumerate(observed['components']['material']):
        genetic = signature(members, locations, units, True)
        material_match = signature(members, locations, units, False) == material_target
        witnesses = []
        for i in members:
            person, site = people[i], locations[i]
            witnesses.append(dict(identity=i, site=site, birth_site=person['site'], birth_tick=person['birth_tick'],
                parent=person['parent'], founder=person['founder'], generation=person['generation'],
                material=units[site]['material'], program=list(units[site]['program']),
                ancestor_chain=ancestry(i, people, (0, 1))['chain'],
                born_after_original_t0=person['birth_tick'] > original_t0,
                born_after_tick32=person['birth_tick'] > 32))
        c = dict(component=index, members=list(members), sites=[locations[i] for i in members],
                 fingerprint=json_value(genetic), material_matches=material_match, full_program_matches=genetic == full_target,
                 original_ancestry=all(people[i]['founder'] in (0, 1) for i in members),
                 excludes_original_members=all(i not in (0, 1) for i in members), member_witnesses=witnesses)
        c['genetic_copy'] = len(members) == 2 and c['full_program_matches'] and c['original_ancestry']
        c['all_new'] = c['genetic_copy'] and c['excludes_original_members']
        components.append(c)
        if c['genetic_copy']:
            copies.append({k: deepcopy(c[k]) for k in ('members', 'sites', 'all_new', 'component', 'member_witnesses')})
    return dict(observation=observed, components=components, copies=copies,
                new_copy_count=sum(1 for c in copies if c['all_new']), template_fingerprint=json_value(full_target))


def reconstruct_prefix(boundary, budget=lambda: None):
    """Validate saved prefix identities and independently observe its components.

    No prefix physics is run. Full history at the intervention is saved source
    evidence; later identities are replayed solely from saved birth/death events.
    """
    initial = boundary['prefix_initial']
    ids, people = deepcopy(initial['site_ids']), deepcopy(initial['individuals'])
    same(initial['parents'], [p['parent'] for p in people], 'prefix historical parents')
    rows = []
    for saved in boundary['prefix_rows']:
        budget()
        births, deaths = advance_identities(ids, people, saved['physical'])
        same([saved['births'], saved['deaths'], saved['site_ids']], [births, deaths, ids], 'prefix passive identity replay')
        observed = observe(boundary['template'], saved['physical']['units'], ids, people, boundary['item']['t0'])
        same(saved['observation'], observed['observation'], 'prefix independently observed components')
        copies = [{k: deepcopy(c[k]) for k in ('members', 'sites', 'all_new')} for c in observed['copies']]
        same(saved['copies'], copies, 'prefix independently matched copies')
        rows.append(dict(tick=saved['tick'], copies=copies))
    state = boundary['initial']
    same([ids, people, [p['parent'] for p in people]], [state['site_ids'], state['individuals'], state['parents']], 'full boundary history independently rebuilt')
    return rows


def runs(ticks):
    """Inclusive runs via start/end transitions, including an explicit sentinel."""
    values = sorted(set(ticks))
    result = []
    start = previous = None
    for tick in [*values, None]:
        if start is not None and (tick is None or tick != previous + 1):
            result.append([start, previous]); start = None
        if tick is not None and start is None: start = tick
        previous = tick
    return result


def temporal(counts, q32, prefix_rows, original_t0):
    require(type(counts) is list and len(counts) == 32 and all(type(c) is int and c >= 0 for c in counts), 'full future counts')
    inputs.integer(q32, 0, 3, 'boundary actual count')
    intervals = []
    for first, last in runs(33 + i for i in range(32) if counts[i] >= 2):
        intervals.append(dict(start=first, end=last, length=last - first + 1,
                              left_censored_at_boundary=first == 33 and q32 >= 2, right_censored=last == 64))
    cross = None
    if q32 >= 2 and counts[0] >= 2:
        lookup = {r['tick']: sum(1 for c in r['copies'] if c['all_new']) for r in prefix_rows}
        require(lookup.get(32, 0) >= 2, 'prefix terminal agrees with independent tick32')
        first = 32
        while lookup.get(first - 1, 0) >= 2: first -= 1
        end = intervals[0]['end']
        cross = dict(prefix_start=first, prefix_end=32, future_start=33, future_end=end,
                     prefix_length=33 - first, future_length=end - 32, combined_observed_length=end - first + 1,
                     prefix_left_censored_at_original_intervention=first == original_t0 + 1,
                     right_censored=end == 64, combined_persistent10=end - first >= 9)
    longest = max([0] + [r['length'] for r in intervals])
    return dict(intervals=intervals, cross_boundary=cross, longest_double=longest, future_persistent10=longest >= 10)


def support(rows, people, original_t0, selected):
    result = {'metrics': {}}
    def born(i):
        return dict(identity=i, birth_tick=people[i]['birth_tick'], parent=people[i]['parent'], site=people[i]['site'])
    for threshold, prefix in ((original_t0, ''), (32, 'after32_')):
        formations, upper, ancestral_ticks = [], [], set()
        for row in rows:
            copies = [c for c in row['copies'] if c['all_new']]
            if len(copies) < 2: continue
            births = [born(i) for c in copies for i in c['members'] if people[i]['birth_tick'] > threshold]
            if births: formations.append(dict(tick=row['tick'], copies=[list(c['members']) for c in copies], births=births))
            for copy in copies:
                if set(copy['sites']) != {85, 86} or any(people[i]['birth_tick'] <= threshold for i in copy['members']): continue
                chains = [ancestry(i, people, selected) for i in copy['members']]
                upper.append(dict(tick=row['tick'], members=list(copy['members']), sites=list(copy['sites']),
                                  births=[born(i) for i in copy['members']], selected_ancestry=chains))
                if all(c['selected_ancestor'] is not None for c in chains): ancestral_ticks.add(row['tick'])
        formation_ticks = {w['tick'] for w in formations}; upper_ticks = {w['tick'] for w in upper}
        for index, ticks in enumerate((formation_ticks, upper_ticks, ancestral_ticks)):
            result['metrics'][prefix + SUPPORT[index]] = int(len(ticks) > 0)
            result['metrics'][prefix + SUPPORT[index + 3]] = int(any(b - a >= 9 for a, b in runs(ticks)))
        result[prefix + 'formation_witnesses'] = formations
        result[prefix + 'upper_witnesses'] = upper
    return result


def gates_for(physical):
    proposals = physical['material']['proposals']; units = physical['interaction_units']
    raw = physical['raw'][:]
    for p in proposals:
        if p['reason'] == 'formed': raw[p['target']] += 1
    candidates = {}
    for p in proposals:
        source, target = units[p['source']], units[p['target']]
        if source['energy'] >= 16 and (target is None or target['energy'] == 0) and raw[p['target']] > 0:
            candidates.setdefault(p['target'], []).append(p['source'])
    output = []
    for p in proposals:
        unit, target = units[p['source']], units[p['target']]
        n = len(candidates.get(p['target'], []))
        output.append(dict(source=p['source'], target=p['target'], direction=p['direction'], reason=p['reason'],
            source_energy=unit['energy'], energy_sufficient=unit['energy'] >= 16,
            target_empty=target is None or target['energy'] == 0, raw_available=raw[p['target']] > 0,
            candidate_count=n, no_collision=n == 1, parent_program=list(unit['program']),
            expressed_material=unit['program'][p['direction']], mutation_ticket=list(physical['mutation_tickets'][p['source']]),
            construction_cost=4, copy_cost=1))
    return output


def reconstruct_arm(boundary, natural, name, budget=lambda: None, progress=None, partial=None):
    same([r['tick'] for r in natural], list(range(33, 65)), 'all fixed future ticks')
    progress = {} if progress is None else progress
    result = {} if partial is None else partial
    initial = restore_state(boundary['initial']); item = boundary['item']
    ids, people = deepcopy(initial['site_ids']), deepcopy(initial['individuals'])
    units, raw = deepcopy(initial['units']), initial['raw'][:]
    rows = []
    result.update(status='running', arm=name, initial=initial, original_t0=item['t0'], boundary_tick=32,
                  historical_removals=deepcopy(boundary['prefix_initial']['removals']),
                  historical_energy_export=boundary['prefix_initial']['energy_export'], rows=rows)
    diagnostic = observe(boundary['template'], units, ids, people, item['t0'])
    result['tick32_diagnostic'] = diagnostic
    for ticket in natural:
        budget(); tick = ticket['tick']
        progress.update(active_arm=name, active_tick=tick, stage='dictionary_physics')
        tape = dict(tick=tick, directions=directions_for(ticket['directions'], name),
                    mutation_tickets=[[999, 0, 1] for _ in range(256)],
                    driven=dict(inputs=[dict(site=s, proposed=8 if s in (85, 86, 117, 118) else 0) for s in range(256)]))
        previous_living = sum(i is not None for i in ids)
        before_energy = sum(u['energy'] for u in units if u is not None)
        physical = physical_step(units, raw, inputs.CONFIG, tape, False)
        progress['physical_steps'] = progress.get('physical_steps', 0) + 1
        progress.update(last_physical_tick=tick, stage='physical_saved_in_memory')
        physical = json_value(physical)
        row = dict(tick=tick, status='physical_complete', physical=physical); rows.append(row)
        same(physical['energy'], before_energy + physical['imported'] - physical['spent'], 'dictionary energy')
        same([physical['material_before'], physical['material_after'],
              sum(physical['raw']) + sum(u is not None for u in physical['units'])], [7, 7, 7], 'dictionary mass')
        births, deaths = advance_identities(ids, people, physical)
        row.update(site_ids=ids[:], births=births, deaths=deaths)
        units, raw = physical['units'], physical['raw']
        same(sum(i is not None for i in ids), previous_living + len(births) - len(deaths), 'identity population')
        result['last_observer_state'] = dict(tick=tick, alive=ids[:], individuals=deepcopy(people), founders=3)
        row.update(observe(boundary['template'], units, ids, people, item['t0']))
        row['proposal_gates'] = gates_for(physical)
        row['failure_counts'] = {reason: len([p for p in physical['material']['proposals'] if p['reason'] == reason]) for reason in REASONS}
        row['selected_lineage'] = []
        for original in item['selection']['offspring_ids']:
            descendants = sorted(i for i in ids if i is not None and ancestry(i, people, (original,))['selected_ancestor'] is not None)
            row['selected_lineage'].append(dict(identity=original, alive=original in ids, living_descendants=descendants))
        row['status'] = 'complete'; progress.update(stage='observation_complete', last_observed_tick=tick); budget()
    final = dict(tick=64, units=deepcopy(units), raw=list(raw), site_ids=list(ids), parents=[p['parent'] for p in people], individuals=deepcopy(people))
    counts = [r['new_copy_count'] for r in rows]
    timing = temporal(counts, diagnostic['new_copy_count'], boundary['prefix_rows'], item['t0'])
    births = support(rows, people, item['t0'], item['selection']['offspring_ids'])
    metrics = dict.fromkeys(METRICS, 0)
    paths = dict(imported=('imported',), rejected_import=('rejected_import',), spent=('spent',),
                 leakage=('driven', 'leakage'), bond_spent=('driven', 'interaction', 'spent'),
                 construction_spent=('material', 'construction_spent'), copy_spent=('material', 'copy_spent'))
    for row in rows:
        metrics['births'] += len(row['births']); metrics['deaths'] += len(row['deaths'])
        for key, path in paths.items():
            value = row['physical']
            for part in path: value = value[part]
            metrics[key] += value
    metrics.update(living=sum(i is not None for i in ids), final_energy=sum(u['energy'] for u in units if u is not None),
                   new_copy_ever=int(max(counts) > 0), double_new_ever=int(max(counts) >= 2),
                   persistent10=int(timing['future_persistent10']), future_persistent10=int(timing['future_persistent10']),
                   longest_double=timing['longest_double'], **births.pop('metrics'))
    ledger = dict(initial_energy=sum(u['energy'] for u in initial['units'] if u is not None),
                  initial_living=sum(i is not None for i in initial['site_ids']), initial_mass=7, final_mass=7,
                  energy_export=0, future_births=metrics['births'], future_natural_deaths=metrics['deaths'])
    same(metrics['final_energy'], ledger['initial_energy'] + metrics['imported'] - metrics['spent'], 'total future energy')
    same(metrics['living'], ledger['initial_living'] + metrics['births'] - metrics['deaths'], 'total future population')
    same(metrics['spent'], sum(metrics[k] for k in ('leakage', 'bond_spent', 'construction_spent', 'copy_spent')), 'all spending categories')
    result.update(status='complete', final=final, metrics=metrics, ledger=ledger, new_copy_counts=counts,
                  failure_counts={r: sum(row['failure_counts'][r] for row in rows) for r in REASONS}, **timing, **births)
    del result['last_observer_state']
    return result


def reconstruct_pair(boundary, natural, budget=lambda: None, progress=None, partial=None):
    result = {} if partial is None else partial
    item = boundary['item']; tape = json_value(natural)
    result.update(schema=inputs.SCHEMA, status='running', encoding=item['encoding'], seed=item['seed'],
                  selection=deepcopy(item['selection']), boundary=deepcopy(item['boundary']), original_template=deepcopy(boundary['template']),
                  natural_tape=tape, natural_tape_sha256=inputs.object_hash(tape), fixed_future_ticks=[33, 64],
                  full_case_expected_steps=64, interpretation=INTERPRETATION)
    for name in ARMS:
        result[name] = {}
        reconstruct_arm(boundary, natural, name, budget, progress, result[name])
    same(result[ARMS[0]]['initial'], result[ARMS[1]]['initial'], 'identical paired complete boundary')
    result['delta'] = {key: result[ARMS[1]]['metrics'][key] - result[ARMS[0]]['metrics'][key] for key in METRICS}
    result['status'] = 'complete'
    return result


def record_for(case, path):
    same(case['status'], 'complete', 'only complete scientific cases')
    record = dict(encoding=case['encoding'], seed=case['seed'], case=path, delta=deepcopy(case['delta']))
    for name in ARMS: record[name + '_metrics'] = deepcopy(case[name]['metrics'])
    for field in ('intervals', 'cross_boundary'):
        record[field] = {name: deepcopy(case[name][field]) for name in ARMS}
    return record


def build_index(census, records, mode):
    require(mode in ('engineering', 'formal'), 'index execution mode')
    grid = [(e, s) for e in ENCODINGS for s in inputs.SEEDS]
    same([(c['encoding'], c['seed']) for c in census['cases']], grid, '100 original ordered entries')
    by_key = {(r['encoding'], r['seed']): r for r in records}
    same(len(by_key), len(records), 'unique paired records')
    selected = [(c['encoding'], c['seed']) for c in census['cases'] if c['trigger']]
    expected = [('east', 120005)] if mode == 'engineering' else selected
    same(sorted(by_key), sorted(expected), 'entire stage record cohort')
    output = []
    for c in census['cases']:
        row = {k: deepcopy(c[k]) for k in ('encoding', 'seed', 'source', 'trigger', 't0', 'remaining', 'short_window', 'applicability', 'selection')}
        key = (c['encoding'], c['seed'])
        if key in by_key:
            row.update(future_status='complete', future=deepcopy(by_key[key]))
        else:
            row.update(future_status='not_run_engineering' if c['trigger'] else 'not_applicable_original_32_no_trigger', future=None)
        output.append(row)
    return output


def group_statistics(records):
    n = len(records)
    arm_totals = {name: {m: 0 for m in METRICS} for name in ARMS}
    totals = dict.fromkeys(METRICS, 0)
    signs = {name: dict.fromkeys(METRICS, 0) for name in ('positive', 'negative', 'tie')}
    binary = {m: {(c, w): 0 for c in (0, 1) for w in (0, 1)} for m in BINARY}
    for row in records:
        for m in METRICS:
            c, w = (row[name + '_metrics'][m] for name in ARMS)
            require(type(c) is int and type(w) is int, 'integer scientific metric')
            same(row['delta'][m], w - c, 'withdraw minus continue')
            arm_totals[ARMS[0]][m] += c; arm_totals[ARMS[1]][m] += w
            totals[m] += w - c
            signs['positive' if w > c else 'negative' if w < c else 'tie'][m] += 1
            if m in binary:
                require(c in (0, 1) and w in (0, 1), 'binary endpoint')
                binary[m][c, w] += 1
    means = {}
    for m, value in totals.items():
        if n == 0: means[m] = None; continue
        common = gcd(value, n); numerator, denominator = value // common, n // common
        means[m] = str(numerator) if denominator == 1 else f'{numerator}/{denominator}'
    return dict(n=n, arm_totals=arm_totals, delta_totals=totals, mean_delta=means, **signs,
                binary_pairs={m: [dict(continue_north=c, withdraw_to_natural=w, n=counts[c, w])
                                  for c in (0, 1) for w in (0, 1)] for m, counts in binary.items()})


def summarize(records, index, mode):
    require(mode in ('engineering', 'formal'), 'summary execution mode')
    same(len(index), 100, 'original index denominator')
    selected = [c for c in index if c['trigger']]
    same([len(selected), sum(c['short_window'] for c in index)], [28, 10], 'fixed selections and historical labels')
    same([sum(c['encoding'] == e for c in selected) for e in ENCODINGS], [5, 3, 0, 9, 11], 'five full encoding strata')
    same(len(records), 1 if mode == 'engineering' else 28, 'stage records')
    same([(r['encoding'], r['seed']) for r in records],
         [(c['encoding'], c['seed']) for c in index if c['future_status'] == 'complete'], 'ordered completed index correspondence')
    seeds = sorted({c['seed'] for c in selected}); same(len(seeds), 14, 'shared environmental seeds')
    cells = []; seed_groups = []
    for encoding in ENCODINGS:
        cells.append(dict(encoding=encoding, original_n=20, selected_n=sum(c['encoding'] == encoding for c in selected),
                          **group_statistics([r for r in records if r['encoding'] == encoding])))
    for seed in seeds:
        chosen = [r for r in records if r['seed'] == seed]
        seed_groups.append(dict(seed=seed, selected_encodings=[c['encoding'] for c in selected if c['seed'] == seed],
                                pairs=deepcopy(chosen), **group_statistics(chosen)))
    return dict(schema=inputs.SCHEMA, mode=mode, interpretation=INTERPRETATION, original_index=100,
                selected_pairs=28, original_no_trigger_not_applicable=72, historical_short_windows=10,
                completed_pairs=len(records), completed_physical_steps=64 * len(records), unique_active_environment_seeds=14,
                overall=group_statistics(records), cells=cells, seed_groups=seed_groups, pairs=deepcopy(records))


class Guard:
    """Work and closing leases share one absolute POSIX deadline.

    Success evidence is committed only after releasing this parent's timer. A
    short forked writer gets the remaining absolute budget and exits without
    timer teardown, so teardown failure cannot leave a successful parent epoch.
    The writer never performs science. An OS uninterruptible operation or broken
    filesystem can prevent failure persistence; it never authorizes success.
    """
    def __init__(self, started, seconds):
        require_backend = all(hasattr(signal, n) for n in ('SIGALRM', 'ITIMER_REAL', 'signal', 'getsignal', 'setitimer', 'getitimer'))
        if not require_backend or not all(hasattr(os, n) for n in ('fork', 'waitpid', 'kill')):
            raise RuntimeError('POSIX SIGALRM and fork deadline backend required')
        self.end = started + seconds
        self.work_end = self.end - min(30.0, seconds / 5)
        self.handler = None; self.installed = False

    @staticmethod
    def expired(signum, frame):
        raise inputs.DeadlineExpired('independent route deadline expired')

    def install(self):
        require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'unused process alarm required')
        self.handler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, self.expired); self.installed = True

    def call(self, action, *, work=False, slots=1):
        if not self.installed: raise RuntimeError('deadline handler not installed')
        remaining = (self.work_end if work else self.end) - time.monotonic()
        if remaining <= 0: raise inputs.DeadlineExpired('absolute route budget exhausted')
        first = None; result = None
        try:
            signal.setitimer(signal.ITIMER_REAL, max(.000001, remaining / slots))
            result = action()
        except BaseException as error: first = error
        try:
            signal.setitimer(signal.ITIMER_REAL, 0)
        except BaseException as error:
            # Never leave a live alarm throwing outside the exception boundary.
            # A broken backend invalidates every later parent action.
            self.installed = False
            try: signal.signal(signal.SIGALRM, signal.SIG_IGN)
            except BaseException: pass
            if first is None: first = error
        if first is not None: raise first
        return result

    def release(self):
        if self.handler is None: return
        # Do not restore an unknown/default handler while a timer may be live.
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, self.handler)
        self.installed = False
        self.handler = None

    def commit(self, action):
        if getattr(self, 'unreaped_child', None) is not None:
            raise RuntimeError('previous evidence writer not confirmed stopped')
        remaining = self.end - time.monotonic()
        if remaining <= 0: raise inputs.DeadlineExpired('no remaining evidence budget')
        # Retain time for recording an abnormal writer outcome in another bounded
        # writer. No work or recovery is given a new absolute route budget.
        cutoff = time.monotonic() + remaining * .6
        read_fd, write_fd = os.pipe()
        child = None; reaped = False; payload = bytearray(); first = None
        def receive():
            while True:
                try: part = os.read(read_fd, 65536)
                except BlockingIOError: return
                if not part: return
                payload.extend(part)
        try:
            os.set_blocking(read_fd, False)
            child = os.fork()
            if child == 0:
                os.close(read_fd)
                try:
                    signal.signal(signal.SIGALRM, self.expired)
                    left = cutoff - time.monotonic()
                    if left <= 0: raise inputs.DeadlineExpired('evidence writer started too late')
                    signal.setitimer(signal.ITIMER_REAL, left)
                    action()
                    os._exit(0)
                except BaseException as error:
                    # The parent drains this private pipe while waiting. Only our
                    # own child writes it: pickle is never loaded from an input.
                    detail = dict(type=type(error).__module__ + '.' + type(error).__qualname__,
                                  message=str(error), traceback=traceback.format_exc())
                    try:
                        packet = pickle.dumps((error, detail))
                        while packet:
                            count = os.write(write_fd, packet[:65536]); packet = packet[count:]
                    except BaseException:
                        pass
                    os._exit(1)
            os.close(write_fd); write_fd = None
            while time.monotonic() < cutoff:
                receive()
                pid, status = os.waitpid(child, os.WNOHANG)
                if pid:
                    reaped = True; receive()
                    if os.waitstatus_to_exitcode(status) == 0: break
                    if payload:
                        error, detail = pickle.loads(bytes(payload))
                        error.verifier_child_failure = detail
                        raise error
                    raise RuntimeError('evidence writer exited abnormally without an exception packet')
                time.sleep(min(.003, max(0, cutoff - time.monotonic())))
            if not reaped:
                raise inputs.DeadlineExpired('bounded evidence writer exceeded its remaining-budget share')
        except BaseException as error:
            first = error
        finally:
            if child not in (None, 0) and not reaped:
                self.unreaped_child = child
                try: os.kill(child, signal.SIGKILL)
                except ProcessLookupError: pass
                except BaseException as error:
                    if first is None: first = error
                cleanup_end = min(self.end, time.monotonic() + .05)
                while time.monotonic() < cleanup_end:
                    try:
                        pid, status = os.waitpid(child, os.WNOHANG)
                        if pid:
                            reaped = True; self.unreaped_child = None; break
                    except ChildProcessError:
                        reaped = True; self.unreaped_child = None; break
                    except BaseException as error:
                        if first is None: first = error
                    time.sleep(min(.001, max(0, cleanup_end - time.monotonic())))
            for fd in (read_fd, write_fd):
                if fd is not None:
                    try: os.close(fd)
                    except BaseException as error:
                        if first is None: first = error
        if first is not None: raise first


class Epoch:
    """Exclusive evidence, all independent closers, original exception identity."""
    def __init__(self, root, *, seconds=inputs.SECONDS, storage=inputs.STORAGE, enforce_deadline=False, started=None):
        self.started = time.monotonic() if started is None else started
        self.seconds = seconds; self.storage = storage
        self.guard = Guard(self.started, seconds) if enforce_deadline else None
        self.root = Path(root); self.root.mkdir(parents=False, exist_ok=False)
        self.owned = set(); self.paths = set(); self.active_case = self.active_environment = None
        self.meta = dict(schema=inputs.SCHEMA, route='verifier', status='running',
            started_at_utc=datetime.now(timezone.utc).isoformat(), physical_steps=0, future_generator_ticks=0,
            reconstructed_past_generator_ticks=0, completed_pairs=0, input_sha256={}, input_sha256_after={},
            input_read_errors_before={}, input_read_errors_after={}, output_sha256={}, output_read_errors={},
            finalization_errors={}, time_limit_seconds=seconds, storage_limit_bytes=storage)
        if self.guard: self.meta['deadline_backend'] = 'POSIX alarm; bounded fork for final evidence only'

    def size(self):
        return sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())

    def budget(self):
        if time.monotonic() >= self.started + self.seconds: raise inputs.DeadlineExpired('route elapsed budget')
        pending = sum(len(inputs.canonical(json_value(v)).encode()) for v in (self.active_case, self.active_environment) if v is not None)
        require(self.size() + pending + min(256 * 1024, self.storage // 8) < self.storage, 'route storage budget')

    def write(self, name, value):
        path = self.root / name
        require(path.resolve().is_relative_to(self.root.resolve()), 'owned output path')
        payload = (inputs.canonical(value) + '\n').encode('utf-8')
        old = path.stat().st_size if path in self.owned and path.exists() else 0
        require(self.size() - old + len(payload) < self.storage, 'projected storage budget')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('wb' if path in self.owned else 'xb') as stream:
            self.owned.add(path); stream.write(payload)

    def capture(self, paths):
        self.paths.update(map(str, paths))
        values, errors, first = inputs.capture(paths)
        for p, h in values.items():
            previous = self.meta['input_sha256'].setdefault(p, h)
            if previous != h and first is None: first = ValueError('source changed during capture: ' + p)
        self.meta['input_read_errors_before'].update(errors)
        if first is not None: raise first
        return values

    def execute(self, work, closing=()):
        first = None; work_done = False
        def attempt(label, action, slots):
            nonlocal first
            try:
                if self.guard: self.guard.call(action, slots=slots)
                else: action()
            except BaseException as error:
                self.meta['finalization_errors'][label] = repr(error)
                if first is None: first = error
        try:
            if self.guard: self.guard.install()
            def main_work():
                self.write('metadata.json', self.meta); self.budget(); work(); self.budget()
            if self.guard: self.guard.call(main_work, work=True)
            else: main_work()
            work_done = True
        except BaseException as error: first = error
        self.meta['status'] = 'closing'
        def input_after():
            values, errors, failure = inputs.capture(self.paths)
            self.meta['input_sha256_after'], self.meta['input_read_errors_after'] = values, errors
            if failure is not None: raise failure
            same(values, self.meta['input_sha256'], 'unchanged complete inputs')
        def outputs():
            paths = [p for p in self.root.rglob('*') if p.is_file() and p.name not in ('metadata.json', 'failure.json', 'proof.json')]
            values, errors, failure = inputs.capture(paths)
            self.meta['output_sha256'] = {str(Path(p).relative_to(self.root)): h for p, h in values.items()}
            self.meta['output_read_errors'] = errors
            if failure is not None: raise failure
        actions = []
        if self.active_case is not None: actions.append(('partial_case', lambda: self.write('partial-case.json', self.active_case)))
        if self.active_environment is not None: actions.append(('partial_environment', lambda: self.write('partial-environment.json', json_value(self.active_environment))))
        actions += [('closing:' + str(i), f) for i, f in enumerate(closing)]
        actions += [('input_hashes', input_after), ('output_hashes', outputs), ('final_budget', self.budget)]
        for i, (label, action) in enumerate(actions): attempt(label, action, len(actions) - i + 4)
        self.meta['work_done'] = work_done
        # Disk remains non-success through every parent timer cleanup operation.
        self.meta['status'] = 'failed' if first is not None else 'closing'
        if first is not None: self.meta['error'] = repr(first)
        attempt('precommit_metadata', lambda: self.write('metadata.json', self.meta), 3)
        if self.guard:
            for retry in range(2):
                try:
                    self.guard.release(); break
                except BaseException as error:
                    self.meta['finalization_errors']['timer_release:' + str(retry)] = repr(error)
                    if first is None: first = error
        self.meta['elapsed_seconds'] = time.monotonic() - self.started
        self.meta['status'] = 'verified' if first is None and work_done else 'failed'
        if first is not None: self.meta['error'] = repr(first)
        def commit():
            # proof first; metadata is the final success commit. Parent metadata
            # has remained closing/failed if this worker cannot finish its I/O.
            proof = dict(schema=inputs.SCHEMA, status=self.meta['status'], route='verifier',
                         scope='complete independent scientific objects; original route bytes retained',
                         output_sha256=deepcopy(self.meta['output_sha256']), input_sha256=deepcopy(self.meta['input_sha256']),
                         input_sha256_after=deepcopy(self.meta['input_sha256_after']))
            if self.meta['status'] == 'failed': self.write('failure.json', self.meta)
            self.write('proof.json', proof)
            self.budget()
            self.write('metadata.json', self.meta)
        try:
            if self.guard: self.guard.commit(commit)
            else: commit()
        except BaseException as error:
            if first is None: first = error
            self.meta.update(status='failed', error=repr(first))
            self.meta['finalization_errors']['final_evidence'] = repr(error)
            if hasattr(error, 'verifier_child_failure'):
                self.meta['child_failure'] = error.verifier_child_failure
            # No unbounded fallback when the absolute budget or backend is gone.
            def failed_commit():
                self.write('metadata.json', self.meta); self.write('failure.json', self.meta)
            try:
                if self.guard: self.guard.commit(failed_commit)
                else: failed_commit()
            except BaseException as failure:
                self.meta['finalization_errors']['failure_evidence'] = repr(failure)
        if first is not None: raise first
        return self.meta


def expected_artifacts(chosen):
    return sorted(['records.json', 'index.json', 'summary.json'] +
                  [f"cases/{c['encoding']}-{c['seed']}.json" for c in chosen] +
                  [f'environments/{s}.json' for s in sorted({c['seed'] for c in chosen})])


def validate_producer(root, mode, chosen, source_bindings, commit):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'existing read-only producer epoch')
    expected = expected_artifacts(chosen)
    files = [p for p in root.rglob('*') if p.is_file()]
    require(not any(p.is_symlink() for p in root.rglob('*')), 'no producer symlinks')
    same(sorted(str(p.relative_to(root)) for p in files), sorted(['metadata.json', *expected]), 'exact producer output inventory')
    require(sum(p.stat().st_size for p in files) < inputs.STORAGE, 'producer storage budget')
    meta = inputs.read(root / 'metadata.json')
    for key, value in dict(schema=inputs.SCHEMA, route='producer', status='complete', mode=mode,
                           git_commit=commit, planned_pairs=len(chosen), completed_pairs=len(chosen),
                           planned_physical_steps=64 * len(chosen), physical_steps=64 * len(chosen),
                           full_case_expected_steps=64, fixed_future_ticks=[33, 64], synthetic_fixture_steps=0,
                           future_generator_ticks=len({c['seed'] for c in chosen}) * 32,
                           reconstructed_past_generator_ticks=640, work_done=True).items():
        same(meta[key], value, 'producer metadata/' + key)
    same(meta['runtime'], inputs.runtime(), 'producer same frozen runtime')
    same(meta['input_sha256'], source_bindings, 'producer complete input inventory including all stage gates')
    same(meta['input_sha256_after'], source_bindings, 'producer immutable source closure')
    for key in ('input_read_errors_before', 'input_read_errors_after', 'output_read_errors', 'finalization_errors'):
        same(meta[key], {}, 'producer successful finalization/' + key)
    require(type(meta['elapsed_seconds']) is float and 0 <= meta['elapsed_seconds'] < inputs.SECONDS, 'producer time budget')
    same(sorted(meta['output_sha256']), expected, 'producer exact scientific hash inventory')
    for name in expected:
        same(inputs.digest(root / name), meta['output_sha256'][name], 'producer original bytes/' + name)
    return meta


def check_no_other_process():
    listing = subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True)
    script_names = {'run_v4_middle_withdrawal.py', 'verify_v4_middle_withdrawal.py'}
    modules = {'scripts.' + s[:-3] for s in script_names}
    for line in listing.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2 or int(parts[0]) == os.getpid(): continue
        try: words = shlex.split(parts[1])
        except ValueError: continue
        if not words: continue
        executable = Path(words.pop(0)).name
        if executable in script_names: raise ValueError('another Study047 route process')
        if not re.fullmatch(r'(?:python|pypy)(?:\d+(?:\.\d+)*)?(?:\.exe)?', executable): continue
        while words:
            token = words.pop(0)
            if token.startswith('-c') or token == '-': break
            if token == '-m' or token.startswith('-m'):
                module = words[0] if token == '-m' and words else token[2:]
                require(module not in modules, 'another Study047 route module'); break
            if token in ('-W', '-X', '--check-hash-based-pycs'):
                if words: words.pop(0)
            elif token == '--':
                require(not words or Path(words[0]).name not in script_names, 'another Study047 route script'); break
            elif not token.startswith('-'):
                require(Path(token).name not in script_names, 'another Study047 route script'); break


def run(mode, producer, output):
    started = time.monotonic()
    require(mode in ('engineering', 'formal'), 'fixed route mode')
    require(Path.cwd().resolve() == inputs.ROOT, 'launch from repository root')
    # Capability validation, stage approvals and clean git precede future input
    # reads/draws. Output is exclusive; producer bytes are only ever opened read.
    Guard(started, inputs.SECONDS)
    check_no_other_process()
    gate_paths = inputs.execution_gates(mode)
    producer, output = Path(producer).resolve(), Path(output).resolve()
    require(not output.is_relative_to(producer) and not producer.is_relative_to(output), 'separate producer and verifier epochs')
    require(not (output.exists()), 'new exclusive verifier epoch')
    epoch = Epoch(output, enforce_deadline=True, started=started)
    epoch.meta.update(mode=mode, producer_epoch=str(producer), fixed_future_ticks=[33, 64], full_case_expected_steps=64,
                      planned_pairs=1 if mode == 'engineering' else 28, planned_physical_steps=64 if mode == 'engineering' else 1792,
                      synthetic_fixture_steps=0)
    def work():
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        epoch.meta['git_commit'] = commit
        epoch.capture([inputs.SOURCES, inputs.CENSUS, inputs.REVIEW, *inputs.NEW_CODE, inputs.VERIFIER, *gate_paths, *inputs.runtime_paths()])
        paths = inputs.input_paths(include_verifier=True)
        epoch.capture(paths)
        source_bindings = inputs.bindings(include_verifier=True)
        same({p: epoch.meta['input_sha256'][p] for p in paths}, source_bindings, 'current source closure')
        source_bindings.update({p: inputs.digest(inputs.source_path(p)) for p in gate_paths})
        census = inputs.read(inputs.CENSUS); source = inputs.read(inputs.SOURCES)
        chosen = [c for c in census['cases'] if c['trigger'] and (mode == 'formal' or (c['encoding'], c['seed']) == ('east', 120005))]
        same(len(chosen), epoch.meta['planned_pairs'], 'fixed complete chosen cohort')
        # All producer bytes enter the before/after capture, including metadata.
        epoch.capture([str(p) for p in producer.rglob('*') if p.is_file()])
        validate_producer(producer, mode, chosen, source_bindings, commit)
        boundary_by_key = {}
        for item in census['cases']:
            epoch.budget()
            if item['trigger']:
                boundary = inputs.load_boundary(item)
                boundary['prefix_rows'] = reconstruct_prefix(boundary, epoch.budget)
                boundary_by_key[item['encoding'], item['seed']] = boundary
        streams = {}
        for environment in census['environments']:
            originals = {name: inputs.read(inputs.source_path(path)) for name, path in environment['origin_paths'].items()}
            streams[environment['seed']] = restore_environment(environment, originals, source['runtime'], epoch.budget)
            epoch.meta['reconstructed_past_generator_ticks'] += 32
        epoch.meta['runtime'] = inputs.runtime()
        tapes, records = {}, []
        epoch.write('records.json', records)
        for item in chosen:
            seed = item['seed']; key = item['encoding'], seed
            epoch.meta.update(active_encoding=item['encoding'], active_seed=seed)
            if seed not in tapes:
                epoch.active_environment = {}
                tapes[seed] = draw_future(streams[seed], epoch.budget, epoch.meta, epoch.active_environment)
                env = dict(seed=seed, natural_tape=json_value(tapes[seed]), sha256=inputs.object_hash(json_value(tapes[seed])),
                           states_after_tick64=deepcopy(epoch.active_environment['current_stream_states']))
                name = f'environments/{seed}.json'
                epoch.write(name, env)
                compare_artifact(inputs.read(producer / name), env, name)
                epoch.active_environment = None
            epoch.active_case = {}
            case = reconstruct_pair(boundary_by_key[key], tapes[seed], epoch.budget, epoch.meta, epoch.active_case)
            name = f"cases/{item['encoding']}-{seed}.json"
            epoch.write(name, case)
            compare_artifact(inputs.read(producer / name), case, name)
            records.append(record_for(case, name))
            epoch.meta['completed_pairs'] = len(records)
            epoch.write('records.json', records); epoch.active_case = None; epoch.budget()
        same(epoch.meta['physical_steps'], epoch.meta['planned_physical_steps'], 'actual dictionary step budget')
        same(epoch.meta['future_generator_ticks'], len(tapes) * 32, 'natural suffix generated once per active seed')
        index = build_index(census, records, mode)
        summary = summarize(records, index, mode)
        for name, value in (('records.json', records), ('index.json', index), ('summary.json', summary)):
            epoch.write(name, value); compare_artifact(inputs.read(producer / name), value, name)
        if mode == 'engineering':
            case_bytes = (epoch.root / records[0]['case']).stat().st_size
            environment_bytes = sum(p.stat().st_size for p in (epoch.root / 'environments').glob('*.json'))
            other_bytes = sum((epoch.root / n).stat().st_size for n in ('records.json', 'index.json', 'summary.json'))
            projected = case_bytes * 28 + environment_bytes * 14 + other_bytes * 28 + len(inputs.canonical(epoch.meta).encode()) * 4
            epoch.meta.update(engineering_case_bytes=case_bytes, projected_28_case_bytes=case_bytes * 28,
                              projected_full_storage_bytes=projected,
                              storage_projection_basis='首工程case×28、环境×14、索引汇总×28及来源收尾预留；正式仍逐写硬限制。')
            require(projected < inputs.STORAGE, 'engineering full-cohort storage projection')
        epoch.meta['stage'] = 'finished'
    closers = []
    for path, task in zip(gate_paths, ('2.1', '2.2', '2.3')):
        required = inputs.NEW_CODE if task == '2.1' else (*inputs.NEW_CODE, inputs.VERIFIER)
        closers.append(lambda p=path, t=task, f=required: inputs.approved_gate(p, t, f))
    return epoch.execute(work, tuple(closers))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', required=True, choices=('engineering', 'formal'))
    parser.add_argument('--producer', required=True, type=Path, help='existing read-only producer epoch')
    parser.add_argument('--output', required=True, type=Path, help='new exclusive verifier epoch')
    args = parser.parse_args(argv)
    metadata = run(args.mode, args.producer, args.output)
    print(json.dumps({k: metadata[k] for k in ('status', 'mode', 'physical_steps', 'completed_pairs', 'elapsed_seconds')}))


if __name__ == '__main__':
    main()
