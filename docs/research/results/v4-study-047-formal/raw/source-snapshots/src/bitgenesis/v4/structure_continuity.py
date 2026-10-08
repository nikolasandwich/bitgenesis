"""Passive sampled cohesion of nearest-anchor-cut birth lineages.

'Closed' means equality to one observed component, not causal/organizational
closure. These observations cannot establish organism identity or reproduction.
"""
STATES = ('extinct', 'fragmented', 'mixed', 'closed_singleton', 'closed_multi')
DEFINITIONS = (('interaction', 'contact'), ('interaction', 'material'),
               ('interaction', 'bond'), ('final', 'contact'), ('final', 'material'))


def members(groups, parents):
    result = {}
    for component, group in enumerate(groups):
        if not group:
            raise ValueError('empty component')
        for identity in group:
            if type(identity) is not int or not 0 <= identity < len(parents) or identity in result:
                raise ValueError('invalid or duplicated birth identity')
            result[identity] = component
    return result


def follow(series, parents, anchor, horizons):
    """Return all anchor components at every requested horizon, no best matching."""
    if not horizons or any(type(h) is not int or h < 1 for h in horizons) or len(set(horizons)) != len(horizons):
        raise ValueError('unique positive horizons required')
    if type(anchor) is not int or anchor < 0 or any(t not in series for t in range(anchor, anchor+max(horizons)+1)):
        raise ValueError('complete ordered snapshot interval required')
    for identity, parent in enumerate(parents):
        if parent is not None and (type(parent) is not int or not 0 <= parent < identity):
            raise ValueError('parent must precede birth identity')
    initial = series[anchor]
    anchors = members(initial, parents)
    roots = []
    for identity, parent in enumerate(parents):
        roots.append(identity if identity in anchors else None if parent is None else roots[parent])
    history = [dict(state_steps=dict.fromkeys(STATES, 0), outsider_unit_steps=dict.fromkeys(STATES, 0),
                    first_break_tick=None, first_complete_replacement_tick=None) for _ in initial]
    results = {}
    for tick in range(anchor+1, anchor+max(horizons)+1):
        groups = series[tick]
        living = members(groups, parents)
        destinations = [{} for _ in initial]
        represented = [set() for _ in initial]
        survivors = [0 for _ in initial]
        for identity, destination in living.items():
            root = roots[identity]
            if root is None:
                raise ValueError('living identity has no anchor-cut ancestor')
            owner = anchors[root]
            destinations[owner][destination] = destinations[owner].get(destination, 0)+1
            represented[owner].add(root)
            survivors[owner] += identity in anchors
        output = []
        for index, origin in enumerate(initial):
            targets = destinations[index]
            descendants = sum(targets.values())
            outsiders = sum(len(groups[target])-count for target, count in targets.items())
            state = ('extinct' if not descendants else 'fragmented' if len(targets)>1 else
                     'mixed' if outsiders else 'closed_singleton' if descendants==1 else 'closed_multi')
            hist = history[index]
            hist['state_steps'][state] += 1
            hist['outsider_unit_steps'][state] += outsiders
            if state != 'closed_multi' and hist['first_break_tick'] is None:
                hist['first_break_tick'] = tick
            replaced = descendants > 0 and survivors[index] == 0
            if replaced and hist['first_complete_replacement_tick'] is None:
                hist['first_complete_replacement_tick'] = tick
            if tick-anchor in horizons:
                continuous = len(origin)>=2 and hist['first_break_tick'] is None
                output.append(dict(component=index, anchor_members=list(origin), anchor_size=len(origin),
                    anchor_world_units=len(anchors), whole_world_anchor=len(origin)==len(anchors),
                    state_steps=dict(hist['state_steps']), outsider_unit_steps=dict(hist['outsider_unit_steps']),
                    first_break_tick=hist['first_break_tick'],
                    first_complete_replacement_tick=hist['first_complete_replacement_tick'],
                    endpoint=dict(state=state, descendants=descendants, original_survivors=survivors[index],
                        new_descendants=descendants-survivors[index], represented_anchor_members=len(represented[index]),
                        destination_components=len(targets), outsiders=outsiders),
                    continuous_closed_multi=continuous, complete_replacement=replaced,
                    endpoint_closed_after_break=state=='closed_multi' and hist['first_break_tick'] is not None,
                    primary=continuous and replaced))
        if tick-anchor in horizons:
            results[tick-anchor] = output
    return results


def analyze(observed, parents, anchors=(100,200,300,400), horizons=(10,50,100)):
    rows = observed['observations']
    if len({r['tick'] for r in rows}) != len(rows):
        raise ValueError('duplicate snapshot tick')
    panels = []
    for phase, boundary in DEFINITIONS:
        series = {r['tick']: r[phase]['components'][boundary] for r in rows}
        for anchor in anchors:
            result = follow(series, parents, anchor, horizons)
            for horizon in horizons:
                panels.append(dict(phase=phase, boundary=boundary, anchor=anchor,
                                   horizon=horizon, records=result[horizon]))
    return panels
