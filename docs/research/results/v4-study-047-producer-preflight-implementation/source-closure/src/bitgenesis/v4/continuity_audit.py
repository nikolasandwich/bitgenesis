"""Independent event ancestry and set/parent-chain audit of sampled cohesion."""
import json
from pathlib import Path


def event_parents(directory, observed):
    """Assign IDs from raw event order without the runtime lineage Observer."""
    root = Path(directory)
    initial = json.loads((root/'initial.json').read_text(encoding='utf-8'))
    alive, parents, born = [], [], []
    for unit in initial['units']:
        alive.append(None if unit is None else len(parents))
        if unit is not None:
            parents.append(None)
            born.append(0)
    count = 0
    with (root/'steps.jsonl').open(encoding='utf-8') as stream:
        for index, line in enumerate(stream):
            row = json.loads(line)
            saved = observed['observations'][index]
            if row['tick'] != index+1 or saved['tick'] != row['tick'] or saved['interaction_site_ids'] != alive:
                raise ValueError('independent interaction identity mismatch')
            for site in row['material']['dissolved']:
                if alive[site] is None:
                    raise ValueError('missing dissolved identity')
                alive[site] = None
            for proposal in row['material']['proposals']:
                if proposal['reason'] == 'formed':
                    parent = alive[proposal['source']]
                    if parent is None or born[parent] == row['tick'] or alive[proposal['target']] is not None:
                        raise ValueError('invalid independently reconstructed birth')
                    alive[proposal['target']] = len(parents)
                    parents.append(parent)
                    born.append(row['tick'])
            if saved['final_site_ids'] != alive:
                raise ValueError('independent final identity mismatch')
            count += 1
    if count != len(observed['observations']):
        raise ValueError('event/observation horizon mismatch')
    return parents


def check_panels(observed, parents, panels, anchors=(100,200,300,400), horizons=(10,50,100)):
    """Recompute through backward parent walks and explicit component sets."""
    definitions = (('interaction','contact'), ('interaction','material'), ('interaction','bond'),
                   ('final','contact'), ('final','material'))
    states = ('extinct','fragmented','mixed','closed_singleton','closed_multi')
    keys = [(p['phase'],p['boundary'],p['anchor'],p['horizon']) for p in panels]
    expected_keys = {(p,b,a,h) for p,b in definitions for a in anchors for h in horizons}
    if len(keys) != len(expected_keys) or set(keys) != expected_keys:
        raise ValueError('panel coverage')
    saved = dict(zip(keys, panels))
    for identity, parent in enumerate(parents):
        if parent is not None and (type(parent) is not int or not 0 <= parent < identity):
            raise ValueError('invalid audit parent chain')
    snapshots = {r['tick']:r for r in observed['observations']}
    checked_records = 0
    for phase, boundary in definitions:
        for anchor in anchors:
            initial = snapshots[anchor][phase]['components'][boundary]
            origin_sets = [set(group) for group in initial]
            anchor_ids = set().union(*origin_sets) if initial else set()
            if len(anchor_ids) != sum(map(len, initial)):
                raise ValueError('duplicate anchor identity')
            intervals = [[] for _ in initial]
            for tick in range(anchor+1, anchor+max(horizons)+1):
                current = [set(g) for g in snapshots[tick][phase]['components'][boundary]]
                where = {i:j for j,g in enumerate(current) for i in g}
                if len(where) != sum(map(len,current)):
                    raise ValueError('duplicate audit identity')
                by_root = {i:set() for i in anchor_ids}
                for identity in where:
                    cursor = identity
                    while cursor is not None and cursor not in anchor_ids:
                        cursor = parents[cursor]
                    if cursor is None:
                        raise ValueError('missing anchor ancestry')
                    by_root[cursor].add(identity)
                for index, origins in enumerate(origin_sets):
                    cohort = set().union(*(by_root[i] for i in origins))
                    destinations = {where[i] for i in cohort}
                    reached = set().union(*(current[j] for j in destinations)) if destinations else set()
                    external = reached-cohort
                    if not cohort:
                        state = 'extinct'
                    elif len(destinations)>1:
                        state = 'fragmented'
                    elif external:
                        state = 'mixed'
                    elif len(cohort)==1:
                        state = 'closed_singleton'
                    else:
                        state = 'closed_multi'
                    endpoint = dict(state=state, descendants=len(cohort), original_survivors=len(cohort & origins),
                        new_descendants=len(cohort-origins), represented_anchor_members=sum(bool(by_root[i]) for i in origins),
                        destination_components=len(destinations), outsiders=len(external))
                    intervals[index].append(endpoint)
                if tick-anchor in horizons:
                    records = saved[(phase,boundary,anchor,tick-anchor)]['records']
                    if len(records) != len(initial):
                        raise ValueError('component coverage')
                    for index, (origins, history, actual) in enumerate(zip(origin_sets, intervals, records)):
                        breaks = [anchor+i+1 for i,e in enumerate(history) if e['state']!='closed_multi']
                        replacements = [anchor+i+1 for i,e in enumerate(history) if e['descendants'] and not e['original_survivors']]
                        terminal = history[-1]
                        continuous = len(origins)>=2 and not breaks
                        replaced = terminal['descendants']>0 and terminal['original_survivors']==0
                        expected = dict(component=index, anchor_members=initial[index], anchor_size=len(origins),
                            anchor_world_units=len(anchor_ids), whole_world_anchor=origins==anchor_ids,
                            state_steps={s:sum(e['state']==s for e in history) for s in states},
                            outsider_unit_steps={s:sum(e['outsiders'] for e in history if e['state']==s) for s in states},
                            first_break_tick=breaks[0] if breaks else None,
                            first_complete_replacement_tick=replacements[0] if replacements else None,
                            endpoint=terminal, continuous_closed_multi=continuous, complete_replacement=replaced,
                            endpoint_closed_after_break=terminal['state']=='closed_multi' and bool(breaks),
                            primary=continuous and replaced)
                        if actual != expected:
                            raise ValueError(f'continuity record mismatch: {phase}/{boundary}/{anchor}/{tick-anchor}/{index}')
                        checked_records += 1
    return dict(panels=len(panels), component_windows=checked_records,
                scope='independent parent-chain attribution and set-based sampled continuity; not organizational closure')
