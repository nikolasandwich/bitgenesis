"""Bounded persisted V3 runs, retaining failed developmental attempts."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
import sys

from bitgenesis.v1.controller import CONTROLLER_VERSION
from .resources import RESOURCE_RULES
from .world import Config, World, RULES_VERSION


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'


def save(path, value):
    path.write_text(encoded(value), encoding='utf-8')


def state(world):
    return {'tick': world.tick, 'food': world.food, 'substrate_b': world.substrate_b,
            'lineage': [asdict(o) for o in world.lineage.values()],
            'attempts': world.attempts, 'initialization_spent':world.initialization_spent,
            'rng': {name: rng.getstate() for name, rng in world.rng.items()}}


def run(output, config, seed, steps, mode='intact', max_actor_records=1000000,
        founder_genomes=None):
    output = Path(output)
    if type(steps) is not int or not 0 <= steps <= 100000:
        raise ValueError('steps must be in 0..100000')
    if type(max_actor_records) is not int or max_actor_records < 0:
        raise ValueError('record budget must be a nonnegative integer')
    # Bound retained ancestry and output before allocating a world. This upper
    # bound deliberately counts every site at every tick, even after extinction.
    if config.width * config.height * steps > max_actor_records:
        raise ValueError('worst-case actor count exceeds recording budget')
    world = World(config, seed, mode, founder_genomes)
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).parent
    hashes = {p.name: sha256(p.read_bytes()).hexdigest() for p in sorted(source.glob('*.py'))}
    for dependency in ('v1/controller.py', 'v2/development.py'):
        hashes['../' + dependency] = sha256((source.parent / dependency).read_bytes()).hexdigest()
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source,
                                          stderr=subprocess.DEVNULL, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=source,
                                             stderr=subprocess.DEVNULL, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = None, None
    metadata = {'schema': 'v3-run-1', 'encoding':'ecological', 'rules': RULES_VERSION, 'resource_rules': RESOURCE_RULES,
                'controller': CONTROLLER_VERSION, 'config': asdict(config), 'seed': seed,
                'steps': steps, 'mode': mode, 'python': platform.python_version(),
                'implementation': platform.python_implementation(), 'source_sha256': hashes,
                'git_commit': revision, 'git_dirty': dirty, 'status': 'running',
                'max_actor_records': max_actor_records, 'completed_steps': 0}
    if founder_genomes is not None:
        metadata['founder_genomes'] = [asdict(g) for g in founder_genomes]
    save(output / 'metadata.json', metadata)
    count = 0
    flows = dict(external_a=0, consumed_a=0, consumed_b=0, released_b=0,
                 feeding_energy=0, feeding_dissipation=0)
    try:
        save(output / 'initial.json', state(world))
        with (output / 'steps.jsonl').open('w', encoding='utf-8', newline='\n') as records, \
             (output / 'events.jsonl').open('w', encoding='utf-8', newline='\n') as events:
            for event in world.events:
                events.write(encoded(event))
            world.events.clear()
            for _ in range(steps):
                record = world.step()
                records.write(encoded(record))
                count += len(record['actors'])
                flows['external_a'] += record['resource_added']
                for actor in record['actors']:
                    feeding = actor['feeding']
                    if feeding is not None:
                        for key in ('consumed_a', 'consumed_b', 'released_b'):
                            flows[key] += feeding[key]
                        flows['feeding_energy'] += feeding['energy_gain']
                        flows['feeding_dissipation'] += feeding['dissipated']
                for event in world.events:
                    events.write(encoded(event))
                world.events.clear()
                metadata['completed_steps'] = world.tick
        save(output / 'final.json', state(world))
        summary = {'steps': world.tick, 'population': len(world.organisms),
                   'individuals': len(world.lineage), 'actor_records': count,
                   'births': sum(o.parent is not None for o in world.lineage.values()),
                   'founder_attempts':config.founders,
                   'successful_founders':sum(o.parent is None for o in world.lineage.values()),
                   'attempts':len(world.attempts),
                   'failed_attempts':sum(not a['valid'] for a in world.attempts),
                   'construction_cost':sum(a['construction_cost'] for a in world.attempts),
                   'failure_loss':sum(a['failure_loss'] for a in world.attempts),
                   'deaths': len(world.lineage) - len(world.organisms),
                   'total_energy': world.total_energy(), 'resource_flows': flows,
                   'remaining_a': sum(world.food), 'remaining_b': sum(world.substrate_b)}
        save(output / 'summary.json', summary)
        metadata['status'] = 'complete'
        metadata['output_sha256'] = {name: sha256((output / name).read_bytes()).hexdigest()
            for name in ('initial.json', 'steps.jsonl', 'events.jsonl', 'final.json', 'summary.json')}
        save(output / 'metadata.json', metadata)
        return summary
    except BaseException as error:
        metadata.update(status='failed', error=f'{type(error).__name__}: {error}')
        save(output / 'metadata.json', metadata)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description='Experimental BitGenesis V3 runner')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, help='JSON object containing Config fields')
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--steps', type=int, default=100)
    parser.add_argument('--mode', choices=('intact', 'blind', 'shuffled'), default='intact')
    parser.add_argument('--max-actor-records', type=int, default=1000000)
    args = parser.parse_args(argv)
    try:
        config = Config(**json.loads(args.config.read_text(encoding='utf-8'))) if args.config else Config()
        print(encoded(run(args.output, config, args.seed, args.steps, args.mode, args.max_actor_records)), end='')
    except (OSError, ValueError, TypeError) as error:
        parser.error(str(error))
    return 0
