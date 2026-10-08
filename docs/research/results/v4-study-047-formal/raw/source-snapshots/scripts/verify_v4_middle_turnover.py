"""Study045 independent verifier by fresh subagent turnover_verifier.

Uses immutable saved observations and the exact verified 042 input ledger. No
producer scientific algorithms, step functions, or physical replay are imported.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from time import monotonic

from scripts.middle_turnover_inputs import bindings, input_paths, capture, read, save, digest

OUTPUT = Path('data/v4-study-045')
MIDDLE = (101, 102)
ARMS = ('control', 'ablation')
ENCODINGS = ('east', 'west', 'south', 'north', 'homogeneous')
CATEGORIES = ('short_window', 'remaining_conditional')
FLAGS = ('occupied', 'material_match', 'genetic_match', 'whole_component',
         'root_descendant', 'all_new', 'post_birth', 'selected_ancestry', 'copy', 'new_copy')
AUTHOR = 'fresh independent subagent turnover_verifier'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(actual, expected, message):
    require(json.dumps(actual, sort_keys=True, allow_nan=False) ==
            json.dumps(expected, sort_keys=True, allow_nan=False), message)


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def check_budget(start, output, extra_bytes=0):
    require(monotonic() - start < 600, 'verification time budget')
    size = sum(p.stat().st_size for p in Path(output).rglob('*') if p.is_file())
    require(size + extra_bytes < 134217728, 'verification storage budget')


def ancestry(identity, people, selected):
    chain = []
    while identity is not None:
        require(type(identity) is int and 0 <= identity < len(people), 'ancestry identity')
        require(identity not in chain, 'ancestry cycle')
        chain.append(identity)
        parent = people[identity]['parent']
        require(parent is None or type(parent) is int and 0 <= parent < identity,
                'ancestry parent ordering')
        identity = parent
    return chain, [i for i in chain if i in selected]


def region(site):
    for name, sites in (('upper', (85, 86)), ('middle', MIDDLE), ('lower', (117, 118))):
        if site in sites:
            return name
    return 'other'


def material_components(units, ids):
    """Independent union-find over geometric equal-material neighbors."""
    parent = {site: site for site, unit in enumerate(units) if unit is not None}
    require(all((units[s] is None) == (ids[s] is None) for s in range(len(units))),
            'physical units and identities agree')
    def find(site):
        while parent[site] != site:
            parent[site] = parent[parent[site]]
            site = parent[site]
        return site
    for site in parent:
        for target in ((site // 16) * 16 + (site % 16 + 1) % 16,
                       ((site // 16 + 1) % 16) * 16 + site % 16):
            if target in parent and units[target]['material'] == units[site]['material']:
                parent[find(target)] = find(site)
    groups = {}
    for site in parent:
        groups.setdefault(find(site), []).append(site)
    lookup = {}
    for sites in groups.values():
        component = dict(identities=sorted(ids[s] for s in sites), sites=sorted(sites))
        for site in sites:
            lookup[site] = component
    return lookup


def verify_slots(units, ids, tick, people, selection, template, prior):
    """Recreate all 044 predicates from saved state, not its derived booleans."""
    components = material_components(units, ids)
    result = []
    for sites in ((85, 86), MIDDLE, (117, 118)):
        members = [ids[s] for s in sites]
        present = all(i is not None for i in members)
        chains = [([], []) if i is None else ancestry(i, people, selection['offspring_ids'])
                  for i in members]
        roots = [chain[-1] if chain else None for chain, _ in chains]
        selected = [hits[0] if hits else None for _, hits in chains]
        material = present and all(units[s]['material'] == t['material']
                                   for s, t in zip(sites, template))
        genetic = material and all(units[s]['program'] == t['program']
                                   for s, t in zip(sites, template))
        whole = present and components[sites[0]]['identities'] == sorted(members)
        root = present and all(value in (0, 1) for value in roots)
        new = present and all(value not in (0, 1) for value in members)
        post = present and all(people[value]['birth_tick'] > selection['t0'] for value in members)
        chosen = present and all(value is not None for value in selected)
        slot = dict(sites=list(sites), identities=members, roots=roots,
                    materials=[None if units[s] is None else units[s]['material'] for s in sites],
                    programs=[None if units[s] is None else units[s]['program'] for s in sites],
                    birth_ticks=[None if i is None else people[i]['birth_tick'] for i in members],
                    selected_chains=[chain if not hits else chain[:chain.index(hits[0]) + 1]
                                     for chain, hits in chains],
                    selected_ancestors=selected,
                    components=[components.get(s) for s in sites],
                    occupied=present, material_match=material, genetic_match=genetic,
                    whole_component=whole, root_descendant=root, all_new=new,
                    post_birth=post, selected_ancestry=chosen,
                    copy=genetic and whole and root, new_copy=genetic and whole and root and new)
        result.append(slot)
    same(prior['tick'], tick, '044 state tick')
    same(prior['slots'], result, '044 independent full slot reconstruction')
    same(prior['new_copy_count'], sum(s['new_copy'] for s in result), '044 original new-copy metric')
    return result


OVERLAPS = ('G', 'physically_empty_both', 'G_genetic_match', 'G_whole_component',
            'G_root_descendant', 'G_all_new', 'G_post_birth', 'G_selected_ancestry',
            'G_other_copy_gates', 'double_new')


def turnover_row(tick, units, ids, slots, count):
    middle = [dict(site=s, identity=ids[s],
                   material=None if units[s] is None else units[s]['material']) for s in MIDDLE]
    b101, b102 = [m['identity'] is not None and m['material'] == 0 for m in middle]
    gap = not (b101 or b102)
    empty = all(m['identity'] is None for m in middle)
    upper, lower = slots[0], slots[2]
    both = {key: upper[key] and lower[key] for key in FLAGS}
    genetic = all(both[k] for k in ('occupied', 'material_match', 'genetic_match'))
    overlaps = dict(G=gap, physically_empty_both=empty, G_genetic_match=gap and genetic,
                    G_whole_component=gap and both['whole_component'],
                    G_root_descendant=gap and both['root_descendant'],
                    G_all_new=gap and both['all_new'],
                    G_post_birth=gap and both['post_birth'],
                    G_selected_ancestry=gap and both['selected_ancestry'],
                    G_other_copy_gates=gap and genetic and both['root_descendant'] and both['all_new'],
                    double_new=count >= 2)
    return dict(tick=tick, middle=middle, B101=b101, B102=b102, G=gap,
                physically_empty_both=empty, upper=deepcopy(upper), lower=deepcopy(lower),
                both_gates=both, genetic_context=genetic,
                actual_whole_components=both['whole_component'],
                component_equivalence=(gap == both['whole_component']) if genetic else None,
                actual_double_new=count >= 2, overlaps=overlaps)


def intervals(diagnostic, values):
    """Partition active runs, carrying a diagnostic-only left-censored run."""
    result = []
    active = bool(diagnostic)
    start = None
    ticks = []
    left = active
    for tick, value in values:
        if value and not active:
            active, start, left = True, tick, False
        if value:
            ticks.append(tick)
        if active and not value:
            result.append(dict(start=ticks[0] if ticks else None,
                               end=ticks[-1] if ticks else None, length=len(ticks),
                               left_censored=left, right_censored=False,
                               entry_tick=start, exit_tick=tick))
            active, ticks, start = False, [], None
    if active:
        result.append(dict(start=ticks[0] if ticks else None,
                           end=ticks[-1] if ticks else None, length=len(ticks),
                           left_censored=left, right_censored=True,
                           entry_tick=start, exit_tick=None))
    return result


def site_gaps(site, t0, initial_ids, people):
    """Associate every observed exit/empty entrance boundary with its next birth."""
    relevant = [p for p in people if p['site'] == site and
                (p['id'] == initial_ids[site] or t0 < p['birth_tick'] <= 32)]
    newborns = sorted((p for p in relevant if p['birth_tick'] > t0),
                      key=lambda p: (p['birth_tick'], p['id']))
    boundaries = ([] if initial_ids[site] is not None else [(t0, None)])
    boundaries += sorted((p['death_tick'], p) for p in relevant
                         if p['death_tick'] is not None and t0 < p['death_tick'] <= 32)
    result = []
    for boundary, predecessor in boundaries:
        successor = next((p for p in newborns if p['birth_tick'] >= boundary), None)
        end = successor['birth_tick'] if successor is not None else 32
        begin_empty = boundary + 1 if predecessor is None else boundary
        end_empty = end if successor is not None else 33
        empty = list(range(begin_empty, end_empty))
        result.append(dict(site=site,
                           predecessor=None if predecessor is None else predecessor['id'],
                           successor=None if successor is None else successor['id'],
                           start_boundary=boundary, end_boundary=end,
                           distance_ticks=end - boundary, empty_ticks=empty,
                           empty_saved_states=len(empty), left_censored=predecessor is None,
                           right_censored=successor is None,
                           same_tick_replacement=predecessor is not None and successor is not None and end == boundary,
                           material_changed=(predecessor['material'] != successor['material'])
                           if predecessor is not None and successor is not None else None))
    return result


def project_energy(identity, arm):
    """Read only the needed saved phase values; never run the physical ledger."""
    person = arm['final']['individuals'][identity]
    site = person['site']
    first = arm['initial']
    left = first['site_ids'][site] == identity
    formations = []
    entry = dict(kind='initial', tick=first['tick'], energy=first['units'][site]['energy']) if left else None
    exit_event = None
    previous_ids = first['site_ids']
    for row in arm['rows']:
        tick, physical = row['tick'], row['physical']
        proposals = physical['material']['proposals']
        if not left and tick == person['birth_tick']:
            same(row['site_ids'][site], identity, 'birth end identity')
            require(identity in [p['id'] for p in row['births']], 'birth identity event')
            incoming = [q for q in proposals if q['reason'] == 'formed' and q['target'] == site]
            same(len(incoming), 1, 'exactly one birth formation')
            q = incoming[0]
            same(previous_ids[q['source']], person['parent'], 'birth parent identity')
            same(q['child_energy'], person['birth_energy'], 'birth recorded child energy')
            same(physical['units'][site]['energy'], person['birth_energy'], 'birth saved energy')
            entry = dict(kind='birth', tick=tick, energy=person['birth_energy'])
        if previous_ids[site] == identity:
            require(tick > person['birth_tick'], 'newborn cannot act at birth')
            own = [q for q in proposals if q['source'] == site]
            if identity in row['deaths']:
                same(own, [], 'death direction ticket is not a proposal')
                require(site in physical['material']['dissolved'], 'physical death site')
                same(person['death_tick'], tick, 'death history tick')
                same(physical['interaction_units'][site]['energy'], 0, 'death preformation energy')
                exit_event = dict(kind='death', tick=tick, energy=0, right_censored=False)
            else:
                same(row['site_ids'][site], identity, 'surviving action identity')
                same(len(own), 1, 'one surviving actor proposal')
                q = own[0]
                if q['reason'] == 'formed':
                    target = q['target']
                    child = row['site_ids'][target]
                    require(child in [p['id'] for p in row['births']], 'successful child identity event')
                    same(arm['final']['individuals'][child]['parent'], identity, 'successful child parent')
                    same(arm['final']['individuals'][child]['birth_tick'], tick, 'successful child tick')
                    pre = physical['interaction_units'][site]['energy']
                    same(q['parent_energy'], physical['units'][site]['energy'], 'success saved parent energy')
                    same(q['child_energy'], physical['units'][target]['energy'], 'success saved child energy')
                    same(pre, q['parent_energy'] + q['child_energy'] + q['cost'], 'success saved split conservation')
                    formations.append(dict(tick=tick, source=site, target=target,
                                           parent_identity=identity, child_identity=child,
                                           preformation_energy=pre, parent_energy=q['parent_energy'],
                                           child_energy=q['child_energy']))
        previous_ids = row['site_ids']
    require(entry is not None, 'observed entry required')
    if exit_event is None:
        same(person['death_tick'], None, 'endpoint living history')
        same(arm['final']['site_ids'][site], identity, 'endpoint identity')
        exit_event = dict(kind='endpoint', tick=32,
                          energy=arm['final']['units'][site]['energy'], right_censored=True)
    return entry, formations, exit_event


def reuse_energy(identity, arm, reference, old_records):
    """Project already verified 042 ledger fields, without lifecycle recalculation."""
    same(reference['source_path'], 'data/v4-study-042/records.json', '042 source path')
    same(digest(reference['source_path']), reference['source_file_sha256'], '042 raw bytes')
    parts = reference['json_pointer'].strip('/').split('/')
    require(len(parts) == 3 and parts[1] == 'identities', '042 exact JSON pointer')
    old_case = old_records[int(parts[0])]
    ledger = old_case['identities'][int(parts[2])]
    same(canonical_hash(ledger), reference['normalized_record_sha256'], '042 normalized record hash')
    same(ledger['identity'], identity, '042 exact identity')
    person = arm['final']['individuals'][identity]
    for key in ('site', 'parent', 'birth_tick', 'birth_energy'):
        same(ledger[key], person[key], '042 birth field ' + key)
    first, last = ledger['rows'][0], ledger['rows'][-1]
    entry = dict(kind='initial' if ledger['left_censored'] else 'birth',
                 tick=first['tick'], energy=first['end_energy'])
    successes = []
    for action in ledger['rows']:
        if action.get('reason') != 'formed':
            continue
        q = action['proposal']
        successes.append(dict(tick=action['tick'], source=q['source'], target=q['target'],
                              parent_identity=identity, child_identity=q['child_id'],
                              preformation_energy=action['preformation_energy'],
                              parent_energy=action['end_energy'], child_energy=action['child_transfer']))
    right = ledger['window']['right_censored']
    exit_event = dict(kind='endpoint' if right else 'death',
                      tick=32 if right else ledger['window']['death_tick'],
                      energy=last['end_energy'], right_censored=right)
    return entry, successes, exit_event


def verify_pair(encoding, branch, prior044, census_arms, reuse, old_records):
    selection = branch['selection']
    seed, t0 = selection['seed'], selection['t0']
    same(selection, prior044['selection'], '044 exact selection')
    same(encoding, prior044['encoding'], '044 encoding')
    same(branch['control']['initial'], branch['ablation']['initial'], 'paired t0 diagnostic')
    source = read(selection['source'])
    template = [source['initial']['units'][s] for s in (85, 86)]
    answer = dict(encoding=encoding, selection=deepcopy(selection), arms={})
    for name in ARMS:
        arm, prior = branch[name], prior044['arms'][name]
        first, people = arm['initial'], arm['final']['individuals']
        same(first['tick'], t0, 't0 state tick')
        same([r['tick'] for r in arm['rows']], list(range(t0 + 1, 33)), 'continuous future window')
        same(len(prior['rows']), len(arm['rows']), '044 complete future window')
        census = [c for c in census_arms if (c['encoding'], c['seed'], c['arm']) == (encoding, seed, name)]
        same(len(census), 1, 'unique census arm')
        census = census[0]
        same(census['t0'], t0, 'census t0')
        same(census['saved_states'], len(arm['rows']), 'census window')
        references = [r for r in reuse if (r['encoding'], r['seed'], r['arm']) == (encoding, seed, name)]
        is_reuse = census['energy_plan'] == 'reuse_042'
        if is_reuse:
            require(name == 'control', '042 cannot map new-policy arm')
            old_path = f'data/v4-study-039/cases/{encoding}-{seed}.json'
            old_branch = read(old_path)
            same(old_branch['selection'], selection, '042 old/new selection')
            same(old_branch['ablation'], arm, '042 complete saved arm equality')
            old_cases = [case for case in old_records if (case['encoding'], case['selection']['seed']) == (encoding, seed)]
            same(len(old_cases), 1, '042 unique old case')
            same(old_cases[0]['selection'], selection, '042 ledger selection')
            for reference in references:
                same(reference['old_branch_source'], old_path, '042 old branch binding')
                same(reference['paired_branch_source'], census['source'], '042 paired branch binding')
                same(reference['complete_old_arm_equal'], True, '042 complete object proof')
                same(reference['ledger_recalculated'], False, '042 no recalculation')
        else:
            same(references, [], 'new-policy and other arms cannot reuse 042')
        states = [(t0, first['units'], first['site_ids'], prior['diagnostic'])]
        states += [(r['tick'], r['physical']['units'], r['site_ids'], old)
                   for r, old in zip(arm['rows'], prior['rows'])]
        seen = set()
        rows, anomalies, transitions = [], [], []
        for tick, units, ids, old in states:
            slots = verify_slots(units, ids, tick, people, selection, template, old)
            rows.append(turnover_row(tick, units, ids, slots, old['new_copy_count']))
            for site in MIDDLE:
                identity = ids[site]
                if identity is None:
                    continue
                seen.add(identity)
                person = people[identity]
                same(person['id'], identity, 'history identity')
                same(person['site'], site, 'history site')
                require(person['birth_tick'] <= tick, 'identity cannot predate birth')
                require(person['death_tick'] is None or person['death_tick'] > tick,
                        'identity cannot survive recorded death')
                if units[site]['material'] != person['material']:
                    anomalies.append(dict(tick=tick, site=site, identity=identity,
                                          birth_material=person['material'], observed_material=units[site]['material']))
        diagnostic, rows = rows[0], rows[1:]
        expected_ids = {p['id'] for p in people if p['site'] in MIDDLE and
                        (first['site_ids'][p['site']] == p['id'] or t0 < p['birth_tick'] <= 32)}
        same(sorted(seen), sorted(expected_ids), 'all middle identities seen')
        same(sorted(seen), sorted(p['identity'] for p in census['identities']), 'frozen census identities')
        if is_reuse:
            same(sorted(r['identity'] for r in references), sorted(seen), 'exact 042 identity mapping')
        previous_ids = first['site_ids']
        previous_units = first['units']
        for physical_row, old in zip(arm['rows'], prior['rows']):
            tick, physical = physical_row['tick'], physical_row['physical']
            ids, units = physical_row['site_ids'], physical['units']
            births = sorted(ids[q['target']] for q in physical['material']['proposals'] if q['reason'] == 'formed')
            deaths = sorted(previous_ids[s] for s in physical['material']['dissolved'])
            same(births, sorted(p['id'] for p in physical_row['births']), 'saved birth identity events')
            same(deaths, sorted(physical_row['deaths']), 'saved death identity events')
            same(births, [p['id'] for p in people if p['birth_tick'] == tick], 'birth history events')
            same(deaths, [p['id'] for p in people if p['death_tick'] == tick], 'death history events')
            def witness(identity):
                p = people[identity]
                return dict(identity=identity, site=p['site'], material=p['material'], program=p['program'],
                            birth_tick=p['birth_tick'], parent=p['parent'])
            same(old['births'], [witness(i) for i in births], '044 physical birth witnesses')
            same(old['deaths'], [witness(i) for i in deaths], '044 physical death witnesses')
            for site in MIDDLE:
                old_id, new_id = previous_ids[site], ids[site]
                old_mat = None if previous_units[site] is None else previous_units[site]['material']
                new_mat = None if units[site] is None else units[site]['material']
                if old_id != new_id or old_mat != new_mat:
                    transitions.append(dict(tick=tick, site=site, before_identity=old_id,
                                            after_identity=new_id, before_material=old_mat,
                                            after_material=new_mat, identity_changed=old_id != new_id,
                                            material_changed=old_mat != new_mat))
            previous_ids, previous_units = ids, units
        same(arm['final']['site_ids'], previous_ids, 'final saved identity state')
        same(arm['final']['units'], previous_units, 'final saved physical state')
        identities = []
        for identity in sorted(seen):
            person = people[identity]
            site, parent = person['site'], person['parent']
            left = first['site_ids'][site] == identity
            frozen = next(p for p in census['identities'] if p['identity'] == identity)
            for field, actual in (('site', site), ('parent', parent), ('birth_tick', person['birth_tick']),
                                  ('left_censored', left), ('birth_material', person['material'])):
                same(frozen[field], actual, 'frozen identity field ' + field)
            chain, selected = ancestry(identity, people, selection['offspring_ids'])
            source_site = people[parent]['site'] if parent is not None else None
            reference = next((r for r in references if r['identity'] == identity), None)
            if reference is not None:
                entry, successes, exit_event = reuse_energy(identity, arm, reference, old_records)
            else:
                entry, successes, exit_event = project_energy(identity, arm)
            identities.append(dict(key=[encoding, seed, name, identity], identity=identity, site=site,
                                   parent=parent, source_site=source_site, source_region=region(source_site),
                                   ancestry_chain=chain, selected_ancestors=selected,
                                   birth_tick=person['birth_tick'], birth_energy=person['birth_energy'],
                                   birth_material=person['material'], left_censored=left,
                                   entry=entry, successful_formations=successes, exit=exit_event,
                                   energy_source=dict(mode='reuse_042' if reference is not None else 'event_projection',
                                                      reference=deepcopy(reference))))
        gaps = [gap for site in MIDDLE for gap in site_gaps(site, t0, first['site_ids'], people)]
        by_tick = {tick: ids for tick, _, ids, _ in states}
        for gap in gaps:
            require(all(by_tick[tick][gap['site']] is None for tick in gap['empty_ticks']),
                    'gap full saved states are physically empty')
        runs = {key: intervals(diagnostic['overlaps'][key], [(r['tick'], r['overlaps'][key]) for r in rows])
                for key in OVERLAPS}
        counts = [r['new_copy_count'] for r in prior['rows']]
        episodes = [[r['start'], r['end']] for r in runs['double_new'] if r['length'] > 0]
        prior_binding = dict(new_copy_counts=counts, episodes=episodes, matched=True)
        same(prior_binding, prior['prior043'], '044 prior metric binding')
        same(episodes, arm['episodes'], '043 original episodes')
        same(counts, arm['new_copy_counts'], '043 original copy counts')
        same(max((r['length'] for r in runs['double_new']), default=0), arm['metrics']['longest_double'],
             '043 original longest duration')
        answer['arms'][name] = dict(arm=name, t0=t0, saved_steps=len(rows), identities=identities,
                                    diagnostic=diagnostic, rows=rows, gaps=gaps, intervals=runs,
                                    transitions=transitions, material_anomalies=anomalies,
                                    component_counterexamples=[deepcopy(r) for r in [diagnostic] + rows
                                                               if r['component_equivalence'] is False],
                                    prior044=prior_binding)
    return answer


def group(arms):
    identities = [i for arm in arms for i in arm['identities']]
    gaps = [g for arm in arms for g in arm['gaps']]
    return dict(n=len(arms), saved_steps=sum(arm['saved_steps'] for arm in arms),
                diagnostic_states=len(arms), identities=len(identities),
                births=sum(not i['left_censored'] for i in identities),
                left_censored=sum(i['left_censored'] for i in identities),
                right_censored=sum(i['exit']['right_censored'] for i in identities),
                natural_deaths=sum(i['exit']['kind'] == 'death' for i in identities),
                successes=sum(len(i['successful_formations']) for i in identities),
                reused_identities=sum(i['energy_source']['mode'] == 'reuse_042' for i in identities),
                projected_identities=sum(i['energy_source']['mode'] == 'event_projection' for i in identities),
                gaps=len(gaps), same_tick_replacements=sum(g['same_tick_replacement'] for g in gaps),
                identity_replacements=sum(g['predecessor'] is not None and g['successor'] is not None for g in gaps),
                material_replacements=sum(g['material_changed'] is True for g in gaps),
                left_censored_gaps=sum(g['left_censored'] for g in gaps),
                right_censored_gaps=sum(g['right_censored'] for g in gaps),
                empty_saved_states=sum(g['empty_saved_states'] for g in gaps),
                material_anomalies=sum(len(arm['material_anomalies']) for arm in arms),
                component_counterexamples=sum(len(arm['component_counterexamples']) for arm in arms),
                transitions=sum(len(arm['transitions']) for arm in arms),
                ticks={key: sum(r['overlaps'][key] for arm in arms for r in arm['rows']) for key in OVERLAPS},
                intervals={key: sum(len(arm['intervals'][key]) for arm in arms) for key in OVERLAPS},
                longest={key: max((run['length'] for arm in arms for run in arm['intervals'][key]), default=0)
                         for key in OVERLAPS})


def difference(new, old):
    if isinstance(new, dict):
        same(sorted(new), sorted(old), 'paired summary fields')
        return {key: difference(new[key], old[key]) for key in new}
    return new - old


def summarize(records, index):
    cells = []
    for encoding in ENCODINGS:
        for category in CATEGORIES:
            chosen = [r for r in records if r['encoding'] == encoding and r['selection']['category'] == category]
            for arm in ARMS:
                cells.append(dict(encoding=encoding, category=category, arm=arm, policy_denominator=20,
                                  triggered_encoding_count=sum(i['encoding'] == encoding and i['trigger'] for i in index),
                                  **group([r['arms'][arm] for r in chosen])))
    return dict(index_cases=len(index), triggered=sum(i['trigger'] for i in index), no_trigger=sum(not i['trigger'] for i in index),
                cells=cells, overall={arm: group([r['arms'][arm] for r in records]) for arm in ARMS},
                paired=[dict(encoding=r['encoding'], seed=r['selection']['seed'],
                             delta=difference(group([r['arms']['ablation']]), group([r['arms']['control']])))
                        for r in records])


FIXED_METADATA = dict(status='complete', planned_cases=28, completed_cases=28,
                      planned_arms=56, completed_arms=56, index_cases=100,
                      no_trigger_cases=72, saved_steps=780, diagnostic_states=56,
                      identities=202, left_censored_identities=12, reused_identities=35,
                      reuse_arms=8, projected_identities=167, event_projection_arms=48,
                      new_simulation_steps=0, new_environment_sources=0,
                      new_independent_initial_worlds=0,
                      time_limit_seconds=600, storage_limit_bytes=134217728)
OUTPUT_NAMES = ('metadata.json', 'records.json', 'summary.json', 'index.json')


def output_capture():
    hashes, errors = capture([str(OUTPUT / name) for name in OUTPUT_NAMES])
    return ({Path(path).name: sha for path, sha in hashes.items()},
            {Path(path).name: error for path, error in errors.items()})


def verify_metadata(meta, paths, bound, output_hashes):
    for key, value in FIXED_METADATA.items():
        same(meta[key], value, 'metadata ' + key)
    for key in ('input_inventory_errors', 'input_read_errors_before', 'input_read_errors_after'):
        same(meta[key], {}, 'metadata ' + key)
    same(meta['input_paths'], paths, 'metadata exact input inventory')
    same(meta['input_sha256'], bound, 'producer source before hashes')
    same(meta['input_sha256_after'], bound, 'producer source after hashes')
    same(meta['output_sha256'], {name: output_hashes[name] for name in OUTPUT_NAMES if name != 'metadata.json'},
         'producer output hashes')
    require(isinstance(meta['git_commit'], str) and len(meta['git_commit']) == 40 and
            all(char in '0123456789abcdef' for char in meta['git_commit']), 'producer commit hash')
    require(type(meta['elapsed_seconds']) in (int, float) and math.isfinite(meta['elapsed_seconds']) and
            0 <= meta['elapsed_seconds'] < 600, 'producer time budget')


def main():
    """Formal verifier. The caller must authorize the full queue separately."""
    proof = OUTPUT / 'independent-verification.json'
    failure = OUTPUT / 'verification-failure.json'
    require(OUTPUT.is_dir(), 'producer output directory required')
    require(not proof.exists() and not failure.exists(), 'exclusive verification output')
    start = monotonic()
    paths = []
    result = dict(status='running', completed_cases=0, completed_arms=0, saved_steps=0,
                  diagnostic_states=0, new_simulation_steps=0,
                  new_environment_sources=0, new_independent_initial_worlds=0,
                  review_mode=AUTHOR, time_limit_seconds=600, storage_limit_bytes=134217728,
                  verifier_sha256=digest(Path(__file__)), input_sha256={})
    try:
        result['files_sha256_before'], result['output_read_errors_before'] = output_capture()
        same(sorted(p.name for p in OUTPUT.iterdir()), sorted(OUTPUT_NAMES), 'exclusive producer output set')
        same(result['output_read_errors_before'], {}, 'producer readable output set')
        result['input_inventory_errors'] = {}
        paths = input_paths(result['input_inventory_errors'])
        result['input_paths'] = paths
        result['input_sha256'], result['input_read_errors_before'] = capture(paths)
        same(result['input_inventory_errors'], {}, 'input inventory errors')
        same(result['input_read_errors_before'], {}, 'source read errors')
        bound = bindings()
        same(paths, sorted(bound), 'complete source inventory')
        same(result['input_sha256'], bound, 'validated method and source bindings')
        check_budget(start, OUTPUT)
        meta = read(OUTPUT / 'metadata.json')
        verify_metadata(meta, paths, bound, result['files_sha256_before'])
        result['producer_git_commit'] = meta['git_commit']
        census = read('docs/research/results/v4-study-045-design-census.json')
        index = read('data/v4-study-044/index.json')
        same(census['index'], index, 'frozen complete index')
        same(read(OUTPUT / 'index.json'), index, '045 full100 index preservation')
        same(len(index), 100, '100 policy denominator')
        same(sum(not i['trigger'] for i in index), 72, '72 not-applicable cases')
        same(sum(i['short_window'] for i in index), 10, '10 short windows')
        for encoding in ENCODINGS:
            same(sorted(i['seed'] for i in index if i['encoding'] == encoding),
                 list(range(120000, 120020)), 'all seeds in each encoding')
        require(all(i['branch'] is None and i['applicability'] == 'not_applicable'
                    for i in index if not i['trigger']), 'explicit non-trigger applicability')
        same(len(census['arms']), 56, '56 census arms')
        same(len(census['reuse_042']), 35, '35 frozen reuse pointers')
        old_records = read('data/v4-study-042/records.json')
        same(len(old_records), 8, 'eight immutable old ledger cases')
        previous = read('data/v4-study-044/records.json')
        same([(r['encoding'], r['selection']['seed']) for r in previous],
             [(i['encoding'], i['seed']) for i in index if i['trigger']], 'all28 ordered previous cases')
        prior_map = {(r['encoding'], r['selection']['seed']): r for r in previous}
        records = []
        for item in index:
            if not item['trigger']:
                continue
            check_budget(start, OUTPUT)
            branch = read(item['branch'])
            same(branch['selection']['seed'], item['seed'], 'indexed seed')
            same(branch['selection']['source'], item['source'], 'indexed source')
            records.append(verify_pair(item['encoding'], branch, prior_map[(item['encoding'], item['seed'])],
                                       census['arms'], census['reuse_042'], old_records))
            result.update(completed_cases=len(records), completed_arms=2 * len(records),
                          saved_steps=sum(r['arms'][a]['saved_steps'] for r in records for a in ARMS),
                          diagnostic_states=2 * len(records))
        for key in ('completed_cases', 'completed_arms', 'saved_steps', 'diagnostic_states'):
            same(result[key], FIXED_METADATA[key], 'complete ' + key)
        summary = summarize(records, index)
        stats = summary['overall']
        for key, expected in (('identities', 202), ('left_censored', 12), ('reused_identities', 35),
                              ('projected_identities', 167)):
            same(sum(stats[a][key] for a in ARMS), expected, 'full identity denominator ' + key)
        same(sum(a['energy_plan'] == 'reuse_042' for a in census['arms']), 8, 'eight reused arms')
        same(sum(a['energy_plan'] == 'needed_event_projection' for a in census['arms']), 48, '48 projection arms')
        same(len(summary['cells']), 20, '20 cells including all zero cells')
        same(len(summary['paired']), 28, '28 paired contrasts')
        same(read(OUTPUT / 'records.json'), records, 'all independent identities events gaps and gate overlaps')
        same(read(OUTPUT / 'summary.json'), summary, 'all independent summary fields and paired contrasts')
        same(bindings(), bound, 'final immutable source validation')
        check_budget(start, OUTPUT)
        result.update(status='verified', identities=202, left_censored_identities=12,
                      reused_identities=35, projected_identities=167, reuse_arms=8,
                      event_projection_arms=48, index_cases=100, no_trigger_cases=72,
                      short_window_pairs=10, summary_cells=20, paired_contrasts=28,
                      input_files=len(bound), files_sha256=result['files_sha256_before'])
    except BaseException as exc:
        result.update(status='failed', error=repr(exc))
        raise
    finally:
        result['input_sha256_after'], result['input_read_errors_after'] = capture(paths)
        result['files_sha256_after'], result['output_read_errors_after'] = output_capture()
        result['elapsed_seconds'] = monotonic() - start
        if result['status'] == 'verified':
            try:
                same(result['input_sha256_after'], result['input_sha256'], 'final captured source hashes')
                same(result['input_read_errors_after'], {}, 'final source readability')
                same(result['files_sha256_after'], result['files_sha256_before'], 'unchanged producer outputs')
                same(result['output_read_errors_after'], {}, 'final output readability')
                payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
                check_budget(start, OUTPUT, len(payload.encode()))
            except BaseException as exc:
                result.update(status='failed', error=repr(exc))
                with failure.open('x') as stream:
                    json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
                    stream.write('\n')
                raise
        destination = proof if result['status'] == 'verified' else failure
        with destination.open('x') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')


if __name__ == '__main__':
    main()
