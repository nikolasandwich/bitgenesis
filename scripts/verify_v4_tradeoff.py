"""Independent retrospective verification; no production analysis imports."""
import json
import time
from fractions import Fraction
from hashlib import sha256
from itertools import product
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def mean(values):
    valid = [Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(valid) / len(valid)) if valid else None,
                available=len(valid), missing=len(values)-len(valid))


def reconstruct(directory):
    initial = read(directory/'initial.json')
    final = read(directory/'final.json')
    rows = [json.loads(line) for line in (directory/'steps.jsonl').read_text().splitlines()]
    require(len(rows) == 100 and [r['tick'] for r in rows] == list(range(1, 101)), '100 ordered snapshots')
    parents = final['parents']
    ancestors = {}
    for identity in range(len(parents)):
        cursor = identity
        while parents[cursor] is not None:
            parent = parents[cursor]
            require(type(parent) is int and 0 <= parent < cursor, 'backward parent chain')
            cursor = parent
        ancestors[identity] = cursor
    groups = initial['observation']['components']['material']
    starting = {i for i in initial['site_ids'] if i is not None}
    require(len(starting) == sum(i is not None for i in initial['site_ids']), 'initial duplicate identity')
    require(sum(map(len, groups)) == len(starting) and set().union(*map(set, groups)) == starting, 'initial partition')
    owner = {i: c for c, g in enumerate(groups) for i in g}
    require(all(parents[i] is None for i in starting), 'anchor identity roots')
    previous = starting
    seen = set(starting)
    births, deaths = [], []
    first = [None] * len(groups)
    first_state = [None] * len(groups)
    endpoints = None
    for row in rows:
        alive = {i for i in row['site_ids'] if i is not None}
        require(len(alive) == sum(i is not None for i in row['site_ids']), 'snapshot duplicate identity')
        added, removed = alive-previous, previous-alive
        require(not added.intersection(seen), 'identity resurrected')
        require(all(parents[i] in previous for i in added), 'birth parent absent')
        births.extend(added)
        deaths.extend(removed)
        seen.update(added)
        destinations = row['observation']['components']['material']
        flat = [i for g in destinations for i in g]
        require(len(flat) == len(alive) and set(flat) == alive, 'snapshot partition')
        cohort = [[] for _ in groups]
        for target, group in enumerate(destinations):
            for i in group:
                require(ancestors[i] in owner, 'unowned identity')
                cohort[owner[ancestors[i]]].append((i, target))
        endpoints = []
        for c, values in enumerate(cohort):
            identities = {i for i, _ in values}
            targets = {t for _, t in values}
            outsiders = sum(len(destinations[t]) for t in targets)-len(identities)
            state = ('extinct' if not identities else 'fragmented' if len(targets)>1 else
                     'mixed' if outsiders else 'closed_singleton' if len(identities)==1 else 'closed_multi')
            if state != 'closed_multi' and first[c] is None:
                first[c], first_state[c] = row['tick'], state
            originals = len(identities.intersection(groups[c]))
            endpoints.append(dict(state=state, descendants=len(identities), original_survivors=originals,
                                  new_descendants=len(identities)-originals,
                                  represented_anchor_members=len({ancestors[i] for i in identities}),
                                  destination_components=len(targets), outsiders=outsiders))
        previous = alive
    require(final['site_ids'] == rows[-1]['site_ids'], 'final identity snapshot')
    require(seen == set(range(len(parents))), 'complete identity history')
    result = []
    for c, group in enumerate(groups):
        born = [i for i in births if owner[ancestors[i]] == c]
        dead = [i for i in deaths if owner[ancestors[i]] == c]
        original_deaths = len(set(group).intersection(dead))
        require(endpoints[c]['descendants'] == len(group)+len(born)-len(dead), 'population balance')
        require(endpoints[c]['original_survivors'] == len(group)-original_deaths, 'original identity balance')
        result.append(dict(component=c, anchor_members=group, anchor_size=len(group),
                           whole_world_anchor=len(group)==len(starting),
                           continuous=len(group)>=2 and first[c] is None,
                           first_break_tick=first[c], first_break_state=first_state[c], endpoint=endpoints[c],
                           births=len(born), deaths=len(dead), original_deaths=original_deaths,
                           descendant_deaths=len(dead)-original_deaths))
    return result


def main():
    start = time.monotonic()
    source, target = Path('data/v4-study-012'), Path('data/v4-study-012-tradeoff')
    metadata = read(target/'metadata.json')
    require(metadata['status']=='complete' and metadata['completed_pairs']==metadata['planned_pairs']==40,
            'complete 40-pair analysis')
    require(metadata['independent_new_samples']==0, 'retrospective only')
    require(metadata['elapsed_seconds'] <= 1800, 'analysis time budget')
    require(sum(p.stat().st_size for p in target.iterdir()) < 128*1024**2, 'analysis storage budget')
    require({p.name for p in target.iterdir()} == {'metadata.json','results.json','summary.json'}, 'exclusive output inventory')
    tracked = {}
    def bind(path, expected=None):
        value = digest(path)
        require(expected is None or value == expected, f'hash mismatch: {path}')
        tracked[str(path)] = value
    bind(Path(__file__))
    bind(Path('scripts/analyze_v4_tradeoff.py'), metadata['script_sha256'])
    bind(Path('docs/design/v4-exchange-tradeoff-supplement.md'), metadata['design_sha256'])
    bind(source/'results.json', metadata['study012_results_sha256'])
    bind(target/'metadata.json')
    for name in ('results','summary'):
        bind(target/f'{name}.json', metadata[f'{name}_sha256'])
    for name in ('metadata','results','summary','aggregation-verification'):
        path = source/f'{name}.json'
        bind(path)
        bind(Path(f'docs/research/results/v4-study-012-{name}.json'), digest(path))
    source_meta = read(source/'metadata.json')
    require(source_meta['status']=='complete' and source_meta['completed_branches']==80, 'source completeness')
    for field in ('bindings_sha256','source_bindings_sha256'):
        for path, value in source_meta[field].items():
            bind(Path(path), value)
    originals = read(source/'results.json')
    keys = ('seed','drive','mutation','anchor','exchange')
    expected = set(product(range(96000,96005),(250,),(0,100),(100,200,300,400),(True,False)))
    index = {tuple(r[k] for k in keys): r for r in originals}
    require(len(originals)==80 and set(index)==expected, 'exact source grid')
    require({p.name for p in source.iterdir()} == {r['directory'] for r in originals} |
            {'metadata.json','results.json','summary.json','aggregation-verification.json'}, 'source inventory')
    pairs = read(target/'results.json')
    require(len(pairs)==40 and {tuple(p[k] for k in keys[:-1]) for p in pairs} ==
            {k[:-1] for k in expected}, 'exact pair grid')
    categories = ('both','on_only','off_only','neither')
    checked_components = 0
    for pair in pairs:
        sides = {}
        for flag, side in ((True,'on'),(False,'off')):
            original = index[tuple(pair[k] for k in keys[:-1])+(flag,)]
            directory = source/original['directory']
            require({p.name for p in directory.iterdir()} ==
                    {'metadata.json','audit.json','initial.json','steps.jsonl','final.json','continuity.json','summary.json'}, 'branch inventory')
            bindings = dict(directory=original['directory'])
            for name in ('metadata','audit','continuity'):
                bind(directory/f'{name}.json', original[f'{name}_sha256'])
                bindings[f'{name}_sha256'] = original[f'{name}_sha256']
            require(pair['bindings'][side]==bindings, 'pair branch binding')
            bm, audit = read(directory/'metadata.json'), read(directory/'audit.json')
            require(bm['status']=='complete' and bm['horizon']==100 and audit['ticks']==100, 'complete branch')
            require(audit == original['audit'], 'index audit record')
            payloads = {'initial.json','steps.jsonl','final.json','continuity.json','summary.json'}
            require(set(bm['output_sha256']) == set(audit['output_sha256']) == payloads, 'payload inventory')
            require(bm['output_sha256']==audit['output_sha256'], 'audited payload binding')
            for name, value in bm['output_sha256'].items():
                bind(directory/name, value)
            for name, value in bm['code_sha256'].items():
                bind(Path('src/bitgenesis/v4')/name, value)
            sides[side] = reconstruct(directory)
        require(len(sides['on'])==len(sides['off'])==len(pair['records'])==pair['initial_components'], 'all components')
        counts = {kind: dict.fromkeys(categories,0) for kind in ('continuous','survival')}
        eligible_n = 0
        for c, record in enumerate(pair['records']):
            on, off = sides['on'][c], sides['off'][c]
            require(record['on']==on and record['off']==off and record['component']==c, 'independent component reconstruction')
            for field in ('component','anchor_members','anchor_size','whole_world_anchor'):
                require(on[field]==off[field], 'common initial component')
            eligible = on['anchor_size']>=2 and not on['whole_world_anchor']
            require(record['eligible']==eligible, 'pre-intervention eligibility')
            eligible_n += eligible
            expected_categories = {}
            for kind, a, b in (('continuous',on['continuous'],off['continuous']),
                               ('survival',on['endpoint']['descendants']>0,off['endpoint']['descendants']>0)):
                category = categories[0 if a and b else 1 if a else 2 if b else 3]
                expected_categories[kind] = category
                counts[kind][category] += eligible
            require(record['categories']==expected_categories, 'all categories')
        require(pair['eligible_components']==eligible_n and pair['counts']==counts, 'pair denominator and integer cross tabs')
        fractions = {f'{kind}_{cat}': str(Fraction(counts[kind][cat],eligible_n)) if eligible_n else None
                     for kind in counts for cat in categories}
        require(pair['fractions']==fractions, 'pair rational fractions')
        checked_components += len(pair['records'])
    metrics = tuple(pairs[0]['fractions'])
    sources = []
    for seed, mutation in product(range(96000,96005),(0,100)):
        selected = [p for p in pairs if p['seed']==seed and p['mutation']==mutation]
        require(len(selected)==4, 'four anchors per source')
        sources.append(dict(seed=seed,drive=250,mutation=mutation,
                            metrics={k:mean([p['fractions'][k] for p in selected]) for k in metrics}))
    groups = [dict(drive=250,mutation=m,metrics={k:mean([s['metrics'][k]['mean'] for s in sources if s['mutation']==m])
                                               for k in metrics}) for m in (0,100)]
    require(read(target/'summary.json')==dict(source_means=sources,groups=groups), 'equal-weight source and condition means')
    for path, value in tracked.items():
        require(digest(path)==value, f'input changed during verification: {path}')
    report = dict(status='verified', verdict='APPROVED',pairs=40,branches=80,
                  components=checked_components,component_branch_records=checked_components*2,snapshots=8000,
                  method='Consecutive identity set differences; backward parent walks; every snapshot partition; exact rational aggregation',
                  binding_sha256=tracked,elapsed_seconds=time.monotonic()-start)
    with (target/'independent-verification.json').open('x') as handle:
        json.dump(report,handle,separators=(',',':'))
        handle.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k!='binding_sha256'}))


if __name__ == '__main__':
    main()
