"""Campaign024 recording helpers; groups are observations of founder ancestry."""
from collections import Counter
from contextlib import ExitStack
import csv
import hashlib
import json

from bitgenesis.v0.artifacts import write_json_atomic
from scripts.run_v0_monomorphic_mutation import initialize as base_initialize
from scripts.run_v0_monomorphic_mutation import record_world, CHECKPOINTS, histogram

GROUPS = ('sampled', 'ancestor')


def initialize(base, seed, sampled_trait, ancestor_trait, swap):
    if type(swap) is not int or swap not in (0, 1):
        raise ValueError('Invalid allocation swap')
    if any(type(t) is not int or not 0 <= t <= 1000 for t in (sampled_trait, ancestor_trait)):
        raise ValueError('Invalid assigned trait')
    world = base_initialize(base, seed, 0)
    if set(world.living) != set(range(80)):
        raise ValueError('Expected eighty founders')
    groups = {i: 'sampled' if (i < 40) != bool(swap) else 'ancestor' for i in range(80)}
    traits = dict(sampled=sampled_trait, ancestor=ancestor_trait)
    for i, organism in world.living.items():
        organism.genome = traits[groups[i]]
    for event in world.events:
        event['genome'] = traits[groups[event['id']]]
    world.check_invariants()
    return world, groups


def evaluate(world, founder_groups, output, steps, identity, after_record=None):
    if set(founder_groups) != set(range(80)) or Counter(founder_groups.values()) != Counter(sampled=40, ancestor=40):
        raise ValueError('Invalid founder group map')
    initial_snapshot = world.snapshot()
    births = Counter(); deaths = Counter()
    extinct = {g: None for g in GROUPS}
    observations = {}; final_groups = {}; writer = None
    with ExitStack() as stack:
        def observe(current):
            nonlocal writer, final_groups
            for event in current.events:
                organism = current.lineage[event['id']]
                group = founder_groups[organism.founder_id]
                if event['event'] == 'birth' and organism.parent_id is not None:
                    births[group] += 1
                elif event['event'] == 'death':
                    deaths[group] += 1
            populations = {g: [] for g in GROUPS}
            for organism in current.living.values():
                populations[founder_groups[organism.founder_id]].append(organism)
            final_groups = {}
            flat = {'tick': current.tick}
            for group, organisms in populations.items():
                n = len(organisms)
                if n == 0 and extinct[group] is None:
                    extinct[group] = current.tick
                if n != 40 + births[group] - deaths[group]:
                    raise ValueError('Group population account differs')
                row = dict(population=n, births=births[group], deaths=deaths[group],
                    organism_energy=sum(o.energy for o in organisms),
                    founder_lineages=len({o.founder_id for o in organisms}),
                    max_generation=max((o.generation for o in organisms), default=None),
                    mean_genome=sum(o.genome for o in organisms)/n if n else None)
                flat.update({f'{group}_{k}': v for k, v in row.items()})
                final_groups[group] = dict(**row, living_genome_histogram=histogram(o.genome for o in organisms))
            snapshot = current.snapshot()
            for field in ('population', 'births', 'deaths', 'organism_energy', 'founder_lineages'):
                if sum(r[field] for r in final_groups.values()) != snapshot[field]:
                    raise ValueError('Group sum differs from world')
            if writer is None:
                stream = stack.enter_context((output/'groups.csv').open('w', encoding='utf-8', newline=''))
                writer = csv.DictWriter(stream, fieldnames=list(flat))
                writer.writeheader()
            writer.writerow(flat)
            if current.tick in CHECKPOINTS:
                observations[str(current.tick)] = final_groups
            if after_record:
                after_record(current)
        result = record_world(world, output, steps, observe)
    initial = json.loads((output/'initial.json').read_text(encoding='utf-8'))
    initial.update(snapshot=initial_snapshot, founder_groups=founder_groups, **identity)
    write_json_atomic(output/'initial.json', initial)
    for tick in result['observations']:
        result['observations'][tick]['groups'] = observations[tick]
    final_state = dict(food=world.food, occupied=world.occupied,
                       rng=world.rng.getstate(), snapshot=world.snapshot())
    result.update(identity, groups=final_groups, group_extinction_ticks=extinct,
                  final_state_sha256=hashlib.sha256(json.dumps(final_state, sort_keys=True).encode()).hexdigest())
    write_json_atomic(output/'result.json', result)
    return result
