"""Independent group/total accounts; full event and lineage reconstruction is separate."""
from collections import Counter
from copy import deepcopy
import csv
if __package__:
    from .verify_v0_monomorphic_metrics import initial_gate as base_initial, metric_gate as base_metrics, INITIAL, read_metrics
else:
    from verify_v0_monomorphic_metrics import initial_gate as base_initial, metric_gate as base_metrics, INITIAL, read_metrics

GROUPS = ('sampled', 'ancestor')
FIELDS = ('population', 'births', 'deaths', 'organism_energy', 'founder_lineages', 'max_generation', 'mean_genome')


def read_groups(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return [{k: None if v == '' else float(v) if k.endswith('_mean_genome') else int(v)
                 for k, v in r.items()} for r in csv.DictReader(stream)]


def initial_gate(initial, result):
    traits = {g: result[g+'_trait'] for g in GROUPS}
    swap = result['swap']
    if type(swap) is not int or swap not in (0, 1) or any(type(t) is not int or not 0 <= t <= 1000 for t in traits.values()):
        raise ValueError('Invalid trait or allocation')
    expected_groups = {str(i): ('sampled' if (i < 40) != bool(swap) else 'ancestor') for i in range(80)}
    if initial['founder_groups'] != expected_groups:
        raise ValueError('Initial group allocation differs')
    if len(initial['founders']) != 80 or {o['id'] for o in initial['founders']} != set(range(80)):
        raise ValueError('Founder IDs differ')
    if any(type(o['genome']) is not int or o['genome'] != traits[expected_groups[str(o['id'])]] for o in initial['founders']):
        raise ValueError('Founder genotype differs from allocation')
    expected = dict(INITIAL, mean_genome=sum(traits.values())/2, genome_variants=len(set(traits.values())))
    if initial['snapshot'] != expected:
        raise ValueError('Initial snapshot differs')
    for k in ('swap', 'sampled_trait', 'ancestor_trait'):
        if initial[k] != result[k]:
            raise ValueError('Initial treatment identity differs')
    normalized = deepcopy(initial)
    for o in normalized['founders']:
        o['genome'] = 250
    base_initial(normalized, result['seed'], 0)
    return traits


def verify_records(initial, rows, groups, result, steps=10000):
    traits = initial_gate(initial, result)
    if len(rows) != steps+1 or len(groups) != steps+1:
        raise ValueError('Incomplete metric horizon')
    schema = {'tick'} | {f'{g}_{f}' for g in GROUPS for f in FIELDS}
    extinct = {g: None for g in GROUPS}
    normalized = []; previous = None
    for tick, (world, flat) in enumerate(zip(rows, groups, strict=True)):
        if set(flat) != schema or flat['tick'] != tick or world['tick'] != tick:
            raise ValueError('Group schema or tick order differs')
        current = {g: {f: flat[f'{g}_{f}'] for f in FIELDS} for g in GROUPS}
        hist = Counter()
        for g, r in current.items():
            n = r['population']
            if any(type(r[f]) is not int or r[f] < 0 for f in FIELDS if f not in ('mean_genome', 'max_generation')):
                raise ValueError('Invalid integer group metric')
            if n != 40+r['births']-r['deaths'] or n > 1024:
                raise ValueError('Group population account differs')
            if not int(n > 0) <= r['founder_lineages'] <= min(n, 40) or r['organism_energy'] < n:
                raise ValueError('Group energy or founder bounds differ')
            if r['mean_genome'] != (traits[g] if n else None):
                raise ValueError('Fixed group genotype differs')
            if n:
                if type(r['max_generation']) is not int or not 0 <= r['max_generation'] <= tick:
                    raise ValueError('Group generation differs')
                hist[str(traits[g])] += n
            elif r['max_generation'] is not None or r['organism_energy']:
                raise ValueError('Invalid empty group')
            if n == 0 and extinct[g] is None:
                extinct[g] = tick
            if tick == 0:
                if r != dict(population=40, births=0, deaths=0, organism_energy=960, founder_lineages=40, max_generation=0, mean_genome=traits[g]):
                    raise ValueError('Initial group metrics differ')
            else:
                p = previous[g]
                uptake = r['organism_energy']-p['organism_energy']+p['population']
                if not 0 <= r['births']-p['births'] <= p['population'] or not 0 <= r['deaths']-p['deaths'] <= p['population'] or not 0 <= uptake <= 8*p['population']:
                    raise ValueError('Per-group births, deaths or energy transfer differs')
                if r['founder_lineages'] > p['founder_lineages']:
                    raise ValueError('Lost founder lineage reappeared')
        for f in ('population', 'births', 'deaths', 'organism_energy', 'founder_lineages'):
            if sum(r[f] for r in current.values()) != world[f]:
                raise ValueError('Group/world sum differs')
        n = world['population']
        if world['mean_genome'] != (sum(traits[g]*current[g]['population'] for g in GROUPS)/n if n else None) or world['genome_variants'] != len(hist) or world['ever_genome_values'] != len(set(traits.values())) or world['changed_births'] != 0:
            raise ValueError('World fixed-trait mixture differs')
        if world['max_generation'] != max((r['max_generation'] for r in current.values() if r['population']), default=None):
            raise ValueError('World/group generation differs')
        if str(tick) in result['observations']:
            obs = result['observations'][str(tick)]
            if any(obs[k] != v for k, v in world.items()) or obs['living_genome_histogram'] != dict(hist):
                raise ValueError('Checkpoint world metrics differ')
            ever = Counter()
            for g in GROUPS:
                ever[str(traits[g])] += 40+current[g]['births']
                expected = dict(**current[g], living_genome_histogram={str(traits[g]): current[g]['population']} if current[g]['population'] else {})
                if obs['groups'][g] != expected:
                    raise ValueError('Checkpoint group metrics differ')
            if obs['ever_born_genome_histogram'] != dict(ever):
                raise ValueError('Checkpoint birth histogram differs')
        normalized.append(dict(world, mean_genome=250 if n else None, genome_variants=int(n > 0), ever_genome_values=1))
        previous = current
    extinction = base_metrics(normalized, 0, steps)
    if set(result['observations']) != {str(t) for t in (0, 100, 500, 1000, 5000, 10000) if t <= steps}:
        raise ValueError('Checkpoint grid differs')
    if result['group_extinction_ticks'] != extinct or result['extinction_tick'] != extinction or result['right_censored'] != (extinction is None):
        raise ValueError('Extinction summary differs')
    if any(result[k] != v for k, v in rows[-1].items()):
        raise ValueError('Terminal world summary differs')
    for g in GROUPS:
        expected = dict(**previous[g], living_genome_histogram={str(traits[g]): previous[g]['population']} if previous[g]['population'] else {})
        if result['groups'][g] != expected:
            raise ValueError('Terminal group summary differs')
    return dict(metric_rows=len(rows), group_rows=len(groups), extinction_tick=extinction, group_extinction_ticks=extinct)
