"""Campaign 022: mutation treatment from monomorphic founders, unchanged V0."""
import argparse
from collections import Counter
import csv
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config, provenance
from bitgenesis.v0.artifacts import write_json_atomic
from scripts.run_v0_food_geometry import food_map

CHECKPOINTS = (0, 100, 500, 1000, 5000, 10000)


def initialize(base, seed, mutation):
    if type(mutation) is not int or mutation not in (0, 100):
        raise ValueError('Undeclared mutation treatment')
    config = replace(base, seed=seed, initial_food=0, mutation_probability=mutation,
                     regrowth_probability=15, regrowth_amount=4, food_capacity=24,
                     birth_threshold=40, birth_cost=0, movement_cost=0, mutation_step=100)
    world = World(config)
    for organism in world.living.values():
        organism.genome = 250
    for event in world.events:
        event['genome'] = 250
    world.food[:] = food_map('block', seed)
    if sum(world.food) != 5120:
        raise ValueError('Initial food differs')
    world.supplied_energy += 5120
    world.check_invariants()
    return world


def histogram(values):
    return {str(k): v for k, v in sorted(Counter(values).items())}


def record_world(world, output, steps, after_record=None):
    """Record one world; short horizons are for engineering checks only."""
    output.mkdir(parents=True, exist_ok=False)
    write_json_atomic(output/'initial.json', dict(config=asdict(world.config),
        founders=[asdict(o) for o in world.living.values()], food=world.food[:],
        rng_state=world.rng.getstate(), supplied_energy=world.supplied_energy))
    ever = Counter(); changed = 0; extinction = None; observations = {}
    with (output/'metrics.csv').open('w', newline='', encoding='utf-8') as mf, (output/'events.jsonl').open('w', encoding='utf-8') as ef:
        writer = csv.DictWriter(mf, fieldnames=[*world.snapshot(), 'ever_genome_values', 'changed_births'])
        writer.writeheader()
        for tick in range(steps+1):
            if tick:
                world.step()
            world.check_invariants()
            for event in world.events:
                if event['event'] == 'birth':
                    ever[event['genome']] += 1
                    parent = event['parent_id']
                    changed += int(parent is not None and event['genome'] != world.lineage[parent].genome)
                if event['event'] in ('birth', 'death'):
                    saved = dict(event)
                    if event['event'] == 'birth':
                        saved['birth_tick'] = event['tick']
                    ef.write(json.dumps(saved, separators=(',', ':'))+'\n')
            row = dict(**world.snapshot(), ever_genome_values=len(ever), changed_births=changed)
            writer.writerow(row)
            if row['population'] == 0 and extinction is None:
                extinction = tick
            if tick in CHECKPOINTS:
                observations[str(tick)] = dict(**row,
                    living_genome_histogram=histogram(o.genome for o in world.living.values()),
                    ever_born_genome_histogram={str(k): v for k, v in sorted(ever.items())})
            if after_record is not None:
                after_record(world)
            world.events.clear()
    write_json_atomic(output/'lineage.json', [asdict(o) for o in world.lineage.values()])
    result = dict(seed=world.config.seed, mutation_probability=world.config.mutation_probability,
                  **row, extinction_tick=extinction, right_censored=extinction is None,
                  observations=observations)
    write_json_atomic(output/'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    base = load_config(root/'experiments/v0/darwin-baseline.toml')
    metadata = dict(protocol='campaign-022-monomorphic-mutation-1', rules_version='v0-darwin-1',
        seeds=list(range(1900, 1920)), mutation_probabilities=[0, 100], steps=10000,
        checkpoints=list(CHECKPOINTS), baseline_config=asdict(base),
        protocol_sha256=hashlib.sha256((root/'experiments/v0/campaign-022.md').read_bytes()).hexdigest(),
        status='running', completed_runs=0, **provenance())
    if metadata['git_dirty'] is not False:
        raise ValueError('Commit source before outcome execution')
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    write_json_atomic(args.output/'metadata.json', metadata)
    try:
        for seed in metadata['seeds']:
            for mutation in metadata['mutation_probabilities']:
                name = f'mutation-{mutation}-seed-{seed}'
                result = record_world(initialize(base, seed, mutation), args.output/name, 10000)
                results.append(result)
                write_json_atomic(args.output/'results.json', results)
                metadata['completed_runs'] = len(results)
                write_json_atomic(args.output/'metadata.json', metadata)
                print(f"{name}: population={result['population']}, extinction={result['extinction_tick']}", flush=True)
        compact = [{k: v for k, v in r.items() if k != 'observations'} for r in results]
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
