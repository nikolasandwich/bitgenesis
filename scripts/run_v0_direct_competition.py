"""Campaign024 recording helpers; groups are observations of founder ancestry."""
from collections import Counter
import argparse
from contextlib import ExitStack
import csv
import hashlib
import json
from pathlib import Path

from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.runner import load_config, provenance
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


def check_neutral_pair(first, second):
    for name in ('metrics.csv', 'events.jsonl', 'lineage.json'):
        if (first/name).read_bytes() != (second/name).read_bytes():
            raise ValueError('Identical-trait physical records differ')
    results = [json.loads((p/'result.json').read_text(encoding='utf-8')) for p in (first, second)]
    if results[0]['final_state_sha256'] != results[1]['final_state_sha256']:
        raise ValueError('Identical-trait final states differ')
    with (first/'groups.csv').open(newline='', encoding='utf-8') as a, (second/'groups.csv').open(newline='', encoding='utf-8') as b:
        for left, right in zip(csv.DictReader(a), csv.DictReader(b), strict=True):
            expected = {'tick': left['tick']}
            for key, value in left.items():
                for group, other in (('sampled', 'ancestor'), ('ancestor', 'sampled')):
                    if key.startswith(group+'_'):
                        expected[other+key[len(group):]] = value
            if right != expected:
                raise ValueError('Neutral group records are not complementary')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    mp = root/'docs/research/results/campaign-023-samples.json'
    vp = root/'docs/research/results/campaign-023-sample-verification.json'
    if sha(mp) != '58fe9c9c7484da17db5d095fbeb93289903ffe5b801b7d3709a297f52a19c741' or sha(vp) != '9aee4ba43d99b541da878fa26231cc78e484f2dcb51e103d45ea7705a63c0a68':
        raise ValueError('Preregistered sampling evidence changed')
    manifest = json.loads(mp.read_text(encoding='utf-8'))
    verified = json.loads(vp.read_text(encoding='utf-8'))
    if verified['manifest_sha256'] != sha(mp):
        raise ValueError('Sample gate linkage differs')
    if len(manifest['samples']) != 20 or {s['source_seed'] for s in manifest['samples']} != set(range(1900, 1920)):
        raise ValueError('Source grid differs')
    available = sum(s['available'] for s in manifest['samples'])
    if available != manifest['available_sources'] or available != verified['available_sources']:
        raise ValueError('Available source count differs')
    metadata = dict(protocol='campaign-024-direct-competition-1', rules_version='v0-darwin-1',
        manifest_sha256=sha(mp), sample_verification_sha256=sha(vp),
        protocol_sha256=sha(root/'experiments/v0/campaign-024.md'),
        available_sources=available, planned_runs=available*10, steps=10000,
        replicates=list(range(5)), swaps=[0, 1], status='running', completed_runs=0,
        **provenance())
    if metadata['git_dirty'] is not False:
        raise ValueError('Commit clean source before outcome execution')
    base = load_config(root/'experiments/v0/darwin-baseline.toml')
    args.output.mkdir(parents=True, exist_ok=False)
    write_json_atomic(args.output/'metadata.json', metadata)
    write_json_atomic(args.output/'samples.json', manifest)
    results = []
    try:
        for sample in manifest['samples']:
            if not sample['available']:
                continue
            source = sample['source_seed']; selected = sample['selected']
            for replicate in range(5):
                seed = 2100 + 5*(source-1900) + replicate
                folders = []
                for swap in (0, 1):
                    folder = args.output/f'source-{source}-replicate-{replicate}-swap-{swap}'
                    identity = dict(source_seed=source, replicate=replicate, swap=swap,
                        sampled_trait=selected['genome'], ancestor_trait=selected['founder_genome'],
                        sampled_individual_id=selected['id'], source_founder_id=selected['founder_id'])
                    world, groups = initialize(base, seed, selected['genome'], selected['founder_genome'], swap)
                    result = evaluate(world, groups, folder, 10000, identity)
                    results.append(result); folders.append(folder)
                    write_json_atomic(args.output/'results.json', results)
                    metadata['completed_runs'] = len(results)
                    write_json_atomic(args.output/'metadata.json', metadata)
                    print(f"{folder.name}: sampled={result['groups']['sampled']['population']}, ancestor={result['groups']['ancestor']['population']}", flush=True)
                if selected['genome'] == selected['founder_genome']:
                    check_neutral_pair(*folders)
        compact = []
        for result in results:
            row = {k: v for k, v in result.items() if k not in ('observations', 'groups', 'group_extinction_ticks')}
            for group in GROUPS:
                row.update({f'{group}_{k}': v for k, v in result['groups'][group].items() if k != 'living_genome_histogram'})
                row[f'{group}_extinction_tick'] = result['group_extinction_ticks'][group]
            compact.append(row)
        if compact:
            with (args.output/'results.csv').open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(compact[0]))
                writer.writeheader(); writer.writerows(compact)
        metadata['status'] = 'complete'
    except (Exception, KeyboardInterrupt) as error:
        metadata['status'] = 'interrupted' if isinstance(error, KeyboardInterrupt) else 'failed'
        metadata['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        write_json_atomic(args.output/'metadata.json', metadata)


if __name__ == '__main__':
    main()
