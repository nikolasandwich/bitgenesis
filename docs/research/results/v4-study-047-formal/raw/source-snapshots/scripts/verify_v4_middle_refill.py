"""Study046 independent saved-phase verifier; no simulator or producer imports.

This route indexes actors, post-dissolution targets, and saved events separately.
041 proposal objects are authenticated common inputs, never reclassified here.
Only the input/reference utility is shared with the production route.
"""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import argparse
import subprocess
import time

try:
    from scripts import middle_refill_inputs as inputs
except ModuleNotFoundError:  # Direct script entry point.
    import middle_refill_inputs as inputs

ENCODINGS = ('east', 'west', 'south', 'north', 'homogeneous')
ARMS = ('control', 'ablation')
STATES = ('empty_source', 'dissolved', 'not_pointing', 'energy', 'occupied',
          'raw_material', 'collision', 'formed')
REGIONS = ('upper', 'middle', 'lower', 'other')
TARGETS = (101, 102)
FORMAL = Path('data/v4-study-046')
SOURCE_COUNT = 954
TIME_LIMIT = 600
BYTE_LIMIT = 128 * 1024 * 1024


def check(condition, message):
    if not condition:
        raise ValueError(message)


def same_value(actual, expected):
    """JSON object equality with exact leaf types and ordered sequences.

    Object key order is not scientific content; sequence order and the complete
    key set are. In particular Python's bool/int/float coercion is not equality
    for this contract. Tuple/set handling serves internal structural assertions.
    """
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        if {(type(k), k) for k in actual} != {(type(k), k) for k in expected}:
            return False
        return all(same_value(actual[key], expected[key]) for key in expected)
    if isinstance(actual, (list, tuple)):
        return len(actual) == len(expected) and all(same_value(a, b) for a, b in zip(actual, expected))
    if isinstance(actual, set):
        return {(type(v), v) for v in actual} == {(type(v), v) for v in expected}
    return actual == expected


def equal(actual, expected, label):
    check(same_value(actual, expected), label + ' mismatch')


def destination(site, direction):
    check(type(direction) is int and 0 <= direction < 4, 'direction ticket')
    y, x = divmod(site, 16)
    dy, dx = ((0, 1), (0, -1), (1, 0), (-1, 0))[direction]
    return ((y + dy) % 16) * 16 + (x + dx) % 16


def incoming(target):
    # Invert the four directions geometrically instead of importing the producer table.
    return [(destination(target, reverse), forward) for reverse, forward in ((1, 0), (0, 1), (3, 2), (2, 3))]


def region(site):
    return next((r for r, sites in (('upper', (85, 86)), ('middle', TARGETS),
                                    ('lower', (117, 118))) if site in sites), 'other')


def ancestry(identity, people):
    chain = []
    while identity is not None:
        check(identity not in chain and identity in people, 'ancestry cycle or missing identity')
        chain.append(identity)
        identity = people[identity]['parent']
    return chain


def expect_ref(reader, reference, parent, suffix, value, label):
    equal(reference, reader.child_ref(parent, suffix), label + ' pointer')
    equal(reader.resolve(reference), value, label + ' value')


def stage_index(previous, row):
    """Index saved phases by site; dissolution precedes every target decision."""
    physical = row['physical']
    prior = previous.get('physical', previous)
    arrays = [previous['site_ids'], prior['units'], prior['raw'], row['site_ids'],
              physical['units'], physical['raw'], physical['interaction_units'], physical['directions']]
    check(all(isinstance(a, list) and len(a) == 256 for a in arrays), 'saved phase geometry')
    equal(physical['tick'], row['tick'], 'physical tick')
    before_ids, before_units, before_raw, after_ids, after_units, after_raw, interacting, tickets = arrays
    live, dead = {}, set()
    for site, identity in enumerate(before_ids):
        check((identity is None) == (before_units[site] is None) == (interacting[site] is None),
              'interaction/before identity presence')
        check((after_ids[site] is None) == (after_units[site] is None), 'after identity presence')
        if identity is not None:
            check(type(interacting[site]['energy']) is int and interacting[site]['energy'] >= 0,
                  'interaction energy')
            if interacting[site]['energy'] == 0:
                dead.add(site)
            else:
                live[site] = identity
    equal(sorted(dead), sorted(physical['material']['dissolved']), 'saved dissolved sites')
    equal(sorted(before_ids[s] for s in dead), sorted(row['deaths']), 'saved death identities')
    events = {}
    for number, event in enumerate(physical['material']['proposals']):
        source = event['source']
        check(source in live, 'nonacting source has saved proposal')
        check(source not in events, 'duplicate saved proposal source')
        events[source] = (number, event)
    # Every surviving actor has a saved event, including actors outside the middle neighborhood.
    equal(set(events), set(live), 'saved actor/event coverage')
    born = {}
    birth_ids = set()
    for birth in row['births']:
        check(isinstance(birth, dict) and {'id', 'parent', 'site'} <= birth.keys(), 'birth object schema')
        check(birth['site'] not in born and birth['id'] not in birth_ids, 'duplicate birth')
        check(birth['id'] not in before_ids, 'birth reused existing identity')
        born[birth['site']] = birth
        birth_ids.add(birth['id'])
    before, preformation, after = {}, {}, {}
    for target in TARGETS:
        check(type(before_raw[target]) is int and before_raw[target] >= 0, 'before raw material')
        before[target] = dict(identity=before_ids[target], material=None if before_units[target] is None
                              else before_units[target]['material'], raw=before_raw[target])
        preformation[target] = dict(identity=live.get(target), material=None if target not in live
                                    else interacting[target]['material'], raw=before_raw[target] + int(target in dead))
        after[target] = dict(identity=after_ids[target], material=None if after_units[target] is None
                              else after_units[target]['material'], raw=after_raw[target])
    return dict(before=before, preformation=preformation, after=after, live=live, dead=dead,
                events=events, births=born, prior=prior, interacting=interacting, tickets=tickets)


def authenticated_reuse(reader, encoding, branch, plan, cases):
    reuse = plan['reuse_041']
    if reuse is None:
        equal(plan['proposal_plan'], 'needed_projection', 'proposal plan')
        return None
    check(plan['arm'] == 'control' and encoding in ('east', 'west'), '041 reuse arm/encoding')
    equal(plan['proposal_plan'], 'reuse_041', '041 proposal plan')
    check(reuse['complete_old_arm_equal'] is True and reuse['proposals_reclassified'] is False,
          '041 reuse boundary')
    equal(reuse['historical_verifier_mode'], 'parent inline fallback independent algorithm', '041 historical author')
    case = reader.resolve(reuse['reference'])
    equal(case['encoding'], encoding, '041 encoding')
    equal(case['selection'], branch['selection'], '041 selection')
    check(sum(same_value(c, case) for c in cases) == 1, '041 supplied case equality/uniqueness')
    equal(reuse['old_branch']['json_pointer'], '/ablation', '039 arm pointer')
    equal(reader.resolve(reuse['old_branch']), branch['control'], '039 complete arm')
    old_document = reader.documents[reuse['old_branch']['path']]
    equal(old_document['selection'], branch['selection'], '039 selection')
    equal(len(case['rows']), len(plan['rows']), '041 row count')
    return case


def decision_links(reader, plans, arm_plan, seed, encoding):
    """Use immutable 045 boundaries to build a (tick,target) lookup, not intervals."""
    chosen = [g for g in plans if (g['encoding'], g['seed'], g['arm']) ==
              (encoding, seed, arm_plan['arm'])]
    equal([g['key'] for g in chosen], arm_plan['gap_keys'], 'gap plan order')
    links = {}
    seen = set()
    for gap in chosen:
        key = tuple(gap['key'])
        check(key not in seen, 'duplicate gap key')
        seen.add(key)
        equal(gap['key'], [encoding, seed, arm_plan['arm'], gap['reference']['json_pointer']], 'gap key')
        equal(reader.resolve(gap['reference']), gap['original'], 'original gap')
        original = gap['original']
        check(original['site'] in TARGETS and gap['intervals_recalculated'] is False, 'gap scope')
        start = arm_plan['t0'] + 1 if original['predecessor'] is None else original['start_boundary']
        stop = 32 if original['successor'] is None else original['end_boundary']
        equal(gap['decision_ticks'], list(range(start, stop + 1)), 'gap decision endpoints')
        equal(gap['decision_target_ticks'], len(gap['decision_ticks']), 'gap target budget')
        equal(gap['decision_source_slots'], 4 * len(gap['decision_ticks']), 'gap slot budget')
        for tick in gap['decision_ticks']:
            token = tick, original['site']
            check(token not in links, 'overlapping gap decisions')
            links[token] = gap['key']
    equal(len(links), arm_plan['gap_target_ticks'], 'arm gap target budget')
    equal(4 * len(links), arm_plan['gap_source_slots'], 'arm gap slot budget')
    return chosen, links


def reconstruct_pair(encoding, branch043, arm_plans, gap_plans, reuse041):
    """Build the published contract using independent phase and destination indexes."""
    branch = branch043
    selection = branch['selection']
    seed, t0 = selection['seed'], selection['t0']
    check(encoding in ENCODINGS, 'encoding')
    plans = [p for p in arm_plans if (p['encoding'], p['seed']) == (encoding, seed)]
    equal([p['arm'] for p in plans], list(ARMS), 'pair arm plans')
    result = dict(encoding=encoding, selection=deepcopy(selection), arms={})
    reader = inputs.SourceReader()
    for plan in plans:
        name = plan['arm']
        saved_arm = branch[name]
        equal(plan['key'], [encoding, seed, name], 'arm identity key')
        equal(plan['source']['json_pointer'], '/' + name, '043 arm pointer')
        equal(reader.resolve(plan['source']), saved_arm, '043 complete arm')
        equal(reader.documents[plan['source']['path']]['selection'], selection, '043 selection')
        expect_ref(reader, plan['diagnostic'], plan['source'], '/initial', saved_arm['initial'], 'diagnostic')
        equal(reader.resolve(plan['turnover_diagnostic'])['tick'], t0, 'turnover diagnostic tick')
        equal((plan['t0'], saved_arm['initial']['tick']), (t0, t0), 'initial tick')
        ticks = list(range(t0 + 1, 33))
        equal([r['tick'] for r in saved_arm['rows']], ticks, 'future ticks')
        equal([r['tick'] for r in plan['rows']], ticks, 'planned future ticks')
        equal((plan['saved_states'], plan['diagnostic_states'], plan['target_ticks'], plan['source_slots']),
              (len(ticks), 1, len(ticks)*2, len(ticks)*8), 'arm budgets')
        equal(selection['remaining_steps'], len(ticks), 'selection remaining')
        equal(plan['category'], selection['category'], 'selection category')
        old_case = authenticated_reuse(reader, encoding, branch, plan, reuse041)
        gaps, links = decision_links(reader, gap_plans, plan, seed, encoding)
        people = {p['id']: p for p in saved_arm['final']['individuals']}
        equal(len(people), len(saved_arm['final']['individuals']), 'unique individual identities')
        rows, target_index, slot_index = [], {}, {}
        previous = saved_arm['initial']
        for number, row in enumerate(saved_arm['rows']):
            tick = row['tick']
            rp = plan['rows'][number]
            expect_ref(reader, rp['source'], plan['source'], f'/rows/{number}', row, 'row source')
            suffix = '/initial' if number == 0 else f'/rows/{number-1}'
            expect_ref(reader, rp['before'], plan['source'], suffix, previous, 'row before')
            equal((rp['target_ticks'], rp['source_slots']), (2, 8), 'row budget')
            turnover = reader.resolve(rp['turnover'])
            equal(turnover['tick'], tick, 'turnover tick')
            phase = stage_index(previous, row)
            old_events = None
            if old_case is not None:
                old_row = old_case['rows'][number]
                expect_ref(reader, rp['reuse_041'], plan['reuse_041']['reference'], f'/rows/{number}', old_row, '041 row')
                equal(old_row['tick'], tick, '041 tick')
                old_events = {e['source']: (i, e) for i, e in enumerate(old_row['events'])}
                equal(len(old_events), len(old_row['events']), '041 duplicate events')
                equal(set(old_events), set(phase['events']), '041 event sources')
            else:
                check(rp['reuse_041'] is None, 'unexpected 041 row')
            # Destination buckets are formed once per target from all four geometric sources.
            buckets = {target: [] for target in TARGETS}
            actors = {}
            for source in sorted({s for t in TARGETS for s, _ in incoming(t)}):
                identity = previous['site_ids'][source]
                direction = phase['tickets'][source]
                destination_site = destination(source, direction)
                chain = [] if identity is None else ancestry(identity, people)
                selected = [i for i in chain if i in selection['offspring_ids']]
                unit = phase['prior']['units'][source]
                if identity is not None:
                    equal(people[identity]['site'], source, 'actor site')
                    equal(phase['interacting'][source]['material'], unit['material'], 'interaction material')
                    equal(phase['interacting'][source]['program'], unit['program'], 'interaction program')
                actor = dict(identity=identity, direction=direction, destination=destination_site, chain=chain,
                             selected=selected, unit=unit, energy=None if identity is None else phase['interacting'][source]['energy'])
                actors[source] = actor
                if source not in phase['live']:
                    continue
                event_number, event = phase['events'][source]
                equal((event['direction'], event['target']), (direction, destination_site), 'saved proposal destination')
                if destination_site not in TARGETS:
                    continue
                pre = phase['preformation'][destination_site]
                if old_events is not None:
                    old_number, immutable = old_events[source]
                    equal((immutable['tick'], immutable['identity'], immutable['source'], immutable['target'], immutable['direction']),
                          (tick, identity, source, destination_site, direction), '041 event identity')
                    equal((immutable['program'], immutable['energy'], immutable['chain']),
                          (unit['program'], actor['energy'], chain), '041 event phase')
                    equal(immutable['reason'], event['reason'], '041 saved reason')
                    actor['proposal'] = deepcopy(immutable)
                    actor['proposal_reference'] = reader.child_ref(rp['reuse_041'], f'/events/{old_number}')
                else:
                    enough, empty, material = actor['energy'] >= 16, pre['identity'] is None, pre['raw'] > 0
                    ancestor = selected[0] if selected else None
                    lineage = ('left' if selection['offspring_ids'].index(ancestor) == 0 else 'right') if selected else 'other'
                    actor['proposal'] = dict(tick=tick, source=source, target=destination_site, direction=direction,
                            identity=identity, program=deepcopy(unit['program']), energy=actor['energy'], target_region='middle',
                            target_raw=pre['raw'], target_occupied=not empty, target_dissolved=destination_site in phase['dead'],
                            energy_ok=enough, target_empty=empty, raw_ok=material, candidate=enough and empty and material,
                            candidate_count=0, reason=None, child_id=None, lineage=lineage, ancestor=ancestor, chain=chain)
                    actor['proposal_reference'] = reader.child_ref(rp['source'], f'/physical/material/proposals/{event_number}')
                buckets[destination_site].append(source)
            for target, sources in buckets.items():
                candidates = [s for s in sources if actors[s]['proposal']['candidate']]
                for source in sources:
                    event = actors[source]['proposal']
                    if old_events is None:
                        gates = (('energy', event['energy_ok']), ('occupied', event['target_empty']),
                                 ('raw_material', event['raw_ok']))
                        reason = next((label for label, passed in gates if not passed),
                                      'collision' if len(candidates) > 1 else 'formed')
                        event.update(reason=reason, candidate_count=len(candidates))
                        equal(reason, phase['events'][source][1]['reason'], 'saved proposal reason')
                        if reason == 'formed':
                            check(target in phase['births'], 'missing birth for formed proposal')
                            event['child_id'] = phase['births'][target]['id']
                    else:
                        # Count immutable candidate flags; no second 041 gate classification.
                        equal(event['candidate_count'], len(candidates), '041 candidate index count')
                formed = [s for s in sources if actors[s]['proposal']['reason'] == 'formed']
                check(len(formed) <= 1, 'multiple successful births')
                birth = phase['births'].get(target)
                equal(bool(formed), birth is not None, 'birth/proposal coverage')
                if birth is not None:
                    event = actors[formed[0]]['proposal']
                    equal((birth['id'], birth['parent'], birth['site']),
                          (event['child_id'], actors[formed[0]]['identity'], target), 'birth identity/parent/site')
                    check(birth['id'] in people, 'birth absent from final individuals')
                    for field in ('site', 'parent', 'birth_tick', 'material'):
                        equal(birth[field], people[birth['id']][field], 'birth final ' + field)
                    equal(birth['birth_tick'], tick, 'birth tick')
                    check(phase['preformation'][target]['identity'] is None, 'birth on occupied target')
                pre, after = phase['preformation'][target], phase['after'][target]
                equal(after['identity'], birth['id'] if birth else pre['identity'], 'birth/after target identity')
                equal(after['material'], birth['material'] if birth else pre['material'], 'birth/after target material')
                equal(after['raw'], pre['raw'] - int(birth is not None), 'after target raw')
            out = {k: deepcopy(rp[k]) for k in ('tick', 'source', 'before', 'turnover', 'reuse_041')}
            out.update(slots=[], targets=[])
            middle = {m['site']: m for m in turnover['middle']}
            equal(set(middle), set(TARGETS), 'turnover middle coverage')
            for target in TARGETS:
                equal(middle[target]['identity'], row['site_ids'][target], 'turnover identity')
                keys, real_keys, candidate_keys = [], [], []
                for source, required in incoming(target):
                    actor = actors[source]
                    if actor['identity'] is None:
                        state = 'empty_source'
                    elif source in phase['dead']:
                        state = 'dissolved'
                    elif actor['destination'] != target:
                        state = 'not_pointing'
                    else:
                        state = actor['proposal']['reason']
                    event = actor.get('proposal') if state not in STATES[:3] else None
                    key = [encoding, seed, name, tick, source, target]
                    observation = dict(key=key, tick=tick, source=source, target=target,
                        required_direction=required, source_region=region(source), direction=actor['direction'],
                        ticket_target=actor['destination'], proposal_target=actor['destination'] if source in phase['live'] else None,
                        identity=actor['identity'], material=None if actor['unit'] is None else actor['unit']['material'],
                        program=None if actor['unit'] is None else deepcopy(actor['unit']['program']),
                        ancestry_chain=actor['chain'], selected_ancestors=actor['selected'], interaction_energy=actor['energy'],
                        end_identity=row['site_ids'][source], state=state, proposal=deepcopy(event),
                        proposal_reference=deepcopy(actor['proposal_reference']) if event else None,
                        source_mode='reuse_041' if event and old_events is not None else 'source_projection',
                        gap_key=deepcopy(links.get((tick, target))))
                    keys.append(key)
                    if event:
                        real_keys.append(key)
                        if event['candidate']:
                            candidate_keys.append(key)
                    out['slots'].append(observation)
                    slot_index[tuple(key)] = observation
                target_row = dict(key=[encoding, seed, name, tick, target], tick=tick, target=target,
                       before=phase['before'][target], preformation=phase['preformation'][target], after=phase['after'][target],
                       slot_keys=keys, proposal_keys=real_keys, candidate_keys=candidate_keys,
                       birth=deepcopy(phase['births'].get(target)),
                       turnover_flags={k: turnover[k] for k in ('B101', 'B102', 'G', 'actual_double_new')},
                       turnover=deepcopy(rp['turnover']), gap_key=deepcopy(links.get((tick, target))))
                out['targets'].append(target_row)
                target_index[tick, target] = target_row
            rows.append(out)
            previous = row
        connected = []
        for gap in gaps:
            targets = [target_index[t, gap['original']['site']] for t in gap['decision_ticks']]
            chosen_slots = [slot_index[tuple(key)] for target in targets for key in target['slot_keys']]
            connected.append(dict(key=deepcopy(gap['key']), reference=deepcopy(gap['reference']),
                original=deepcopy(gap['original']), decision_ticks=deepcopy(gap['decision_ticks']),
                target_keys=[t['key'] for t in targets], slot_keys=[s['key'] for s in chosen_slots],
                sequence=[dict(tick=t['tick'], target_key=t['key'], slot_keys=t['slot_keys'],
                    states=[slot_index[tuple(k)]['state'] for k in t['slot_keys']], real_proposals=len(t['proposal_keys']),
                    candidate_count=len(t['candidate_keys']), birth_id=None if t['birth'] is None else t['birth']['id']) for t in targets],
                counts=tabulate(chosen_slots, targets), intervals_recalculated=False))
        result['arms'][name] = dict(arm=name, t0=t0, saved_steps=len(rows), source=deepcopy(plan['source']),
            diagnostic=dict(source=deepcopy(plan['diagnostic']), turnover=deepcopy(plan['turnover_diagnostic'])),
            proposal_plan=plan['proposal_plan'], reuse_041=deepcopy(plan['reuse_041']), rows=rows, gaps=connected)
    return result


def tabulate(slots, targets):
    """Histogram aggregation from observations, with explicit empty Cartesian cells."""
    def histogram(items):
        frequency = Counter(s['state'] for s in items)
        return dict(source_slots=len(items), real_proposals=sum(s['proposal'] is not None for s in items),
                    eligible_candidates=sum(s['proposal'] is not None and s['proposal']['candidate'] for s in items),
                    births=frequency['formed'], states={s: frequency[s] for s in STATES})
    result = histogram(slots)
    result['target_ticks'] = len(targets)
    result['gap_target_ticks'] = sum(t['gap_key'] is not None for t in targets)
    result['gap_source_slots'] = sum(s['gap_key'] is not None for s in slots)
    result['cross_counts'] = {r: {where: histogram([s for s in slots if s['source_region'] == r and
                                   (s['gap_key'] is not None) == (where == 'inside')])
                                 for where in ('inside', 'outside')} for r in REGIONS}
    return result


def arm_statistics(arms):
    rows = [row for arm in arms for row in arm['rows']]
    gaps = [gap for arm in arms for gap in arm['gaps']]
    values = dict(n=len(arms), saved_steps=len(rows), diagnostic_states=len(arms), gaps=len(gaps),
                  empty_saved_states=sum(g['original']['empty_saved_states'] for g in gaps),
                  left_censored_gaps=sum(g['original']['left_censored'] for g in gaps),
                  right_censored_gaps=sum(g['original']['right_censored'] for g in gaps),
                  same_tick_replacements=sum(g['original']['same_tick_replacement'] for g in gaps))
    values.update(tabulate([s for row in rows for s in row['slots']], [t for row in rows for t in row['targets']]))
    return values


def validate_index(index):
    equal(len(index), 100, 'complete 100 index')
    equal([(e['encoding'], e['seed']) for e in index],
          [(encoding, seed) for encoding in ENCODINGS for seed in range(120000, 120020)], 'index keys/order')
    for item in index:
        check(type(item['trigger']) is bool, 'index trigger')
        if item['trigger']:
            check(type(item['t0']) is int and 0 <= item['t0'] < 32, 'index t0')
            equal(item['remaining'], 32-item['t0'], 'index remaining')
            check(bool(item['branch']) and item['applicability'] == 'observed', 'triggered index scope')
        else:
            equal((item['t0'], item['remaining'], item['branch'], item['short_window'], item['applicability']),
                  (None, 0, None, False, 'not_applicable'), 'untriggered index')


def independent_summary(records, index):
    validate_index(index)
    lookup = {(e['encoding'], e['seed']): e for e in index}
    seen = set()
    for pair in records:
        key = pair['encoding'], pair['selection']['seed']
        check(key not in seen and key in lookup and lookup[key]['trigger'], 'record/index membership')
        seen.add(key)
        entry = lookup[key]
        equal((pair['selection']['t0'], pair['selection']['remaining_steps']),
              (entry['t0'], entry['remaining']), 'record/index selection')
        equal(pair['selection']['category'], 'short_window' if entry['short_window'] else 'remaining_conditional',
              'record/index category')
        equal(set(pair['arms']), set(ARMS), 'summary arm coverage')
    cells = []
    for encoding in ENCODINGS:
        for category in ('short_window', 'remaining_conditional'):
            for arm in ARMS:
                selected = [p['arms'][arm] for p in records if p['encoding'] == encoding and p['selection']['category'] == category]
                cells.append(dict(encoding=encoding, category=category, arm=arm, policy_denominator=20,
                                  triggered_encoding_count=sum(i['trigger'] for i in index if i['encoding'] == encoding),
                                  **arm_statistics(selected)))
    def difference(left, right):
        check(type(left) == type(right), 'numeric paired schema')
        if isinstance(left, dict):
            equal(set(left), set(right), 'numeric paired keys')
            return {k: difference(left[k], right[k]) for k in left}
        check(type(left) is int, 'numeric paired field')
        return left-right
    return dict(index=deepcopy(index), index_cases=100, triggered=sum(i['trigger'] for i in index),
                no_trigger=sum(not i['trigger'] for i in index), cells=cells,
                overall={arm: arm_statistics([p['arms'][arm] for p in records]) for arm in ARMS},
                paired=[dict(encoding=p['encoding'], seed=p['selection']['seed'],
                         delta=difference(arm_statistics([p['arms']['ablation']]), arm_statistics([p['arms']['control']]))) for p in records])


def clean_launch():
    status = subprocess.run(['git', 'status', '--porcelain'], check=True, capture_output=True, text=True)
    check(not status.stdout.strip(), 'formal verifier requires a clean committed checkout')
    return subprocess.run(['git', 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()


def producer_evidence(metadata, current, output_hashes, names, engineering, planned):
    """Accept the explicit historical 953-file engineering epoch without rewriting it."""
    equal(metadata['status'], 'complete', 'producer completion')
    equal(metadata['route'], 'producer', 'producer route')
    equal(metadata['phase'], 'engineering' if engineering else 'formal', 'producer phase')
    check(metadata['outputs_exclusive'] is True, 'producer exclusive output')
    for field in ('new_simulation_steps', 'new_environment_sources', 'new_independent_initial_worlds'):
        equal(metadata[field], 0, 'producer physical boundary')
    check(not metadata['input_inventory_errors'] and not metadata['input_read_errors_before'] and
          not metadata['input_read_errors_after'], 'producer input read errors')
    expected = dict(current)
    if metadata['includes_verifier'] is False:
        check(engineering and metadata['source_epoch'] == 'producer-only engineering', 'historical source epoch')
        expected.pop(inputs.NEW[-1])
    else:
        check(metadata['includes_verifier'] is True, 'producer verifier binding flag')
        equal(metadata['source_epoch'], 'producer and verifier', 'producer source epoch')
    equal(metadata['input_paths'], sorted(expected), 'producer input paths')
    equal(metadata['input_sha256'], expected, 'producer common source bindings')
    equal(metadata['input_sha256_after'], expected, 'producer closing source bindings')
    equal(set(metadata['output_sha256']), set(names), 'producer output inventory')
    equal(metadata['output_sha256'], output_hashes, 'producer output hashes')
    for key, value in planned.items():
        equal(metadata[key], value, 'producer ' + key)
    check(0 < metadata['time_limit_seconds'] <= TIME_LIMIT and
          0 < metadata['storage_limit_bytes'] <= BYTE_LIMIT, 'producer declared budgets')
    check(0 <= metadata['elapsed_seconds'] <= metadata['time_limit_seconds'], 'producer elapsed budget')


def run(source_dir=FORMAL, output_dir=None, *, engineering=False, seconds=TIME_LIMIT, byte_limit=BYTE_LIMIT):
    """Verify in an exclusive directory; persist failures including unreadable producer JSON.

    Default output: <source_dir>/verifier/independent-verification.json and the
    independently reconstructed records, index, summary and pair files. Producer
    input capture is a fixed file inventory, so these new outputs cannot enter it.
    """
    started = time.monotonic()
    source = Path(source_dir).resolve()
    output = (source/'verifier') if output_dir is None else Path(output_dir).resolve()
    formal = FORMAL.resolve()
    check(output != source and output not in source.parents, 'verifier output overlaps producer directory')
    if engineering:
        check(not (source == formal or formal in source.parents or output == formal or formal in output.parents),
              'engineering cannot use formal path')
    output.mkdir(parents=True, exist_ok=False)
    proof = dict(status='running', phase='engineering' if engineering else 'formal', route='independent_verifier',
                 verifier_mode='fresh independent author, phase and destination indexes',
                 reused_041_mode='immutable common input; historical parent inline fallback preserved',
                 new_simulation_steps=0, new_environment_sources=0, new_independent_initial_worlds=0,
                 time_limit_seconds=seconds, storage_limit_bytes=byte_limit, outputs_exclusive=True,
                 completed_cases=0, completed_arms=0, saved_steps=0, diagnostic_states=0, target_ticks=0, source_slots=0,
                 input_paths=[], input_inventory_errors={}, input_sha256={}, input_read_errors_before={},
                 input_sha256_after={}, input_read_errors_after={}, producer_sha256={}, producer_read_errors_before={},
                 producer_sha256_after={}, producer_read_errors_after={}, output_sha256={},
                 output_sha256_after={}, output_read_errors_after={},
                 execution_complete=False, closing_complete=False)
    source_paths = []
    pairs_expected = 1 if engineering else 28
    names = ['index.json', 'records.json', 'summary.json'] + [f'pair-{i:02d}.json' for i in range(1, pairs_expected+1)]
    producer_paths = [str(source/name) for name in ['metadata.json'] + names]
    failure = None
    failure_traceback = None
    def remember_failure(error, stage=None):
        nonlocal failure, failure_traceback
        if stage is not None:
            proof.setdefault('closing_errors', {})[stage] = repr(error)
        if failure is None:
            failure, failure_traceback = error, error.__traceback__
            proof['error'] = repr(error)

    def budget():
        if time.monotonic()-started > seconds:
            raise TimeoutError('verifier time budget exceeded')
        check(sum(p.stat().st_size for p in output.iterdir() if p.is_file()) <= byte_limit,
              'verifier storage budget exceeded')
    def save(name, value):
        budget()
        data = inputs.encode(value)
        occupied = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
        check(occupied + len(data) <= byte_limit, 'verifier storage budget exceeded')
        with (output/name).open('xb') as handle:
            handle.write(data)
        proof['output_sha256'][name] = inputs.digest(output/name)
    try:
        # Capture both inventories before parsing any producer JSON, so malformed
        # or missing metadata cannot suppress the source/failure evidence.
        source_paths = inputs.input_paths(proof['input_inventory_errors'])
        proof['input_paths'] = source_paths
        proof['input_sha256'], proof['input_read_errors_before'] = inputs.capture(source_paths)
        proof['producer_sha256'], proof['producer_read_errors_before'] = inputs.capture(producer_paths)
        check(0 <= seconds <= TIME_LIMIT and 0 <= byte_limit <= BYTE_LIMIT, 'verifier budget limits')
        check(not proof['input_inventory_errors'] and not proof['input_read_errors_before'], 'verifier input inventory reads')
        equal(len(source_paths), SOURCE_COUNT, 'full verifier source count')
        equal(len(set(source_paths)), SOURCE_COUNT, 'unique verifier sources')
        check(set(inputs.NEW) <= set(source_paths), 'verifier/producer/helper source binding')
        current = inputs.bindings()
        equal(current, proof['input_sha256'], 'verified input capture')
        check(not proof['producer_read_errors_before'], 'producer input file reads')
        if not engineering:
            proof['git_commit'] = clean_launch()
        budget()
        census = inputs.read(inputs.CENSUS)
        index = deepcopy(census['index'])
        validate_index(index)
        reader = inputs.SourceReader()
        equal(reader.resolve(census['index_reference']), index, 'method index source')
        triggered = [i for i in index if i['trigger']]
        selected = triggered[:1] if engineering else triggered
        if engineering:
            equal([(i['encoding'], i['seed']) for i in selected], [('east', 120005)], 'first engineering case')
        else:
            equal(len(selected), 28, 'formal pair count')
        chosen_keys = {(i['encoding'], i['seed']) for i in selected}
        plans = [p for p in census['arms'] if (p['encoding'], p['seed']) in chosen_keys]
        equal(len(plans), 2*len(selected), 'planned arm coverage')
        steps = sum(p['saved_states'] for p in plans)
        planned = dict(planned_cases=len(selected), planned_arms=len(plans), completed_cases=len(selected),
                       completed_arms=len(plans), saved_steps=steps, diagnostic_states=len(plans),
                       target_ticks=2*steps, source_slots=8*steps)
        proof.update(planned_cases=len(selected), planned_arms=len(plans))
        metadata = inputs.read(source/'metadata.json')
        producer_evidence(metadata, current, {name: proof['producer_sha256'][str(source/name)] for name in names},
                          names, engineering, planned)
        equal(metadata['output_bytes_before_metadata'], sum((source/name).stat().st_size for name in names),
              'producer output bytes')
        check(sum(Path(path).stat().st_size for path in producer_paths) <= metadata['storage_limit_bytes'], 'producer storage budget')
        proof['producer_source_count'] = len(metadata['input_sha256'])
        proof['producer_source_epoch'] = metadata['source_epoch']
        # Bind and compare the entire index, including all untriggered entries.
        equal(inputs.read(source/'index.json'), index, 'producer complete index')
        expected_records = inputs.read(source/'records.json')
        equal(len(expected_records), len(selected), 'producer record count')
        records = []
        reuse = []
        for plan in plans:
            if plan['reuse_041'] is not None:
                case = reader.resolve(plan['reuse_041']['reference'])
                if not any(same_value(case, old) for old in reuse):
                    reuse.append(case)
        save('index.json', index)
        for number, entry in enumerate(selected, 1):
            budget()
            branch = inputs.read(entry['branch'])
            equal(branch['selection']['seed'], entry['seed'], 'selected branch seed')
            equal(branch['selection']['t0'], entry['t0'], 'selected branch t0')
            record = reconstruct_pair(entry['encoding'], branch, plans, census['gaps'], reuse)
            # Counters describe completed independent work even when a producer mismatch follows.
            records.append(record)
            proof['completed_cases'] = len(records)
            proof['completed_arms'] += 2
            proof['saved_steps'] += sum(a['saved_steps'] for a in record['arms'].values())
            proof['diagnostic_states'] += 2
            proof['target_ticks'] = proof['saved_steps'] * 2
            proof['source_slots'] = proof['saved_steps'] * 8
            save(f'pair-{number:02d}.json', record)
            equal(record, expected_records[number-1], f'producer records pair {number}')
            equal(record, inputs.read(source/f'pair-{number:02d}.json'), f'producer pair file {number}')
        summary = independent_summary(records, index)
        equal(summary, inputs.read(source/'summary.json'), 'producer full summary')
        for key, value in planned.items():
            equal(proof[key], value, 'independent completed ' + key)
        if not engineering:
            equal((proof['source_slots'], proof['target_ticks'], len(summary['paired'])), (6240, 1560, 28),
                  'formal scientific scope')
        save('records.json', records)
        save('summary.json', summary)
        proof['records_equal'] = proof['summary_equal'] = proof['index_equal'] = True
        budget()
        # Reaching finally (or having no ordinary Exception) is not completion.
        proof['execution_complete'] = True
    except BaseException as error:
        # KeyboardInterrupt/SystemExit must leave truthful evidence, then propagate.
        remember_failure(error)
    finally:
        inventories = (
            ('input', source_paths),
            ('producer', producer_paths),
            ('output', [str(output/name) for name in proof['output_sha256']]),
        )
        # Capture all three independently, including after a primary cancellation.
        # Preserve the first exception object and traceback; later faults are evidence.
        for stage, paths in inventories:
            try:
                hashes, errors = inputs.capture(paths)
                proof[stage + '_sha256_after'] = ({Path(p).name: sha for p, sha in hashes.items()}
                                                   if stage == 'output' else hashes)
                proof[stage + '_read_errors_after'] = errors
            except BaseException as error:
                proof[stage + '_read_errors_after'] = {'capture': repr(error)}
                remember_failure(error, stage + '_capture')
        for stage, _ in inventories:
            try:
                check(not proof[stage + '_read_errors_after'], 'closing ' + stage + ' reads')
                label = 'verifier output' if stage == 'output' else stage
                equal(proof[stage + '_sha256_after'], proof[stage + '_sha256'], label + ' before/after hashes')
            except BaseException as error:
                remember_failure(error, stage + '_binding')
        try:
            proof['output_bytes_before_proof'] = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
            proof['elapsed_seconds'] = time.monotonic() - started
            budget()
        except BaseException as error:
            remember_failure(error, 'budget')
        proof['closing_complete'] = not bool(proof.get('closing_errors'))
        if not proof['execution_complete'] and failure is None:
            remember_failure(ValueError('independent execution did not complete'))
        proof['status'] = ('complete' if proof['execution_complete'] and proof['closing_complete']
                           and failure is None else 'failed')
        # Failure evidence may exceed an exhausted storage budget. A proof cannot
        # be marked complete unless its own bytes fit the successful route budget.
        payload = inputs.encode(proof)
        if failure is None and proof['output_bytes_before_proof'] + len(payload) > byte_limit:
            remember_failure(ValueError('verifier storage budget including proof exceeded'), 'proof_budget')
            proof.update(status='failed', closing_complete=False)
            payload = inputs.encode(proof)
        try:
            with (output/'independent-verification.json').open('xb') as handle:
                handle.write(payload)
        except BaseException as error:
            # If persistence itself is unavailable, do not mask the original cause.
            remember_failure(error, 'proof_write')
    if failure is not None:
        raise failure.with_traceback(failure_traceback)
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=FORMAL)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--engineering', action='store_true', help='Only the first east/120005 pair, outside formal data')
    args = parser.parse_args()
    result = run(args.source_dir, args.output_dir, engineering=args.engineering)
    print(result['status'], result['completed_cases'], 'pairs;', result['source_slots'], 'slots; 0 physics')


if __name__ == '__main__':
    main()
