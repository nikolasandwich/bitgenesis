"""Study046: read-only local source slots, target phases and saved-gap links.

Public data contract: project_pair(encoding, branch043, arm_plans, gap_plans,
reuse041) -> {encoding, selection, arms}. Each arm contains source/diagnostic
references, chronological rows of eight slots and two targets, and original
045 gaps joined to decision keys. Keys include encoding, seed and policy arm;
slot keys append tick/source/target, target keys append tick/target.

A slot's proposal is the unchanged 041 event, or a newly projected local event
with that same field contract. not_pointing retains its actual proposal_target
but has no proposal to this slot's target. Empty/dead sources have neither.
All missing identities/values are explicit nulls. Diagnostics have no slots.
No simulation, full-world proposal classification, energy ledger, component
analysis or gap-interval reconstruction is imported or executed.
"""
from copy import deepcopy
from pathlib import Path
import subprocess
import time

from scripts import middle_refill_inputs as inputs

OUTPUT = Path('data/v4-study-046')
ENCODINGS = ('east', 'west', 'south', 'north', 'homogeneous')
ARMS = ('control', 'ablation')
CATEGORIES = ('short_window', 'remaining_conditional')
REGIONS = ('upper', 'middle', 'lower', 'other')
STATES = ('empty_source', 'dissolved', 'not_pointing', 'energy', 'occupied',
          'raw_material', 'collision', 'formed')
EDGES = ((100, 101, 0, 'other'), (102, 101, 1, 'middle'),
         (85, 101, 2, 'upper'), (117, 101, 3, 'lower'),
         (101, 102, 0, 'middle'), (103, 102, 1, 'other'),
         (86, 102, 2, 'upper'), (118, 102, 3, 'lower'))
TIME_LIMIT = 600
STORAGE_LIMIT = 134217728
require = inputs.require


def ticket_target(site, direction):
    require(type(direction) is int and direction in range(4), 'saved direction ticket')
    x, y = site % 16, site // 16
    return (16*y + (x+1) % 16, 16*y + (x-1) % 16,
            16*((y+1) % 16) + x, 16*((y-1) % 16) + x)[direction]


def ancestry(identity, people, selection):
    chain, cursor = [], identity
    while cursor is not None:
        require(type(cursor) is int and 0 <= cursor < len(people) and cursor not in chain,
                'complete acyclic identity ancestry')
        person = people[cursor]
        require(person['id'] == cursor, 'identity table index')
        chain.append(cursor)
        cursor = person['parent']
    chosen = dict(zip(selection['offspring_ids'], selection['offspring_sites']))
    selected = [i for i in chain if i in chosen]
    ancestor = selected[0] if selected else None
    lineage = {117: 'left', 118: 'right'}.get(chosen.get(ancestor), 'other')
    return dict(chain=chain, selected_ancestors=selected, ancestor=ancestor, lineage=lineage)


def stage(ids, units, raw, site):
    require((ids[site] is None) == (units[site] is None), 'phase identity occupancy')
    require(type(raw[site]) is int and raw[site] >= 0, 'integer phase raw')
    return dict(identity=ids[site], material=None if units[site] is None else units[site]['material'], raw=raw[site])


def saved_context(before, saved):
    """Read phase identity/raw; classify no proposal gates here (including reuse)."""
    physical = saved['physical']
    previous_units = before['units'] if 'units' in before else before['physical']['units']
    previous_raw = before['raw'] if 'raw' in before else before['physical']['raw']
    ids, phases = before['site_ids'], physical['interaction_units']
    require(saved['tick'] == physical['tick'], 'saved physical tick')
    require(all(len(v) == 256 for v in (ids, previous_units, previous_raw, phases,
                physical['units'], physical['raw'], physical['directions'], saved['site_ids'])), 'phase world coverage')
    require([u is not None for u in phases] == [i is not None for i in ids], 'pre-state actor coverage')
    dead = [s for s, u in enumerate(phases) if u is not None and u['energy'] == 0]
    require(physical['material']['dissolved'] == dead, 'saved dissolution sites')
    require(sorted(saved['deaths']) == sorted(ids[s] for s in dead), 'saved death identities')
    pre_ids, pre_units, pre_raw = ids[:], deepcopy(phases), previous_raw[:]
    for site in dead:
        pre_ids[site] = pre_units[site] = None
        pre_raw[site] += 1
    proposals = {}
    for pos, proposal in enumerate(physical['material']['proposals']):
        source = proposal['source']
        require(type(source) is int and source in range(256), 'saved source bounds')
        require(source not in proposals, 'unique saved source proposal')
        require(phases[source] is not None and phases[source]['energy'] > 0, 'nonacting source proposal')
        direction = physical['directions'][source]
        require(proposal['target'] == ticket_target(source, direction)
                and proposal['direction'] == direction, 'saved proposal direction and target')
        proposals[source] = (pos, proposal)
    # Presence of proposals is structural; classify only the eight target slots.
    require(set(proposals) == {s for s, u in enumerate(phases) if u is not None and u['energy'] > 0},
            'saved surviving source proposal coverage')
    return dict(previous_units=previous_units, previous_raw=previous_raw, ids=ids, phases=phases,
                dead=dead, pre_ids=pre_ids, pre_units=pre_units, pre_raw=pre_raw, proposals=proposals)


def project_proposals(saved, context, people, selection):
    """Compute new gates only for real proposals entering one of the two targets."""
    events, gates, counts = {}, {}, {101: 0, 102: 0}
    for source, (_, proposal) in context['proposals'].items():
        target = proposal['target']
        if target not in counts:
            continue
        energy = context['phases'][source]['energy']
        require(type(energy) is int and energy > 0, 'positive interaction energy')
        gates[source] = (energy >= 16, context['pre_ids'][target] is None, context['pre_raw'][target] >= 1)
        if all(gates[source]):
            counts[target] += 1
    for source, (energy_ok, empty, raw_ok) in gates.items():
        proposal = context['proposals'][source][1]
        target, identity = proposal['target'], context['ids'][source]
        count = counts[target]
        reason = ('energy' if not energy_ok else 'occupied' if not empty else 'raw_material' if not raw_ok
                  else 'collision' if count > 1 else 'formed')
        require(proposal['reason'] == reason, 'saved proposal reason')
        a = ancestry(identity, people, selection)
        events[source] = dict(tick=saved['tick'], source=source, target=target, direction=proposal['direction'],
            identity=identity, program=deepcopy(context['phases'][source]['program']),
            energy=context['phases'][source]['energy'], target_region='middle',
            target_raw=context['pre_raw'][target], target_occupied=context['pre_ids'][target] is not None,
            target_dissolved=target in context['dead'], energy_ok=energy_ok, target_empty=empty,
            raw_ok=raw_ok, candidate=all(gates[source]), candidate_count=count, reason=reason,
            child_id=saved['site_ids'][target] if reason == 'formed' else None,
            lineage=a['lineage'], ancestor=a['ancestor'], chain=a['chain'])
    return events


def reused_events(reader, plan, row_plan, original, saved, context):
    reference = row_plan['reuse_041']
    require(reference is not None and reference['path'] == plan['reuse_041']['reference']['path'], '041 row reference file')
    position = saved['tick'] - plan['t0'] - 1
    prefix = plan['reuse_041']['reference']['json_pointer'] + '/rows/' + str(position)
    require(reference['json_pointer'] == prefix, '041 exact row pointer')
    row = reader.resolve(reference)
    require(row == original['rows'][position] and row['tick'] == saved['tick'], '041 exact saved row')
    events = row['events']
    proposals = saved['physical']['material']['proposals']
    require(len(events) == len(proposals), '041 all proposal count')
    require(sorted(d['identity'] for d in row['deaths']) == sorted(saved['deaths']), '041 saved death coverage')
    answer, references = {}, {}
    for pos, (event, proposal) in enumerate(zip(events, proposals)):
        source = event['source']
        require(all(event[k] == proposal[k] for k in ('source', 'target', 'direction', 'reason')),
                '041 exact saved proposal values')
        require(event['identity'] == context['ids'][source] and event['tick'] == saved['tick'], '041 actor identity')
        if event['target'] in (101, 102):
            answer[source] = deepcopy(event)
            references[source] = reader.child_ref(reference, '/events/' + str(pos))
    return answer, references


def birth_for(target, saved, context, events, people):
    successes = [event for event in events.values() if event['target'] == target and event['reason'] == 'formed']
    births = [b for b in saved['births'] if b['site'] == target]
    require(len(successes) <= 1 and len(births) == len(successes), 'unique target birth coverage')
    if not successes:
        require(saved['site_ids'][target] == context['pre_ids'][target], 'target identity without birth')
        return None
    event, birth = successes[0], births[0]
    identity = saved['site_ids'][target]
    require(type(identity) is int and 0 <= identity < len(people), 'birth identity bounds')
    require(event['child_id'] == birth['id'] == identity and birth['parent'] == event['identity']
            and birth['site'] == target and birth['birth_tick'] == saved['tick'], 'saved birth identity parent site')
    person = people[identity]
    require(all(person[k] == birth[k] for k in ('id', 'parent', 'site', 'birth_tick')), 'birth identity provenance')
    require(context['pre_ids'][target] is None and identity not in context['ids'], 'birth after dissolution is new identity')
    require(saved['physical']['units'][target] is not None, 'birth saved unit')
    require(saved['physical']['units'][target]['material'] == birth['material'], 'birth material')
    return deepcopy(birth)


def project_arm(encoding, branch, plan, gap_plans, reuse041, reader=None):
    reader = inputs.SourceReader() if reader is None else reader
    selection = branch['selection']
    seed, t0, arm_name = selection['seed'], selection['t0'], plan['arm']
    require(encoding in ENCODINGS and arm_name in ARMS, 'encoding and policy arm')
    require(plan['encoding'] == encoding and plan['seed'] == seed and plan['key'] == [encoding, seed, arm_name],
            'arm plan identity')
    arm = branch[arm_name]
    require(reader.resolve(plan['source']) == arm, 'exact source arm')
    require(plan['source']['json_pointer'] == '/' + arm_name, 'exact source arm pointer')
    require(plan['t0'] == t0 and plan['saved_states'] == len(arm['rows']) == selection['remaining_steps'], 'arm chronology')
    require([r['tick'] for r in arm['rows']] == list(range(t0+1, 33)), 'complete future chronology')
    require(len(plan['rows']) == len(arm['rows']) and plan['target_ticks'] == 2*len(arm['rows'])
            and plan['source_slots'] == 8*len(arm['rows']), 'planned row and slot coverage')
    require(reader.resolve(plan['diagnostic']) == arm['initial'] and arm['initial']['tick'] == t0, 'diagnostic origin')
    require(reader.resolve(plan['turnover_diagnostic'])['tick'] == t0, 'turnover diagnostic origin')
    old = None
    reuse = plan['reuse_041']
    if plan['proposal_plan'] == 'reuse_041':
        require(arm_name == 'control' and encoding in ('east', 'west') and reuse is not None, '041 reuse arm boundary')
        old = reader.resolve(reuse['reference'])
        require(old['encoding'] == encoding and old['selection'] == selection, '041 case selection')
        pointer = reuse['reference']['json_pointer']
        require(pointer.startswith('/') and pointer[1:].isdigit() and pointer.count('/') == 1, '041 case pointer')
        require(int(pointer[1:]) < len(reuse041) and reuse041[int(pointer[1:])] == old, '041 supplied case exact object')
        require(reuse['old_branch']['json_pointer'] == '/ablation'
                and reader.resolve(reuse['old_branch']) == arm, '041 entire old branch equality')
        old_document = reader.documents[reuse['old_branch']['path']]
        require(old_document['selection'] == selection, '039 exact selection')
        require(reuse['complete_old_arm_equal'] is True and reuse['proposals_reclassified'] is False, '041 reuse declaration')
        require([r['tick'] for r in old['rows']] == [r['tick'] for r in arm['rows']], '041 full row chronology')
    else:
        require(plan['proposal_plan'] == 'needed_projection' and reuse is None
                and all(r['reuse_041'] is None for r in plan['rows']), 'explicit new projection boundary')
    people = arm['final']['individuals']
    rows, before = [], arm['initial']
    for pos, (saved, row_plan) in enumerate(zip(arm['rows'], plan['rows'])):
        tick = saved['tick']
        require(row_plan['tick'] == tick and reader.resolve(row_plan['source']) == saved
                and reader.resolve(row_plan['before']) == before, 'exact source and previous row references')
        require(row_plan['source']['json_pointer'] == f'/{arm_name}/rows/{pos}', 'source row pointer')
        turnover = reader.resolve(row_plan['turnover'])
        require(turnover['tick'] == tick and [v['site'] for v in turnover['middle']] == [101, 102]
                and [v['identity'] for v in turnover['middle']] == [saved['site_ids'][s] for s in (101, 102)],
                '045 exact target row')
        context = saved_context(before, saved)
        if old is not None:
            events, event_refs = reused_events(reader, plan, row_plan, old, saved, context)
        else:
            events = project_proposals(saved, context, people, selection)
            event_refs = {source: reader.child_ref(row_plan['source'], '/physical/material/proposals/' + str(context['proposals'][source][0]))
                          for source in events}
        slots = []
        for source, target, required_direction, source_region in EDGES:
            identity = context['ids'][source]
            phase = context['phases'][source]
            direction = saved['physical']['directions'][source]
            destination = ticket_target(source, direction)
            a = dict(chain=[], selected_ancestors=[]) if identity is None else ancestry(identity, people, selection)
            if identity is not None:
                require(people[identity]['site'] == source and people[identity]['birth_tick'] < tick, 'pre-state actor birth chronology')
                require(context['previous_units'][source]['program'] == phase['program'], 'actor program continuity')
                require(type(phase['energy']) is int and phase['energy'] >= 0, 'integer interaction energy')
            state = ('empty_source' if identity is None else 'dissolved' if phase['energy'] == 0
                     else 'not_pointing' if destination != target else events[source]['reason'])
            require(state in STATES, 'fixed slot state')
            event = events.get(source) if state not in STATES[:3] else None
            slots.append(dict(key=[encoding, seed, arm_name, tick, source, target], tick=tick,
                source=source, target=target, required_direction=required_direction, source_region=source_region,
                direction=direction, ticket_target=destination,
                proposal_target=destination if identity is not None and phase['energy'] > 0 else None,
                identity=identity, material=None if identity is None else context['previous_units'][source]['material'],
                program=None if identity is None else deepcopy(context['previous_units'][source]['program']),
                ancestry_chain=a['chain'], selected_ancestors=a['selected_ancestors'],
                interaction_energy=None if phase is None else phase['energy'], end_identity=saved['site_ids'][source],
                state=state, proposal=deepcopy(event), proposal_reference=deepcopy(event_refs.get(source)) if event else None,
                source_mode='reuse_041' if old is not None and event is not None else 'source_projection', gap_key=None))
        require({s['source'] for s in slots if s['proposal'] is not None} == set(events), 'complete local incoming proposals')
        targets = []
        for target in (101, 102):
            incoming = [s for s in slots if s['target'] == target]
            targets.append(dict(key=[encoding, seed, arm_name, tick, target], tick=tick, target=target,
                before=stage(context['ids'], context['previous_units'], context['previous_raw'], target),
                preformation=stage(context['pre_ids'], context['pre_units'], context['pre_raw'], target),
                after=stage(saved['site_ids'], saved['physical']['units'], saved['physical']['raw'], target),
                slot_keys=[s['key'] for s in incoming], proposal_keys=[s['key'] for s in incoming if s['proposal'] is not None],
                candidate_keys=[s['key'] for s in incoming if s['proposal'] is not None and s['proposal']['candidate']],
                birth=birth_for(target, saved, context, events, people),
                turnover_flags={k: turnover[k] for k in ('B101', 'B102', 'G', 'actual_double_new')},
                turnover=deepcopy(row_plan['turnover']), gap_key=None))
        rows.append(dict(tick=tick, source=deepcopy(row_plan['source']), before=deepcopy(row_plan['before']),
                         turnover=deepcopy(row_plan['turnover']), reuse_041=deepcopy(row_plan['reuse_041']),
                         slots=slots, targets=targets))
        before = saved
    gaps = link_gaps(encoding, seed, arm_name, t0, rows, plan, gap_plans, reader)
    return dict(arm=arm_name, t0=t0, saved_steps=len(rows), source=deepcopy(plan['source']),
        diagnostic=dict(source=deepcopy(plan['diagnostic']), turnover=deepcopy(plan['turnover_diagnostic'])),
        proposal_plan=plan['proposal_plan'], reuse_041=deepcopy(reuse), rows=rows, gaps=gaps)


def link_gaps(encoding, seed, arm_name, t0, rows, plan, gap_plans, reader):
    chosen = [g for g in gap_plans if (g['encoding'], g['seed'], g['arm']) == (encoding, seed, arm_name)]
    require([g['key'] for g in chosen] == plan['gap_keys'], 'exact gap plan list')
    by_target = {(t['target'], t['tick']): t for r in rows for t in r['targets']}
    by_slot = {tuple(s['key']): s for r in rows for s in r['slots']}
    result = []
    for g in chosen:
        original = reader.resolve(g['reference'])
        require(original == g['original'] and g['intervals_recalculated'] is False, 'unchanged original gap')
        require(g['key'][:3] == [encoding, seed, arm_name] and len(g['key']) == 4, 'gap policy identity')
        successor = original['successor']
        ticks = original['empty_ticks'] + ([] if successor is None else [original['end_boundary']])
        require(g['decision_ticks'] == ticks and ticks == list(range(t0+1 if original['predecessor'] is None
                else original['start_boundary'], original['end_boundary']+1)), 'gap decision endpoints')
        require(g['decision_target_ticks'] == len(ticks) and g['decision_source_slots'] == 4*len(ticks), 'gap decision budget')
        targets, slots, sequence = [], [], []
        for tick in ticks:
            require((original['site'], tick) in by_target, 'gap decision within future window')
            target = by_target[original['site'], tick]
            require(target['gap_key'] is None, 'overlapping gap target tick')
            target['gap_key'] = deepcopy(g['key'])
            incoming = [by_slot[tuple(key)] for key in target['slot_keys']]
            for s in incoming:
                s['gap_key'] = deepcopy(g['key'])
            targets.append(target)
            slots.extend(incoming)
            if tick in original['empty_ticks']:
                require(target['after']['identity'] is None, 'original empty gap state')
            if successor is not None and tick == original['end_boundary']:
                require(target['birth'] is not None and target['birth']['id'] == successor, 'gap successful birth endpoint')
            if original['predecessor'] is not None and tick == original['start_boundary']:
                require(target['before']['identity'] == original['predecessor'] and target['preformation']['identity'] is None,
                        'gap predecessor dissolution endpoint')
            sequence.append(dict(tick=tick, target_key=deepcopy(target['key']), slot_keys=deepcopy(target['slot_keys']),
                states=[s['state'] for s in incoming], real_proposals=len(target['proposal_keys']),
                candidate_count=len(target['candidate_keys']), birth_id=None if target['birth'] is None else target['birth']['id']))
        result.append(dict(key=deepcopy(g['key']), reference=deepcopy(g['reference']), original=original,
            decision_ticks=deepcopy(ticks), target_keys=[t['key'] for t in targets], slot_keys=[s['key'] for s in slots],
            sequence=sequence, counts=observation_counts(slots, targets), intervals_recalculated=False))
    require(sum(t['gap_key'] is not None for t in by_target.values()) == plan['gap_target_ticks']
            and sum(s['gap_key'] is not None for s in by_slot.values()) == plan['gap_source_slots'], 'complete gap coverage budget')
    return result


def project_pair(encoding, branch043, arm_plans, gap_plans, reuse041):
    require(branch043['control']['initial'] == branch043['ablation']['initial'], 'paired diagnostic equality')
    seed = branch043['selection']['seed']
    chosen = [a for a in arm_plans if (a['encoding'], a['seed']) == (encoding, seed)]
    require(len(chosen) == 2 and {p['arm'] for p in chosen} == set(ARMS), 'exact pair arm plans')
    reader = inputs.SourceReader()
    return dict(encoding=encoding, selection=deepcopy(branch043['selection']), arms={
        a: project_arm(encoding, branch043, next(p for p in chosen if p['arm'] == a), gap_plans, reuse041, reader)
        for a in ARMS})


def slot_counts(slots):
    proposals = [s['proposal'] for s in slots if s['proposal'] is not None]
    return dict(source_slots=len(slots), real_proposals=len(proposals),
        eligible_candidates=sum(p['candidate'] for p in proposals), births=sum(p['reason'] == 'formed' for p in proposals),
        states={state: sum(s['state'] == state for s in slots) for state in STATES})


def observation_counts(slots, targets):
    return dict(target_ticks=len(targets), **slot_counts(slots),
        gap_target_ticks=sum(t['gap_key'] is not None for t in targets),
        gap_source_slots=sum(s['gap_key'] is not None for s in slots),
        cross_counts={region: {scope: slot_counts([s for s in slots if s['source_region'] == region
            and (s['gap_key'] is not None) == (scope == 'inside')]) for scope in ('inside', 'outside')} for region in REGIONS})


def group(arms):
    rows = [r for arm in arms for r in arm['rows']]
    gaps = [g for arm in arms for g in arm['gaps']]
    return dict(n=len(arms), saved_steps=len(rows), diagnostic_states=len(arms), gaps=len(gaps),
        empty_saved_states=sum(g['original']['empty_saved_states'] for g in gaps),
        left_censored_gaps=sum(g['original']['left_censored'] for g in gaps),
        right_censored_gaps=sum(g['original']['right_censored'] for g in gaps),
        same_tick_replacements=sum(g['original']['same_tick_replacement'] for g in gaps),
        **observation_counts([s for r in rows for s in r['slots']], [t for r in rows for t in r['targets']]))


def difference(new, old):
    if isinstance(new, dict):
        require(new.keys() == old.keys(), 'paired count schema')
        return {key: difference(new[key], old[key]) for key in new}
    return new - old


def summarize(records, index):
    cells = []
    for encoding in ENCODINGS:
        for category in CATEGORIES:
            for arm in ARMS:
                chosen = [r['arms'][arm] for r in records if r['encoding'] == encoding and r['selection']['category'] == category]
                cells.append(dict(encoding=encoding, category=category, arm=arm, policy_denominator=20,
                    triggered_encoding_count=sum(i['trigger'] for i in index if i['encoding'] == encoding), **group(chosen)))
    return dict(index=deepcopy(index), index_cases=len(index), triggered=sum(i['trigger'] for i in index),
        no_trigger=sum(not i['trigger'] for i in index), cells=cells,
        overall={a: group([r['arms'][a] for r in records]) for a in ARMS},
        paired=[dict(encoding=r['encoding'], seed=r['selection']['seed'],
                     delta=difference(group([r['arms']['ablation']]), group([r['arms']['control']]))) for r in records])


def run(*, output=None, engineering=False, include_verifier=True, time_limit=TIME_LIMIT, storage_limit=STORAGE_LIMIT):
    """Default formal entry; engineering is limited to the first E120005 pair.

    Early producer-only engineering may explicitly omit the future verifier.
    Both modes otherwise bind the complete producer/verifier source epoch.
    Formal mode requires the verifier, all bindings and a clean working tree.
    """
    output = OUTPUT if output is None else Path(output)
    require(engineering or include_verifier, 'formal execution requires verifier input')
    require(time_limit <= TIME_LIMIT and storage_limit <= STORAGE_LIMIT, 'cannot extend fixed execution budgets')
    require(not engineering or output.resolve() != OUTPUT.resolve(), 'engineering cannot use formal output directory')
    if not engineering:
        require(not subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip(), 'clean launch')
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    records, paths = [], []
    meta = dict(status='running', phase='engineering' if engineering else 'formal', route='producer',
        planned_cases=1 if engineering else 28, planned_arms=2 if engineering else 56,
        completed_cases=0, completed_arms=0, saved_steps=0, diagnostic_states=0, target_ticks=0, source_slots=0,
        new_simulation_steps=0, new_environment_sources=0, new_independent_initial_worlds=0,
        time_limit_seconds=time_limit, storage_limit_bytes=storage_limit, outputs_exclusive=True,
        includes_verifier=include_verifier, source_epoch='producer-only engineering' if not include_verifier else 'producer and verifier',
        input_paths=[], input_inventory_errors={}, input_sha256={}, input_read_errors_before={})

    def used():
        return sum(p.stat().st_size for p in output.rglob('*') if p.is_file())

    def budget(extra=0):
        require(time.monotonic()-started < time_limit and used()+extra < storage_limit, 'bounded execution')

    def write(name, value):
        payload = inputs.encode(value)
        budget(len(payload))
        with (output/name).open('xb') as handle:
            handle.write(payload)
        budget()

    def hashes():
        return {str(p.relative_to(output)): inputs.digest(p) for p in sorted(output.rglob('*.json'))
                if p.name != 'metadata.json'}

    try:
        meta['git_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        paths = inputs.input_paths(meta['input_inventory_errors'], include_verifier=include_verifier)
        meta['input_paths'] = paths
        meta['input_sha256'], meta['input_read_errors_before'] = inputs.capture(paths)
        require(inputs.bindings(include_verifier=include_verifier) == meta['input_sha256']
                and not meta['input_inventory_errors'] and not meta['input_read_errors_before'], 'validated initial inputs')
        budget()
        census = inputs.read(inputs.CENSUS)
        index = deepcopy(census['index'])
        require(len(index) == 100 and sum(i['trigger'] for i in index) == 28
                and sum(i['short_window'] for i in index) == 10, 'full frozen index')
        require(all(sorted(i['seed'] for i in index if i['encoding'] == e) == list(range(120000, 120020))
                    for e in ENCODINGS), 'five complete encoding cohorts')
        require(all(i['branch'] is None and i['applicability'] == 'not_applicable'
                    for i in index if not i['trigger']), 'non-applicable index cases')
        write('index.json', index)
        chosen = [i for i in index if i['trigger']]
        if engineering:
            require((chosen[0]['encoding'], chosen[0]['seed']) == ('east', 120005), 'first engineering pair')
            chosen = chosen[:1]
        reuse041 = inputs.read('data/v4-study-041/records.json')
        for item in chosen:
            budget()
            branch = inputs.read(item['branch'])
            require(branch['selection']['seed'] == item['seed'] and branch['selection']['source'] == item['source'], 'indexed branch identity')
            record = project_pair(item['encoding'], branch, census['arms'], census['gaps'], reuse041)
            records.append(record)
            meta.update(completed_cases=len(records), completed_arms=2*len(records),
                        saved_steps=sum(r['arms'][a]['saved_steps'] for r in records for a in ARMS),
                        diagnostic_states=2*len(records))
            meta.update(target_ticks=2*meta['saved_steps'], source_slots=8*meta['saved_steps'])
            # Append-only checkpoints preserve successful pairs if later input fails.
            write(f'pair-{len(records):02d}.json', record)
        expected = (1, 2, 26, 2, 52, 208) if engineering else (28, 56, 780, 56, 1560, 6240)
        require(tuple(meta[k] for k in ('completed_cases', 'completed_arms', 'saved_steps', 'diagnostic_states',
                                      'target_ticks', 'source_slots')) == expected, 'complete planned denominator')
        summary = summarize(records, index)
        if not engineering:
            require(sum(summary['overall'][a]['gaps'] for a in ARMS) == 226
                    and sum(summary['overall'][a]['gap_target_ticks'] for a in ARMS) == 601
                    and sum(summary['overall'][a]['gap_source_slots'] for a in ARMS) == 2404, 'complete gap subset')
        write('records.json', records)
        write('summary.json', summary)
        require(inputs.bindings(include_verifier=include_verifier) == meta['input_sha256'], 'unchanged validated inputs')
        budget()
        meta['status'] = 'complete'
    except BaseException as error:
        meta.update(status='failed', error=repr(error))
        raise
    finally:
        try:
            meta['input_sha256_after'], meta['input_read_errors_after'] = inputs.capture(paths)
            meta['output_sha256'] = hashes()
            meta['elapsed_seconds'] = time.monotonic()-started
            meta['output_bytes_before_metadata'] = used()
            if meta['status'] == 'complete':
                require(meta['input_sha256_after'] == meta['input_sha256'] and not meta['input_read_errors_after'], 'final input binding')
                budget(len(inputs.encode(meta)))
        except BaseException as error:
            meta.update(status='failed', finalization_error=repr(error), elapsed_seconds=time.monotonic()-started)
            raise
        finally:
            # Failure diagnostics are retained even when a budget has expired.
            with (output/'metadata.json').open('xb') as handle:
                handle.write(inputs.encode(meta))
    return meta


def main():
    run()


if __name__ == '__main__':
    main()
