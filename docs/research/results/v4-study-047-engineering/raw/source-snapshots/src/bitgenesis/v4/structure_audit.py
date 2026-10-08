"""Independent union-find reconstruction of saved structural observations."""
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path


def reconstruct(units, identities, width, height, phase, bonds=()):
    occupied = [i for i, u in enumerate(units) if u is not None]
    if any((u is None) != (i is None) for u, i in zip(units, identities)):
        raise ValueError('audit phase identities')
    edges = {'contact': [], 'material': []}
    if phase == 'interaction':
        edges['bond'] = list(bonds)
    # All occupied site pairs, independent of the observer's east/south scan.
    for a, b in combinations(occupied, 2):
        ax, ay, bx, by = a % width, a // width, b % width, b // width
        adjacent = (ay == by and (ax - bx) % width in (1, width - 1)) or (
            ax == bx and (ay - by) % height in (1, height - 1))
        if adjacent:
            edges['contact'].append((a, b))
            if units[a]['material'] == units[b]['material']:
                edges['material'].append((a, b))
    groups = {}
    metrics = {}
    for name, links in edges.items():
        parent = {i: i for i in occupied}
        def root(i):
            while i != parent[i]:
                i = parent[i]
            return i
        for a, b in links:
            parent[root(a)] = root(b)
        sets = {}
        for site in occupied:
            sets.setdefault(root(site), []).append(identities[site])
        groups[name] = sorted(sorted(group) for group in sets.values())
        sizes = sorted(map(len, groups[name]))
        metrics[name] = dict(component_count=len(sizes), sizes=sizes, singleton_units=sizes.count(1),
            occupied_units=len(occupied), singleton_fraction=sizes.count(1)/len(occupied) if occupied else None)
    differences = []
    for a, b in combinations(groups, 2):
        # Identical member sets represent agreement for all their members.
        same = set(map(tuple, groups[a])) & set(map(tuple, groups[b]))
        numerator = len(occupied) - sum(map(len, same))
        differences.append(dict(first=a, second=b, numerator=numerator, denominator=len(occupied),
                                fraction=numerator/len(occupied) if occupied else None))
    return dict(version='v4-structure-observer-1', phase=phase, components=groups,
                metrics=metrics, boundary_disagreement=differences)


def overlap(old, new):
    shared = [(a, b, len(set(x) & set(y))) for a, x in enumerate(old) for b, y in enumerate(new)
              if set(x) & set(y)]
    old_ids = set().union(*map(set, old)) if old else set()
    new_ids = set().union(*map(set, new)) if new else set()
    return dict(overlaps=[dict(previous=a, current=b, shared=n, previous_size=len(old[a]), current_size=len(new[b]))
                          for a, b, n in shared],
                surviving_members=len(old_ids & new_ids), lost_members=sorted(old_ids-new_ids),
                added_members=sorted(new_ids-old_ids),
                splits=[a for a in range(len(old)) if sum(x==a for x,_,_ in shared)>1],
                merges=[b for b in range(len(new)) if sum(y==b for _,y,_ in shared)>1],
                previous_without_overlap=[a for a in range(len(old)) if not any(x==a for x,_,_ in shared)],
                current_without_overlap=[b for b in range(len(new)) if not any(y==b for _,y,_ in shared)])


def audit(directory, observation_path):
    root, path = Path(directory), Path(observation_path)
    def hashes():
        return {p.name: sha256(p.read_bytes()).hexdigest() for p in sorted(root.iterdir()) if p.is_file()}
    original = hashes()
    observed_bytes = path.read_bytes()
    observed = json.loads(observed_bytes)
    meta = json.loads((root/'metadata.json').read_text(encoding='utf-8'))
    if meta['schema'] == 'v4-hereditary-run-1':
        from .hereditary_audit import audit as dynamics
    elif meta['schema'] == 'v4-program-assay-1':
        from .program_assay_audit import audit as dynamics
    elif meta['schema'] == 'v4-competition-1':
        from .competition_audit import audit as dynamics
    else:
        raise ValueError('unsupported structural source')
    checked = dynamics(root)
    if observed['input_sha256'] != original or observed['dynamics_audit'] != checked:
        raise ValueError('structural source binding')
    for name in ('structure_trace.py', 'structure.py', 'lineage.py'):
        if observed['observer_sha256'][name] != sha256((Path(__file__).parent/name).read_bytes()).hexdigest():
            raise ValueError('observer source binding')
    units = json.loads((root/'initial.json').read_text(encoding='utf-8'))['units']
    ids = [None] * len(units)
    counter = 0
    for site, u in enumerate(units):
        if u is not None:
            ids[site] = counter
            counter += 1
    width, height = meta['width'], meta['height']
    initial = reconstruct(units, ids, width, height, 'final')
    if initial != observed['initial'] or len(observed['observations']) != meta['steps']:
        raise ValueError('initial structure/horizon')
    previous = {'final': initial, 'interaction': None}
    partitions, transitions = 2, 0
    with (root/'steps.jsonl').open(encoding='utf-8') as stream:
        for index, line in enumerate(stream):
            row = json.loads(line)
            saved = observed['observations'][index]
            if saved['tick'] != row['tick'] or saved['interaction_site_ids'] != ids:
                raise ValueError('interaction identity mapping')
            snapshots = {'interaction': reconstruct(row['interaction_units'], ids, width, height,
                'interaction', row['driven']['interaction']['bonds'])}
            for site in row['material']['dissolved']:
                ids[site] = None
            for proposal in row['material']['proposals']:
                if proposal['reason'] == 'formed':
                    ids[proposal['target']] = counter
                    counter += 1
            if saved['final_site_ids'] != ids:
                raise ValueError('final identity mapping')
            snapshots['final'] = reconstruct(row['units'], ids, width, height, 'final')
            for phase, result in snapshots.items():
                links = None if previous[phase] is None else {
                    name: overlap(previous[phase]['components'][name], group)
                    for name, group in result['components'].items()}
                if saved[phase] != result or saved[phase+'_continuity'] != links:
                    raise ValueError('structural partition/metric/continuity mismatch')
                partitions += len(result['components'])
                transitions += 0 if links is None else len(links)
                previous[phase] = result
    if hashes() != original or path.read_bytes() != observed_bytes:
        raise ValueError('structural audit inputs changed')
    return dict(scope='independent partitions, phase birth IDs, metrics and member overlaps on audited dynamics; not group replication',
                partitions=partitions, transitions=transitions, ticks=meta['steps'],
                observation_sha256=sha256(observed_bytes).hexdigest(), input_sha256=original,
                auditor_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
