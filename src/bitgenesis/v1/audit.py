"""Independent serialized V1 ledger/ancestry audit; does not import the engine.

Includes decision and spatial reconstruction; initialization and mutation RNG
are not independently replayed.
"""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
from .decision_audit import check_decision
from .spatial_audit import reconstruct


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(directory):
    root = Path(directory)
    def read(name):
        return json.loads((root / name).read_text(encoding='utf-8'))
    meta = read('metadata.json')
    require(meta['status'] == 'complete' and meta['schema'] == 'v1-run-1'
            and meta['rules'] == 'v1-world-1' and meta['controller'] == 'v1-linear-1', 'incomplete or unknown run')
    names = ('initial.json', 'steps.jsonl', 'events.jsonl', 'final.json', 'summary.json')
    hashes = {name: sha256((root / name).read_bytes()).hexdigest() for name in names}
    require(hashes == meta['output_sha256'], 'output hash mismatch')
    c = meta['config']
    initial, final, summary = read('initial.json'), read('final.json'), read('summary.json')
    require(initial['tick'] == 0 and final['tick'] == meta['steps'] == meta['completed_steps'], 'horizon mismatch')
    require(len(initial['food']) == len(final['food']) == c['width'] * c['height'], 'food dimensions')
    require(initial['food'] == [c['initial_food']] * len(initial['food']), 'initial food')
    require(all(type(f) is int and 0 <= f <= c['capacity'] for f in final['food']), 'final food bounds')
    initial_by_id = {o['id']: o for o in initial['lineage']}
    require(len(initial_by_id) == len(initial['lineage']) == c['founders'], 'founder count')
    events = defaultdict(list)
    last_tick = 0
    with (root / 'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event = json.loads(line)
            require(type(event['tick']) is int and last_tick <= event['tick'] <= meta['steps'], 'event order')
            last_tick = event['tick']
            events[event['tick']].append(event)
    alive, born, dead, offspring = {}, {}, {}, Counter()

    def birth(event):
        identifier = event['id']
        require(type(identifier) is int and identifier == len(born), 'birth ID sequence')
        require(event['birth_tick'] == event['tick'] and event['death_tick'] is None
                and event['offspring'] == 0 and type(event['energy']) is int and event['energy'] > 0, 'birth state')
        weights = event['genome']['weights']
        require(len(weights) == 35 and all(type(w) is int and -100 <= w <= 100 for w in weights), 'genome bounds')
        if event['parent'] is None:
            assignment = meta.get('founder_assignments')
            if assignment is not None:
                require(len(assignment) == c['founders'], 'assignment count')
                require(weights == assignment[identifier]['weights'], 'assigned genome mismatch')
                founder_mode = assignment[identifier]['mode']
            else:
                founder_mode = meta['mode']
            require(event['tick'] == 0 and event['founder'] == identifier and event['generation'] == 0
                    and event['energy'] == c['initial_energy'] and event['mode'] == founder_mode, 'founder state')
            snapshot = {k: v for k, v in event.items() if k not in ('event', 'tick')}
            require(snapshot == initial_by_id.get(identifier), 'founder snapshot mismatch')
        else:
            parent = event['parent']
            require(parent in alive and born[parent]['tick'] < event['tick'], 'invalid parent')
            require(event['founder'] == born[parent]['founder']
                    and event['generation'] == born[parent]['generation'] + 1
                    and event['mode'] == born[parent]['mode'], 'ancestry mismatch')
            previous = born[parent]['genome']['weights']
            changes = [abs(a-b) for a, b in zip(weights, previous) if a != b]
            require(len(changes) <= 1 and all(d <= 10 for d in changes), 'mutation support')
            require(c['mutation_per_thousand'] != 0 or not changes, 'disabled mutation changed genome')
            offspring[parent] += 1
        born[identifier] = event
        alive[identifier] = event['energy']

    for event in events.pop(0, []):
        require(event['event'] == 'birth', 'nonbirth initial event')
        birth(event)
    require(len(born) == c['founders'], 'missing founder events')
    total = sum(initial['food']) + sum(alive.values())
    actor_count = 0
    tick_count = 0
    with (root / 'steps.jsonl').open(encoding='utf-8') as stream:
        for tick_count, line in enumerate(stream, 1):
            row = json.loads(line)
            require(row['tick'] == tick_count and row['energy_before'] == total, 'tick energy continuity')
            actors = row['actors']
            require(len({r['id'] for r in actors}) == len(actors)
                    and {r['id'] for r in actors} == set(alive), 'actor set/newborn timing')
            actor_count += len(actors)
            tick_events = events.pop(tick_count, [])
            expected_events = []
            spent = 0
            for r in actors:
                identifier = r['id']
                require(r['tick'] == tick_count and r['energy_before'] == alive[identifier], 'actor continuity')
                check_decision(r, born[identifier]['genome']['weights'], born[identifier]['mode'])
                energy = alive[identifier]
                phase_of_death = None
                for phase, cost in (('basal', c['basal_cost']), ('decision', c['decision_cost']),
                                    ('movement', c['movement_cost'] if r['action'] else 0)):
                    payment = min(energy, cost) if phase_of_death is None else 0
                    require(type(r[phase]) is int and r[phase] == payment, 'phase payment')
                    energy -= payment
                    if energy == 0 and phase_of_death is None:
                        phase_of_death = phase
                for key in ('intake', 'birth_cost', 'child_energy', 'energy_after'):
                    require(type(r[key]) is int and r[key] >= 0, 'negative/noninteger energy')
                if phase_of_death:
                    require(r['intake'] == r['birth_cost'] == r['child_energy'] == r['energy_after'] == 0, 'dead actor acted')
                    if phase_of_death != 'movement':
                        require(r['action'] is None, 'decision after death')
                    expected_events.append(('death', identifier, phase_of_death))
                    dead[identifier] = tick_count
                    del alive[identifier]
                else:
                    require(type(r['action']) is int and 0 <= r['action'] <= 4, 'action bounds')
                    require(0 <= r['intake'] <= c['feeding_limit'], 'intake bounds')
                    energy += r['intake']
                    if r['child_energy']:
                        require(energy >= c['birth_threshold'] and r['birth_cost'] == c['birth_cost'], 'birth eligibility')
                        energy -= r['birth_cost']
                        require(r['child_energy'] == energy // 2, 'birth transfer')
                        energy -= r['child_energy']
                        expected_events.append(('birth', identifier, r['child_energy']))
                    else:
                        require(r['birth_cost'] == 0, 'birth payment without child')
                    require(r['energy_after'] == energy, 'actor energy mismatch')
                    alive[identifier] = energy
                spent += sum(r[k] for k in ('basal', 'decision', 'movement', 'birth_cost'))
            require(len(expected_events) == len(tick_events), 'event count mismatch')
            for expected, event in zip(expected_events, tick_events):
                require(event['event'] == expected[0], 'event action order')
                if expected[0] == 'birth':
                    require(event['parent'] == expected[1] and event['energy'] == expected[2], 'birth ledger mismatch')
                    birth(event)
                else:
                    require(event['id'] == expected[1] and event['phase'] == expected[2], 'death mismatch')
            require(type(row['resource_added']) is int and 0 <= row['resource_added'] <= len(initial['food']) * c['renewal_amount'], 'resource addition bounds')
            total += row['resource_added'] - spent
            require(row['spent'] == spent and row['energy_after'] == total and row['population'] == len(alive), 'world ledger mismatch')
    require(tick_count == meta['steps'] and not events, 'missing ticks/events')
    require(len(final['lineage']) == len(born), 'final lineage length')
    positions = set()
    for identifier, organism in enumerate(final['lineage']):
        require(organism['id'] == identifier, 'final ID order')
        event = born[identifier]
        for key in ('parent', 'founder', 'generation', 'birth_tick', 'genome', 'mode'):
            require(organism[key] == event[key], 'final inherited state')
        require(organism['offspring'] == offspring[identifier] and organism['death_tick'] == dead.get(identifier), 'final life history')
        require(organism['energy'] == alive.get(identifier, 0), 'final individual energy')
        require(type(organism['x']) is int and type(organism['y']) is int
                and 0 <= organism['x'] < c['width'] and 0 <= organism['y'] < c['height'], 'final position bounds')
        if identifier in alive:
            position = (organism['x'], organism['y'])
            require(position not in positions, 'duplicate occupied site')
            positions.add(position)
    require(total == sum(final['food']) + sum(alive.values()), 'final world energy')
    require(summary == {'steps': tick_count, 'population': len(alive), 'individuals': len(born),
                        'actor_records': actor_count, 'births': len(born) - c['founders'],
                        'deaths': len(dead), 'total_energy': total}, 'summary mismatch')
    spatial = reconstruct(root)
    return {'scope': 'energy, ancestry, decisions and spatial reconstruction; five RNG streams checked from recorded initial states; initialization and mutation RNG not replayed',
            **spatial,
            'steps': tick_count, 'actor_records': actor_count, 'individuals': len(born),
            'population': len(alive), 'input_sha256': hashes,
            'metadata_sha256': sha256((root / 'metadata.json').read_bytes()).hexdigest(),
            'audit_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
            'decision_audit_sha256': sha256(Path(__file__).with_name('decision_audit.py').read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.directory)
    text = json.dumps(result, indent=2) + '\n'
    if args.output:
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(text)
    print(text)
