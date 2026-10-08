"""Study047 paired tick33–64 continuation; explicit gated offline research CLI."""
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

# The canonical smoke invokes this file directly with PYTHONPATH=src.
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bitgenesis.v4.hereditary_growing import step
from bitgenesis.v4.heredity import HeritableUnit
from bitgenesis.v4.lineage import Observer
from bitgenesis.v4.structure import snapshot
from scripts import middle_withdrawal_inputs as inputs
from scripts.run_v4_founder_removal import match_copies, ancestry
from scripts.analyze_v4_structure_copies import canonical as fingerprint

ARMS = inputs.ARMS
ENCODINGS = inputs.ENCODINGS
CONFIG = inputs.CONFIG
require = inputs.require
same = inputs.same
REASONS = ('energy', 'occupied', 'raw_material', 'collision', 'formed')
SUPPORT_METRICS = ('formation_supported', 'upper_formed', 'selected_ancestry_supported',
                   'formation_persistent10', 'upper_persistent10', 'selected_ancestry_persistent10')
METRICS = ('births', 'deaths', 'living', 'final_energy', 'imported', 'rejected_import',
           'spent', 'leakage', 'bond_spent', 'construction_spent', 'copy_spent',
           'new_copy_ever', 'double_new_ever', 'persistent10', 'future_persistent10',
           'longest_double', *SUPPORT_METRICS, *('after32_' + k for k in SUPPORT_METRICS))
BINARY_METRICS = ('new_copy_ever', 'double_new_ever', 'persistent10', 'future_persistent10',
                  *SUPPORT_METRICS, *('after32_' + k for k in SUPPORT_METRICS))
INTERPRETATION = ('既定北向前缀后的完整方向政策撤除效果；方向同时影响程序材料表达；'
                  '人工初态与外部供能保持，不估计从未干预或自主生命出现；同seed编码相关。')


@dataclass(frozen=True)
class NaturalTicket:
    tick: int
    directions: tuple
    feed_sites_draw_order: tuple

    def __getitem__(self, key):
        return getattr(self, key)


def normalized(value):
    def encode(item):
        if is_dataclass(item): return asdict(item)
        raise TypeError('unsupported JSON object: ' + type(item).__name__)
    return json.loads(json.dumps(value, allow_nan=False, default=encode))


def restore_observer(state):
    inputs.validate_state(state)
    # Empty initialization creates no new founders or identities.
    observer = Observer([None] * 256)
    observer.tick = 32
    observer.founders = 3
    observer.alive = deepcopy(state['site_ids'])
    observer.individuals = deepcopy(state['individuals'])
    same(dict(tick=observer.tick, founders=observer.founders, alive=observer.alive,
              individuals=observer.individuals),
         dict(tick=32, founders=3, alive=state['site_ids'], individuals=state['individuals']), 'exact restored observer')
    return observer


def restore_environment(boundary, originals, frozen_runtime, budget=lambda: None):
    """Independently consume saved ticks1–32 and verify the full method checkpoint.

    No future draws occur here. Lists from JSON must become recursive tuples for
    Random.setstate; normalized getstate is checked before returning the streams.
    """
    same(inputs.runtime(), frozen_runtime, 'frozen random runtime')
    seed = boundary['seed']; integer_seed = type(seed) is int
    require(integer_seed, 'integer seed')
    for mode in ('random-direction', 'random-both'):
        case = originals[mode]
        same([case['seed'], case['mode'], case['exchange'], case['config'], len(case['rows'])],
             [seed, mode, False, CONFIG, 32], 'original environment identity')
    streams = {kind: inputs.new_stream(seed, kind) for kind in ('directions', 'feeds')}
    past = []
    for tick in range(1, 33):
        budget()
        directions = [streams['directions'].randrange(4) for _ in range(256)]
        feeds = streams['feeds'].sample(range(256), 4)
        for mode, case in originals.items():
            p = case['rows'][tick - 1]['physical']
            same(p['tick'], tick, 'past physical tick')
            same(p['directions'], directions, 'past natural directions')
            same(p['mutation_tickets'], inputs.fixed_tickets(), 'constant past mutation')
            same([v['site'] for v in p['driven']['inputs']], list(range(256)), 'ordered complete feed sites')
            proposed = inputs.fixed_proposals() if mode == 'random-direction' else [8 if s in feeds else 0 for s in range(256)]
            same([v['proposed'] for v in p['driven']['inputs']], proposed, 'past feed proposals')
        past.append(dict(tick=tick, directions=directions, feed_sites_draw_order=feeds))
    same(inputs.object_hash(past), boundary['tape_sha256'], 'past natural tape hash')
    same([p['feed_sites_draw_order'] for p in past], boundary['past_feed_sites_draw_order'], 'ordered past samples')
    same(boundary['past_ticks'], 32, 'checkpoint boundary')
    restored = {}
    for kind, stream in streams.items():
        saved = boundary['states_after_tick32'][kind]
        same(normalized(stream.getstate()), saved, 'reconstructed complete RNG state')
        same(inputs.object_hash(saved), boundary['state_sha256'][kind], 'checkpoint state hash')
        rng = inputs.new_stream(seed, kind)
        rng.setstate(inputs.tuples(saved))
        same(normalized(rng.getstate()), saved, 'restored RNG roundtrip')
        restored[kind] = rng
    return restored


def future_tape(streams, budget=lambda: None, progress=None, partial=None, checkpoint=None):
    """Exactly32 future tickets once per seed; retain partial draws on failure."""
    result = [] if partial is None else partial
    require(not result, 'future tape starts empty')
    first = None
    try:
        for tick in range(33, 65):
            budget()
            pending = dict(tick=tick, directions=[], feed_sites_draw_order=None)
            if checkpoint is not None:
                checkpoint.update(status='running', pending_tick=pending)
            for _ in range(256):
                pending['directions'].append(streams['directions'].randrange(4))
                if progress is not None:
                    progress['future_direction_values'] = progress.get('future_direction_values', 0) + 1
            pending['feed_sites_draw_order'] = streams['feeds'].sample(range(256), 4)
            result.append(NaturalTicket(tick, tuple(pending['directions']), tuple(pending['feed_sites_draw_order'])))
            if progress is not None:
                progress['future_generator_ticks'] = progress.get('future_generator_ticks', 0) + 1
            if checkpoint is not None:
                checkpoint['pending_tick'] = None
        if checkpoint is not None: checkpoint['status'] = 'complete'
    except BaseException as error:
        first = error
        if checkpoint is not None: checkpoint['status'] = 'failed'
    finally:
        if checkpoint is not None:
            checkpoint['current_stream_states'] = {}
            checkpoint['state_capture_errors'] = {}
            for kind, stream in streams.items():
                try:
                    checkpoint['current_stream_states'][kind] = normalized(stream.getstate())
                except BaseException as error:
                    checkpoint['status'] = 'failed'
                    checkpoint['state_capture_errors'][kind] = repr(error)
                    if first is None: first = error
    if first is not None: raise first
    return tuple(result)


def arm_directions(natural, name):
    require(name in ARMS, 'fixed arm name')
    require(len(natural) == 256 and all(type(d) is int and d in range(4) for d in natural), 'complete natural directions')
    directions = list(natural)
    if name == 'continue_north':
        directions[101] = directions[102] = 3
    return directions


def observe_components(template, units, ids, people, original_t0):
    observation = snapshot(units, ids, 16, 16, phase='final')
    matches = match_copies(template, units, ids, observation, people)
    sites = {i: s for s, i in enumerate(ids) if i is not None}
    target_sites = {i: s for s, i in enumerate(template['site_ids']) if i is not None}
    def fp(members, us, locations, program=True):
        return normalized(fingerprint([(locations[i] % 16, locations[i] // 16, us[locations[i]]['material'],
                                       *([tuple(us[locations[i]]['program'])] if program else [])) for i in members]))
    target = fp([0, 1], template['units'], target_sites)
    target_material = fp([0, 1], template['units'], target_sites, False)
    def witness(i):
        p = people[i]
        return dict(identity=i, site=sites[i], birth_site=p['site'], birth_tick=p['birth_tick'],
                    parent=p['parent'], founder=p['founder'], generation=p['generation'],
                    material=units[sites[i]]['material'], program=deepcopy(units[sites[i]]['program']),
                    ancestor_chain=ancestry(i, people, (0, 1))['chain'],
                    born_after_original_t0=p['birth_tick'] > original_t0,
                    born_after_tick32=p['birth_tick'] > 32)
    components = []
    for index, members in enumerate(observation['components']['material']):
        full = fp(members, units, sites)
        component = dict(component=index, members=list(members), sites=[sites[i] for i in members],
                         fingerprint=full, material_matches=fp(members, units, sites, False) == target_material,
                         full_program_matches=full == target,
                         original_ancestry=all(people[i]['founder'] in (0, 1) for i in members),
                         excludes_original_members=not bool(set(members) & {0, 1}),
                         member_witnesses=[witness(i) for i in members])
        component['genetic_copy'] = len(members) == 2 and component['full_program_matches'] and component['original_ancestry']
        component['all_new'] = component['genetic_copy'] and component['excludes_original_members']
        components.append(component)
    copies = []
    for match in matches:
        component = next(c for c in components if c['members'] == match['members'])
        copies.append(dict(deepcopy(match), component=component['component'], member_witnesses=deepcopy(component['member_witnesses'])))
    same(sum(c['all_new'] for c in copies), sum(c['all_new'] for c in components), 'whole component count')
    return dict(observation=observation, components=components, copies=copies,
                new_copy_count=sum(c['all_new'] for c in copies), template_fingerprint=target)


def intervals(ticks):
    result = []
    for tick in ticks:
        if result and result[-1][1] == tick - 1:
            result[-1][1] = tick
        else:
            result.append([tick, tick])
    return result


def interval_metrics(counts, q32, prefix_rows, original_t0):
    require(type(counts) is list and len(counts) == 32 and all(type(q) is int and q >= 0 for q in counts), '32 actual future counts')
    inputs.integer(q32, 0, 3, 'tick32 copy diagnosis')
    spans = intervals([t for t, q in zip(range(33, 65), counts) if q >= 2])
    result = [dict(start=a, end=b, length=b - a + 1,
                   left_censored_at_boundary=a == 33 and q32 >= 2, right_censored=b == 64) for a, b in spans]
    longest = max((s['length'] for s in result), default=0)
    cross = None
    if q32 >= 2 and counts[0] >= 2:
        old = intervals([r['tick'] for r in prefix_rows if sum(c['all_new'] for c in r['copies']) >= 2])
        require(old and old[-1][1] == 32, 'saved prefix supplies actual terminal interval')
        start, _ = old[-1]; end = result[0]['end']
        cross = dict(prefix_start=start, prefix_end=32, future_start=33, future_end=end,
                     prefix_length=33 - start, future_length=end - 32,
                     combined_observed_length=end - start + 1,
                     prefix_left_censored_at_original_intervention=start == original_t0 + 1,
                     right_censored=end == 64, combined_persistent10=end - start + 1 >= 10)
    return dict(intervals=result, cross_boundary=cross, longest_double=longest,
                future_persistent10=longest >= 10)


def birth_support(rows, people, original_t0, selected):
    result = {}; metrics = {}
    for prefix, threshold in (('', original_t0), ('after32_', 32)):
        formations, upper = [], []
        def witness(i):
            p = people[i]
            return dict(identity=i, birth_tick=p['birth_tick'], parent=p['parent'], site=p['site'])
        for row in rows:
            copies = [c for c in row['copies'] if c['all_new']]
            if len(copies) < 2:
                continue
            born = [witness(i) for c in copies for i in c['members'] if people[i]['birth_tick'] > threshold]
            if born:
                formations.append(dict(tick=row['tick'], copies=[c['members'] for c in copies], births=born))
            for c in copies:
                if sorted(c['sites']) == [85, 86] and all(people[i]['birth_tick'] > threshold for i in c['members']):
                    upper.append(dict(tick=row['tick'], members=c['members'], sites=c['sites'],
                                      births=[witness(i) for i in c['members']],
                                      selected_ancestry=[ancestry(i, people, selected) for i in c['members']]))
        ancestral = [w for w in upper if all(a['selected_ancestor'] is not None for a in w['selected_ancestry'])]
        metrics.update({prefix + 'formation_supported': int(bool(formations)),
                        prefix + 'upper_formed': int(bool(upper)),
                        prefix + 'selected_ancestry_supported': int(bool(ancestral))})
        for name, witnesses in (('formation_persistent10', formations), ('upper_persistent10', upper),
                                ('selected_ancestry_persistent10', ancestral)):
            spans = intervals(sorted({w['tick'] for w in witnesses}))
            metrics[prefix + name] = int(any(b - a + 1 >= 10 for a, b in spans))
        result[prefix + 'formation_witnesses'] = formations
        result[prefix + 'upper_witnesses'] = upper
    return dict(metrics=metrics, **result)


def proposal_gates(physical):
    """Expose every gate, even those masked by an earlier failed gate."""
    units = physical['interaction_units']; raw = list(physical['raw'])
    # Final raw plus successful use reconstructs the post-dissolution stock.
    for p in physical['material']['proposals']:
        if p['reason'] == 'formed': raw[p['target']] += 1
    live = [None if u is None or u['energy'] == 0 else u for u in units]
    candidates = Counter(p['target'] for p in physical['material']['proposals']
                         if live[p['source']]['energy'] >= CONFIG['threshold']
                         and live[p['target']] is None and raw[p['target']] >= 1)
    gates = []
    for p in physical['material']['proposals']:
        source = live[p['source']]; target = p['target']
        gates.append(dict(source=p['source'], target=target, direction=p['direction'], reason=p['reason'],
                          source_energy=source['energy'], energy_sufficient=source['energy'] >= CONFIG['threshold'],
                          target_empty=live[target] is None, raw_available=raw[target] >= 1,
                          candidate_count=candidates[target], no_collision=candidates[target] == 1,
                          parent_program=deepcopy(source['program']), expressed_material=source['program'][p['direction']],
                          mutation_ticket=deepcopy(physical['mutation_tickets'][p['source']]),
                          construction_cost=4, copy_cost=1))
    return gates


def run_arm(boundary, natural, name, budget=lambda: None, progress=None, partial=None):
    require(name in ARMS, 'fixed arm')
    same([t['tick'] for t in natural], list(range(33, 65)), 'fixed full future window')
    item = boundary['item']; state = deepcopy(boundary['initial'])
    observer = restore_observer(state)
    units = [None if u is None else HeritableUnit(u['material'], u['energy'], tuple(u['program'])) for u in state['units']]
    raw = list(state['raw']); rows = []
    progress = {} if progress is None else progress
    result = {} if partial is None else partial
    result.update(status='running', arm=name, initial=state, original_t0=item['t0'], boundary_tick=32,
                  historical_removals=deepcopy(boundary['prefix_initial']['removals']),
                  historical_energy_export=boundary['prefix_initial']['energy_export'], rows=rows)
    diagnostic = observe_components(boundary['template'], state['units'], state['site_ids'], observer.individuals, item['t0'])
    result['tick32_diagnostic'] = diagnostic
    for ticket in natural:
        budget(); tick = ticket['tick']; progress.update(active_arm=name, active_tick=tick, stage='physics')
        prior_ids = list(observer.alive); birth_start = len(observer.individuals)
        directions = arm_directions(ticket['directions'], name)
        before = sum(u.energy for u in units if u is not None)
        units, raw, event = step(units, raw, proposals=inputs.fixed_proposals(), directions=directions,
                                 mutation_tickets=[tuple(t) for t in inputs.fixed_tickets()], exchange=False, **CONFIG)
        # Count immediately after the successful kernel call, before observer/I/O.
        progress['physical_steps'] = progress.get('physical_steps', 0) + 1
        progress['last_physical_tick'] = tick; progress['stage'] = 'physical_saved_in_memory'
        physical = normalized(dict(tick=tick, units=[None if u is None else asdict(u) for u in units],
                                   raw=list(raw), energy=sum(u.energy for u in units if u is not None),
                                   directions=directions, mutation_tickets=inputs.fixed_tickets(), **event))
        row = dict(tick=tick, status='physical_complete', physical=physical)
        rows.append(row)
        same(physical['energy'], before + event['imported'] - event['spent'], 'future step energy')
        same([event['material_before'], event['material_after'], sum(raw) + sum(u is not None for u in units)], [7, 7, 7], 'future mass seven')
        observer.accept(physical)
        row.update(site_ids=list(observer.alive), births=deepcopy(observer.individuals[birth_start:]),
                   deaths=[prior_ids[s] for s in event['material']['dissolved']])
        same(sum(i is not None for i in observer.alive), sum(i is not None for i in prior_ids) + len(row['births']) - len(row['deaths']), 'future step population')
        result['last_observer_state'] = dict(tick=observer.tick, alive=list(observer.alive), individuals=deepcopy(observer.individuals), founders=3)
        row.update(observe_components(boundary['template'], physical['units'], observer.alive, observer.individuals, item['t0']))
        row['proposal_gates'] = proposal_gates(physical)
        row['failure_counts'] = {reason: sum(p['reason'] == reason for p in physical['material']['proposals']) for reason in REASONS}
        row['selected_lineage'] = [dict(identity=i, alive=i in observer.alive, living_descendants=sorted(
            j for j in observer.alive if j is not None and ancestry(j, observer.individuals, [i])['selected_ancestor'] is not None))
            for i in item['selection']['offspring_ids']]
        row['status'] = 'complete'; progress.update(stage='observation_complete', last_observed_tick=tick)
        budget()
    final = dict(tick=64, units=deepcopy(rows[-1]['physical']['units']), raw=list(raw), site_ids=list(observer.alive),
                 parents=[p['parent'] for p in observer.individuals], individuals=deepcopy(observer.individuals))
    counts = [r['new_copy_count'] for r in rows]
    temporal = interval_metrics(counts, diagnostic['new_copy_count'], boundary['prefix_rows'], item['t0'])
    support = birth_support(rows, final['individuals'], item['t0'], item['selection']['offspring_ids'])
    metrics = dict(births=sum(len(r['births']) for r in rows), deaths=sum(len(r['deaths']) for r in rows),
                   living=sum(i is not None for i in observer.alive), final_energy=rows[-1]['physical']['energy'],
                   imported=sum(r['physical']['imported'] for r in rows), rejected_import=sum(r['physical']['rejected_import'] for r in rows),
                   spent=sum(r['physical']['spent'] for r in rows), leakage=sum(r['physical']['driven']['leakage'] for r in rows),
                   bond_spent=sum(r['physical']['driven']['interaction']['spent'] for r in rows),
                   construction_spent=sum(r['physical']['material']['construction_spent'] for r in rows),
                   copy_spent=sum(r['physical']['material']['copy_spent'] for r in rows),
                   new_copy_ever=int(any(counts)), double_new_ever=int(any(q >= 2 for q in counts)),
                   persistent10=int(temporal['future_persistent10']), future_persistent10=int(temporal['future_persistent10']),
                   longest_double=temporal['longest_double'], **support.pop('metrics'))
    same(sorted(metrics), sorted(METRICS), 'complete fixed metric keys')
    ledger = dict(initial_energy=sum(u['energy'] for u in state['units'] if u is not None),
                  initial_living=sum(i is not None for i in state['site_ids']), initial_mass=7, final_mass=7,
                  energy_export=0, future_births=metrics['births'], future_natural_deaths=metrics['deaths'])
    same(metrics['final_energy'], ledger['initial_energy'] + metrics['imported'] - metrics['spent'], 'future cumulative energy no export')
    same(metrics['spent'], metrics['leakage'] + metrics['bond_spent'] + metrics['construction_spent'] + metrics['copy_spent'], 'all actual expenditure')
    same(metrics['living'], ledger['initial_living'] + metrics['births'] - metrics['deaths'], 'future cumulative population')
    result.update(status='complete', final=final, metrics=metrics, ledger=ledger, new_copy_counts=counts,
                  failure_counts={reason: sum(r['failure_counts'][reason] for r in rows) for reason in REASONS},
                  **temporal, **support)
    result.pop('last_observer_state', None)
    return result


def run_pair(boundary, natural, budget=lambda: None, progress=None, partial=None):
    progress = {} if progress is None else progress
    result = {} if partial is None else partial
    item = boundary['item']
    result.update(schema=inputs.SCHEMA, status='running', encoding=item['encoding'], seed=item['seed'],
                  selection=deepcopy(item['selection']), boundary=deepcopy(item['boundary']),
                  original_template=deepcopy(boundary['template']), natural_tape=normalized(natural),
                  natural_tape_sha256=inputs.object_hash(normalized(natural)),
                  fixed_future_ticks=[33, 64], full_case_expected_steps=64, interpretation=INTERPRETATION)
    for name in ARMS:
        result[name] = {}
        run_arm(boundary, natural, name, budget, progress, result[name])
    same(result[ARMS[0]]['initial'], result[ARMS[1]]['initial'], 'same complete paired boundary')
    result['delta'] = {k: result[ARMS[1]]['metrics'][k] - result[ARMS[0]]['metrics'][k] for k in METRICS}
    result['status'] = 'complete'
    return result


def pair_record(case, path):
    require(case['status'] == 'complete', 'no partial case used as completed result')
    return dict(encoding=case['encoding'], seed=case['seed'], case=path,
                **{name + '_metrics': deepcopy(case[name]['metrics']) for name in ARMS},
                delta=deepcopy(case['delta']),
                intervals={name: deepcopy(case[name]['intervals']) for name in ARMS},
                cross_boundary={name: deepcopy(case[name]['cross_boundary']) for name in ARMS})


def make_index(census, records, mode):
    require(mode in ('engineering', 'formal'), 'fixed index mode')
    cases = census['cases']; same([(c['encoding'], c['seed']) for c in cases],
                                  [(e, s) for e in ENCODINGS for s in inputs.SEEDS], 'full original index order')
    selected = {(c['encoding'], c['seed']) for c in cases if c['trigger']}
    mapped = {(r['encoding'], r['seed']): r for r in records}
    require(len(mapped) == len(records), 'unique completed records')
    expected = {('east', 120005)} if mode == 'engineering' else selected
    same(sorted(mapped), sorted(expected), 'complete stage cohort')
    result = []
    for item in cases:
        key = item['encoding'], item['seed']
        out = {k: deepcopy(item[k]) for k in ('encoding', 'seed', 'source', 'trigger', 't0', 'remaining', 'short_window', 'applicability', 'selection')}
        out['future_status'] = ('complete' if key in mapped else 'not_run_engineering' if item['trigger'] else 'not_applicable_original_32_no_trigger')
        out['future'] = deepcopy(mapped.get(key))
        result.append(out)
    return result


def summarize(records, index, mode):
    require(mode in ('engineering', 'formal'), 'fixed summary stage')
    same(len(index), 100, '100 original denominator entries')
    selected = [r for r in index if r['trigger']]
    same(len(selected), 28, '28 conditional denominator')
    same(sum(r['short_window'] for r in index), 10, 'ten historical short windows')
    same([sum(r['encoding'] == e for r in selected) for e in ENCODINGS], [5, 3, 0, 9, 11], 'five fixed cohort cells')
    same(len(records), 1 if mode == 'engineering' else 28, 'full stage records')
    same([(r['encoding'], r['seed']) for r in records],
         [(r['encoding'], r['seed']) for r in index if r['future_status'] == 'complete'], 'index record correspondence')
    def group(rows):
        n = len(rows); totals = {k: sum(r['delta'][k] for r in rows) for k in METRICS}
        return dict(n=n, arm_totals={name: {k: sum(r[name + '_metrics'][k] for r in rows) for k in METRICS} for name in ARMS},
                    delta_totals=totals, mean_delta={k: str(Fraction(v, n)) if n else None for k, v in totals.items()},
                    positive={k: sum(r['delta'][k] > 0 for r in rows) for k in METRICS},
                    negative={k: sum(r['delta'][k] < 0 for r in rows) for k in METRICS},
                    tie={k: sum(r['delta'][k] == 0 for r in rows) for k in METRICS},
                    binary_pairs={k: [dict(continue_north=c, withdraw_to_natural=w,
                                          n=sum(r['continue_north_metrics'][k] == c and r['withdraw_to_natural_metrics'][k] == w for r in rows))
                                      for c in (0, 1) for w in (0, 1)] for k in BINARY_METRICS})
    seeds = sorted({r['seed'] for r in selected}); same(len(seeds), 14, '14 correlated environments')
    return dict(schema=inputs.SCHEMA, mode=mode, interpretation=INTERPRETATION, original_index=100,
                selected_pairs=28, original_no_trigger_not_applicable=72, historical_short_windows=10,
                completed_pairs=len(records), completed_physical_steps=len(records) * 64,
                unique_active_environment_seeds=14, overall=group(records),
                cells=[dict(encoding=e, original_n=20, selected_n=sum(r['encoding'] == e for r in selected),
                            **group([r for r in records if r['encoding'] == e])) for e in ENCODINGS],
                seed_groups=[dict(seed=s, selected_encodings=[r['encoding'] for r in selected if r['seed'] == s],
                                  pairs=[deepcopy(r) for r in records if r['seed'] == s],
                                  **group([r for r in records if r['seed'] == s])) for s in seeds],
                pairs=deepcopy(records))


class RouteDeadline:
    """POSIX execution guard: total600s includes a30s closing reserve.

    Independent closing actions receive a fraction of the remaining total time,
    so consuming the work alarm cannot leave subsequent evidence I/O unbounded.
    No extra recovery budget is granted after the route deadline. Signal delivery
    can interrupt Python/sleep/file I/O; an OS-level uninterruptible operation or
    failed storage can still prevent evidence persistence, never justify success.
    """
    def __init__(self, started, seconds):
        required = ('SIGALRM', 'ITIMER_REAL', 'getsignal', 'signal', 'setitimer', 'getitimer')
        if not all(hasattr(signal, name) for name in required):
            raise RuntimeError('unsupported deadline backend: POSIX SIGALRM/setitimer required')
        self.started = started; self.seconds = seconds
        self.reserve = min(30.0, seconds / 10)
        self.end = started + seconds; self.work_end = self.end - self.reserve
        self.installed = False; self.prior_handler = None; self.cutoff = None
        self.phase = 'work'; self.label = 'work'; self.cleanup_errors = {}

    def install(self):
        require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'deadline backend already in use')
        self.prior_handler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, self._expired)
        self.installed = True

    def _expired(self, _signum, _frame):
        raise inputs.DeadlineExpired('producer deadline expired: ' + self.label)

    def perform(self, action, label, cutoff=None):
        if not self.installed:
            raise RuntimeError('deadline backend is not installed')
        outer, old_label = self.cutoff, self.label
        limit = cutoff if cutoff is not None else self.work_end if self.phase == 'work' else self.end
        if outer is not None: limit = min(limit, outer)
        delay = limit - time.monotonic()
        if delay <= 0:
            raise inputs.DeadlineExpired('producer deadline unavailable: ' + label)
        self.cutoff, self.label = limit, label
        first = None; value = None
        try:
            signal.setitimer(signal.ITIMER_REAL, delay)
            value = action()
        except BaseException as error:
            first = error
        finally:
            try:
                signal.setitimer(signal.ITIMER_REAL, 0)
            except BaseException as error:
                self.cleanup_errors[label + ':disarm'] = repr(error)
                if first is None: first = error
            self.cutoff, self.label = outer, old_label
            if outer is not None and outer > time.monotonic():
                try:
                    signal.setitimer(signal.ITIMER_REAL, outer - time.monotonic())
                except BaseException as error:
                    self.cleanup_errors[label + ':restore_outer'] = repr(error)
                    if first is None: first = error
        if first is not None: raise first
        return value

    def closing(self, action, label, remaining_actions):
        self.phase = 'closing'
        now = time.monotonic()
        # Leave a share for every scheduled action and final failure evidence.
        cutoff = now + max(0, self.end - now) / max(1, remaining_actions)
        return self.perform(action, label, cutoff)

    def release(self):
        first = None
        if self.installed:
            for label, action in (
                ('disarm', lambda: signal.setitimer(signal.ITIMER_REAL, 0)),
                ('restore_handler', lambda: signal.signal(signal.SIGALRM, self.prior_handler))):
                try: action()
                except BaseException as error:
                    self.cleanup_errors[label] = repr(error)
                    if first is None: first = error
            self.installed = first is not None
        if first is not None: raise first


class Epoch:
    """Exclusive bounded output ownership; all closing operations are attempted.

    Metadata starts as running; CLI preflight keeps it in memory until the
    clean Git gate passes, because an empty owned directory is Git-invisible.
    Completed is written only
    after work, closing checks, input/output hashes and budgets all succeed.
    Any BaseException keeps its original object, partial arm and captured hashes.
    A separate failure.json is attempted if metadata persistence itself fails.
    """
    def __init__(self, root, *, seconds=inputs.SECONDS, storage=inputs.STORAGE, deadline=None, defer_metadata=False):
        self.root = Path(root); self.root.mkdir(parents=False, exist_ok=False)
        self.deadline = deadline
        self.started = deadline.started if deadline is not None else time.monotonic()
        self.seconds = seconds; self.storage = storage
        self.owned = set(); self.paths = []; self.active_case = None; self.active_environment = None
        self.meta = dict(schema=inputs.SCHEMA, status='running', route='producer',
                         started_at_utc=datetime.now(timezone.utc).isoformat(), physical_steps=0,
                         future_generator_ticks=0, reconstructed_past_generator_ticks=0,
                         completed_pairs=0, time_limit_seconds=seconds, storage_limit_bytes=storage,
                         input_paths=[], input_sha256={}, input_sha256_after={},
                         input_read_errors_before={}, input_read_errors_after={}, finalization_errors={})
        if deadline is not None:
            same(seconds, deadline.seconds, 'one total route budget')
            self.meta.update(work_limit_seconds=seconds - deadline.reserve,
                             closing_reserve_seconds=deadline.reserve,
                             deadline_backend='POSIX SIGALRM', closing_action_deadlines={},
                             recovery_policy='预算内逐项有界尝试；OS不可中断调用或存储故障可能阻止证据保存，绝不记complete。')
        try:
            if deadline is not None: deadline.install()
            if not defer_metadata: self.write('metadata.json', self.meta, check=False)
        except BaseException as first:
            self.meta.update(status='failed', error=repr(first), stage='initial_metadata_reservation')
            # Never overwrite a raced foreign metadata file. Ownership is added
            # only after the exclusive open succeeds, including partial writes.
            if deadline is not None: deadline.phase = 'closing'
            if self.root / 'metadata.json' in self.owned:
                try: self.persist()
                except BaseException as error:
                    self.meta['finalization_errors']['initial_failed_metadata_write'] = repr(error)
            try: self.write('failure.json', self.meta, check=False)
            except BaseException:
                pass
            if deadline is not None:
                try: deadline.release()
                except BaseException: pass
            raise first

    def size(self):
        return sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())

    def budget(self):
        require(time.monotonic() - self.started < self.seconds, 'producer time budget')
        pending = sum(len(inputs.canonical(normalized(value)).encode()) + 1
                      for value in (self.active_case, self.active_environment) if value is not None)
        # A row can finish between two budget checks. Reserve its maximum
        # fixed256-site payload plus failure metadata before starting the step.
        margin = min(256 * 1024, self.storage // 8) if pending else 0
        require(self.size() + pending + margin < self.storage, 'producer storage budget')

    def write(self, name, value, *, check=True):
        action = lambda: self._write(name, value, check=check)
        if self.deadline is not None and self.deadline.installed:
            return self.deadline.perform(action, 'write:' + name)
        return action()

    def _write(self, name, value, *, check=True):
        path = self.root / name
        require(path.resolve().is_relative_to(self.root.resolve()), 'output within owned epoch')
        payload = (inputs.canonical(value) + '\n').encode()
        # Keep room for failure evidence; no scientific fields are pruned.
        reserve = min(1024 * 1024, self.storage // 4) if name != 'metadata.json' else 0
        old = path.stat().st_size if path in self.owned and path.exists() else 0
        require(self.size() - old + len(payload) + reserve < self.storage, 'projected output storage budget')
        if check: self.budget()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('wb' if path in self.owned else 'xb') as stream:
            self.owned.add(path)
            stream.write(payload)
        if check: self.budget()

    def persist(self):
        self.meta['elapsed_seconds'] = time.monotonic() - self.started
        self.write('metadata.json', self.meta, check=False)

    def capture(self, paths, expected=None, *, persist=True):
        self.paths = sorted(set(self.paths) | set(paths)); self.meta['input_paths'] = self.paths
        values, errors, failure = inputs.capture(paths)
        changes = {}
        for path, h in values.items():
            previous = self.meta['input_sha256'].setdefault(path, h)
            if previous != h: changes[path] = dict(before=previous, after=h)
        self.meta['input_read_errors_before'].update(errors)
        self.meta.setdefault('capture_stages', []).append(dict(files_sha256=values, read_errors=errors))
        if persist:
            try: self.persist()
            except BaseException as error:
                if failure is None: failure = error
        if failure is not None: raise failure
        require(not changes, 'source changed during input capture')
        if expected is not None: same(values, expected, 'validated captured bindings')

    def output_hashes(self):
        paths = [p for p in sorted(self.root.rglob('*')) if p.is_file() and p.name not in ('metadata.json', 'failure.json')]
        values, errors, failure = inputs.capture(paths)
        self.meta['output_sha256'] = {str(Path(p).relative_to(self.root)): h for p, h in values.items()}
        self.meta['output_read_errors'] = errors
        if failure is not None: raise failure

    def execute(self, work, closing=lambda: None):
        first = None; work_done = False; remaining_actions = 1
        def attempt(label, action):
            nonlocal first, remaining_actions
            try:
                if self.deadline is None:
                    action()
                else:
                    self.meta['closing_action_deadlines'][label] = dict(
                        remaining_route_seconds=max(0, self.deadline.end - time.monotonic()),
                        remaining_actions=remaining_actions)
                    self.deadline.closing(action, label, remaining_actions)
            except BaseException as error:
                self.meta['finalization_errors'][label] = repr(error)
                if first is None: first = error
            finally:
                remaining_actions = max(1, remaining_actions - 1)
                if self.deadline is not None:
                    self.meta['deadline_cleanup_errors'] = dict(self.deadline.cleanup_errors)
        try:
            self.budget()
            if self.deadline is None: work()
            else: self.deadline.perform(work, 'scientific_work', self.deadline.work_end)
            work_done = True
        except BaseException as error:
            first = error
        actions = []
        if self.active_environment is not None:
            actions.append(('partial_environment_write', lambda: self.write('partial-environment.json', normalized(self.active_environment), check=False)))
        if self.active_case is not None:
            actions.append(('partial_case_write', lambda: self.write('partial-case.json', self.active_case, check=False)))
        def after():
            values, errors, error = inputs.capture(self.paths)
            self.meta['input_sha256_after'] = values
            self.meta['input_read_errors_after'] = errors
            if error is not None: raise error
            same(values, self.meta['input_sha256'], 'unchanged source bytes')
        actions.extend(('closing_checks_' + str(i), action)
                       for i, action in enumerate(closing if type(closing) is tuple else (closing,)))
        actions.extend((('input_hashes', after), ('output_hashes', self.output_hashes), ('final_budget', self.budget)))
        # Five final slots: metadata, post-write budget, failed metadata,
        # independent failure proof and timer release/error recovery.
        remaining_actions = len(actions) + 5
        for label, action in actions: attempt(label, action)
        self.meta['work_done'] = work_done
        self.meta['status'] = 'complete' if first is None and work_done else 'failed'
        if first is not None: self.meta['error'] = repr(first)
        attempt('metadata_write', self.persist)
        attempt('after_metadata_budget', self.budget)
        if first is not None:
            self.meta.update(status='failed', error=repr(first))
            attempt('failed_metadata_write', self.persist)
            attempt('failure_evidence_write', lambda: self.write('failure.json', self.meta, check=False))
        if self.deadline is not None:
            try: self.deadline.release()
            except BaseException as error:
                self.meta['finalization_errors']['deadline_release'] = repr(error)
                self.meta['deadline_cleanup_errors'] = dict(self.deadline.cleanup_errors)
                if first is None: first = error
                self.meta.update(status='failed', error=repr(first))
                # A failed recovery installation may be transient: release can
                # subsequently succeed, but that does not repair saved status.
                # Permit at most two recovery installations under the SAME
                # absolute deadline. A successful installation must write failed
                # evidence even if the preceding release cleared installed.
                for recovery in range(2):
                    suffix = '' if recovery == 0 else '_second'
                    self.meta['deadline_recovery_attempts'] = recovery + 1
                    if time.monotonic() >= self.deadline.end:
                        self.meta['finalization_errors']['deadline_recovery_unavailable' + suffix] = 'original route deadline exhausted'
                        break
                    ready = False
                    try:
                        signal.signal(signal.SIGALRM, self.deadline._expired)
                        self.deadline.installed = True
                        ready = True
                    except BaseException as recovery_error:
                        self.meta['finalization_errors']['deadline_recovery_handler' + suffix] = repr(recovery_error)
                    if ready:
                        remaining_actions = 3
                        attempt('release_failure_metadata' + suffix, self.persist)
                        attempt('release_failure_evidence' + suffix, lambda: self.write('failure.json', self.meta, check=False))
                    released = False
                    try:
                        self.deadline.release()
                        released = True
                    except BaseException as recovery_error:
                        self.meta['finalization_errors']['deadline_release_retry' + suffix] = repr(recovery_error)
                    if ready and released:
                        break

        if first is not None: raise first
        return self.meta


def check_no_other_process():
    import os
    import re
    import shlex
    output = subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True)
    names = {'run_v4_middle_withdrawal.py', 'verify_v4_middle_withdrawal.py'}
    modules = {'scripts.' + name[:-3] for name in names}
    def matches(words):
        if not words: return False
        if Path(words[0]).name in names: return True
        if not re.fullmatch(r'(?:python|pypy)(?:[0-9]+(?:\.[0-9]+)*)?(?:\.exe)?', Path(words[0]).name):
            return False
        index = 1
        while index < len(words):
            word = words[index]
            if word == '-m': return index + 1 < len(words) and words[index + 1] in modules
            if word.startswith('-m'): return word[2:] in modules
            if word == '-' or word.startswith('-c'): return False
            if word in ('-W', '-X', '--check-hash-based-pycs'):
                index += 2; continue
            if word == '--':
                return index + 1 < len(words) and Path(words[index + 1]).name in names
            if word.startswith('-'):
                index += 1; continue
            return Path(word).name in names
        return False
    for line in output.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2 or int(parts[0]) == os.getpid(): continue
        try: words = shlex.split(parts[1])
        except ValueError: continue
        require(not matches(words), 'another Study047 route process is running')


def run(mode, output):
    require(mode in ('engineering', 'formal'), 'fixed run mode')
    require(Path.cwd().resolve() == inputs.ROOT, 'launch from repository root')
    # Explicitly reject unsupported platforms before any scientific work.
    deadline = RouteDeadline(time.monotonic(), inputs.SECONDS)
    gates = [inputs.BASE + 'producer-review.json', inputs.BASE + 'verifier-review.json']
    if mode == 'formal': gates.append(inputs.BASE + 'engineering-review.json')
    # Git ignores this exclusively owned EMPTY directory. Delay all output
    # files until the unchanged clean-tree/approval gates finish; failed
    # preflight still enters the same bounded epoch finalization.
    epoch = Epoch(output, seconds=inputs.SECONDS, deadline=deadline,
                  defer_metadata=True)
    epoch.meta.update(mode=mode, full_case_expected_steps=64,
                      planned_pairs=1 if mode == 'engineering' else 28,
                      planned_physical_steps=64 if mode == 'engineering' else 1792,
                      fixed_future_ticks=[33, 64], synthetic_fixture_steps=0)
    def work():
        epoch.meta['stage'] = 'git_revision_preflight'
        epoch.meta['git_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        # Retain byte bindings in memory before any process/approval read can
        # fail. Persisting here would make our own evidence dirty the Git gate.
        epoch.meta['stage'] = 'source_inventory_preflight'
        epoch.capture([inputs.SOURCES, inputs.CENSUS, inputs.REVIEW, *inputs.NEW_CODE,
                       inputs.VERIFIER, *gates, *inputs.runtime_paths()], persist=False)
        epoch.meta['stage'] = 'process_preflight'
        check_no_other_process()
        epoch.meta['stage'] = 'execution_gates'
        same(inputs.execution_gates(mode), gates, 'fixed stage approval paths')
        epoch.meta['preflight_status'] = 'passed'
        epoch.persist()
        epoch.meta['stage'] = 'source_closure'
        paths = inputs.input_paths(include_verifier=True)
        epoch.capture(paths)
        expected = inputs.bindings(include_verifier=True)
        same({p: epoch.meta['input_sha256'][p] for p in paths}, expected, 'complete source closure')
        source = inputs.read(inputs.SOURCES); census = inputs.read(inputs.CENSUS)
        frozen = census['cases']; chosen = [c for c in frozen if c['trigger']]
        if mode == 'engineering': chosen = [c for c in chosen if (c['encoding'], c['seed']) == ('east', 120005)]
        same(len(chosen), epoch.meta['planned_pairs'], 'entire stage cohort')
        # Validate all28 boundaries and all20 past streams before any future.
        boundaries = {}
        for item in frozen:
            epoch.budget()
            if item['trigger']:
                boundaries[item['encoding'], item['seed']] = inputs.load_boundary(item)
        streams = {}
        for environment in census['environments']:
            seed = environment['seed']
            originals = {mode_name: inputs.read(inputs.source_path(path)) for mode_name, path in environment['origin_paths'].items()}
            streams[seed] = restore_environment(environment, originals, source['runtime'], epoch.budget)
            epoch.meta['reconstructed_past_generator_ticks'] += 32
        epoch.meta['runtime'] = inputs.runtime(); epoch.persist(); epoch.budget()
        tapes = {}; records = []
        epoch.write('records.json', records)
        for item in chosen:
            key = item['encoding'], item['seed']; seed = item['seed']
            if seed not in tapes:
                epoch.active_environment = dict(seed=seed, natural_tape=[])
                tapes[seed] = future_tape(streams[seed], epoch.budget, epoch.meta, epoch.active_environment['natural_tape'], epoch.active_environment)
                epoch.write(f'environments/{seed}.json', dict(seed=seed, natural_tape=normalized(tapes[seed]),
                                                            sha256=inputs.object_hash(normalized(tapes[seed])),
                                                            states_after_tick64=deepcopy(epoch.active_environment['current_stream_states'])))
                epoch.active_environment = None
            partial = {}; epoch.active_case = partial
            epoch.meta.update(active_encoding=item['encoding'], active_seed=seed)
            case = run_pair(boundaries[key], tapes[seed], epoch.budget, epoch.meta, partial)
            path = f"cases/{item['encoding']}-{seed}.json"
            epoch.write(path, case)
            records.append(pair_record(case, path)); epoch.meta['completed_pairs'] = len(records)
            epoch.write('records.json', records); epoch.active_case = None; epoch.persist(); epoch.budget()
        same(epoch.meta['physical_steps'], epoch.meta['planned_physical_steps'], 'exact actual physical steps')
        same(epoch.meta['future_generator_ticks'], len({c['seed'] for c in chosen}) * 32, 'one natural future per seed')
        index = make_index(census, records, mode)
        epoch.write('index.json', index); epoch.write('summary.json', summarize(records, index, mode))
        if mode == 'engineering':
            # Bound complete future cohort storage without generating other27.
            # Also retain actual byte size; this projection is not a guarantee.
            epoch.meta['engineering_case_bytes'] = (epoch.root / records[0]['case']).stat().st_size
            epoch.meta['projected_28_case_bytes'] = epoch.meta['engineering_case_bytes'] * 28
            environment_bytes = sum(p.stat().st_size for p in (epoch.root / 'environments').glob('*.json'))
            summary_bytes = sum((epoch.root / p).stat().st_size for p in ('records.json', 'index.json', 'summary.json'))
            epoch.meta['projected_full_storage_bytes'] = (epoch.meta['projected_28_case_bytes'] +
                environment_bytes * 14 + summary_bytes * 28 + len(inputs.canonical(epoch.meta).encode()) * 4)
            epoch.meta['storage_projection_basis'] = '首工程case×28、环境×14、索引汇总×28及来源收尾预留；正式仍逐写硬限制。'
            require(epoch.meta['projected_full_storage_bytes'] < inputs.STORAGE, 'engineering full cohort storage projection exceeds budget')
        epoch.meta['stage'] = 'finished'
    def check_producer_gate():
        inputs.approved_gate(gates[0], '2.1', inputs.NEW_CODE)
    def check_verifier_gate():
        inputs.approved_gate(gates[1], '2.2', (*inputs.NEW_CODE, inputs.VERIFIER))
    return epoch.execute(work, (check_producer_gate, check_verifier_gate))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', required=True, choices=('engineering', 'formal'),
                        help='engineering: E120005 only; formal: all28 paired branches')
    parser.add_argument('--output', required=True, type=Path, help='new exclusive epoch directory; existing outputs are never overwritten')
    args = parser.parse_args(argv)
    result = run(args.mode, args.output)
    print(json.dumps({k: result[k] for k in ('status', 'mode', 'physical_steps', 'completed_pairs', 'elapsed_seconds')}))


if __name__ == '__main__':
    main()
