"""Passive component boundaries and birth-member overlap; no dynamic inputs."""
from itertools import combinations

VERSION = 'v4-structure-observer-1'


def partition(members, edges):
    """Canonical connected partition of unique nonnegative birth identities."""
    members = list(members)
    if any(type(i) is not int or i < 0 for i in members) or len(set(members)) != len(members):
        raise ValueError('unique nonnegative identities required')
    neighbors = {i: set() for i in members}
    for a, b in edges:
        if a not in neighbors or b not in neighbors or a == b:
            raise ValueError('invalid component edge')
        neighbors[a].add(b)
        neighbors[b].add(a)
    remaining = set(members)
    result = []
    while remaining:
        reached = {min(remaining)}
        pending = list(reached)
        while pending:
            new = neighbors[pending.pop()] - reached
            reached.update(new)
            pending.extend(new)
        remaining.difference_update(reached)
        result.append(sorted(reached))
    return result


def _members(groups):
    result = {}
    for index, group in enumerate(groups):
        if not group:
            raise ValueError('empty component')
        for identity in group:
            if type(identity) is not int or identity < 0 or identity in result:
                raise ValueError('invalid or repeated component member')
            result[identity] = index
    return result


def continuity(previous, current):
    """Retain every surviving-member overlap, including ambiguous splits/merges.

    Indices refer only to the supplied snapshots, never persistent group IDs.
    No-overlap components may still contain descendants of previous members.
    """
    old, new = _members(previous), _members(current)
    intersections = {}
    for identity in old.keys() & new.keys():
        key = (old[identity], new[identity])
        intersections[key] = intersections.get(key, 0) + 1
    edges = [dict(previous=a, current=b, shared=n,
                  previous_size=len(previous[a]), current_size=len(current[b]))
             for (a, b), n in sorted(intersections.items())]
    outgoing = {a: set() for a in range(len(previous))}
    incoming = {b: set() for b in range(len(current))}
    for a, b in intersections:
        outgoing[a].add(b)
        incoming[b].add(a)
    return dict(overlaps=edges, surviving_members=len(old.keys() & new.keys()),
                lost_members=sorted(old.keys() - new.keys()),
                added_members=sorted(new.keys() - old.keys()),
                splits=[a for a, links in outgoing.items() if len(links) > 1],
                merges=[b for b, links in incoming.items() if len(links) > 1],
                previous_without_overlap=[a for a, links in outgoing.items() if not links],
                current_without_overlap=[b for b, links in incoming.items() if not links])


def snapshot(units, site_ids, width, height, *, phase, bonds=None):
    """Partition one explicitly declared phase using serialized states/identities.

    Realized bonds must come from the same audited interaction state. They are
    supplied observations, not recomputed from post-charge energy. Final states
    have only geometric definitions and reject an interaction bond list.
    """
    if any(type(v) is not int or v < 3 for v in (width, height)):
        raise ValueError('periodic dimensions must be integers >=3')
    if len(units) != width * height or len(site_ids) != len(units):
        raise ValueError('geometry mismatch')
    if phase not in ('interaction', 'final'):
        raise ValueError('explicit interaction/final phase required')
    if (phase == 'interaction') != (bonds is not None):
        raise ValueError('bonds belong only to interaction phase')
    for u, identity in zip(units, site_ids):
        if (u is None) != (identity is None):
            raise ValueError('phase identity/occupation mismatch')
        if u is not None and (type(u['material']) is not int or not 0 <= u['material'] <= 3):
            raise ValueError('invalid expressed material')
    members = [i for i in site_ids if i is not None]
    partition(members, [])  # Validate unique birth identities before edge lookup.
    contact, material = set(), set()
    for a, u in enumerate(units):
        if u is None:
            continue
        x, y = a % width, a // width
        for b in (y * width + (x + 1) % width, ((y + 1) % height) * width + x):
            if units[b] is not None:
                edge = tuple(sorted((a, b)))
                contact.add(edge)
                if u['material'] == units[b]['material']:
                    material.add(edge)
    definitions = dict(contact=contact, material=material)
    if bonds is not None:
        realized = set()
        for a, b in bonds:
            if type(a) is not int or type(b) is not int:
                raise ValueError('integer bond sites required')
            edge = tuple(sorted((a, b)))
            if edge not in material or edge in realized:
                raise ValueError('invalid or duplicate realized bond')
            realized.add(edge)
        definitions['bond'] = realized
    groups = {name: partition(members, [(site_ids[a], site_ids[b]) for a, b in edges])
              for name, edges in definitions.items()}
    metrics = {}
    memberships = {}
    for name, components in groups.items():
        sizes = sorted(len(group) for group in components)
        metrics[name] = dict(component_count=len(sizes), sizes=sizes,
                             singleton_units=sizes.count(1), occupied_units=len(members),
                             singleton_fraction=None if not members else sizes.count(1) / len(members))
        memberships[name] = {i: frozenset(group) for group in components for i in group}
    disagreement = []
    for a, b in combinations(groups, 2):
        numerator = sum(memberships[a][i] != memberships[b][i] for i in members)
        disagreement.append(dict(first=a, second=b, numerator=numerator, denominator=len(members),
                                 fraction=None if not members else numerator / len(members)))
    return dict(version=VERSION, phase=phase, components=groups, metrics=metrics,
                boundary_disagreement=disagreement)
