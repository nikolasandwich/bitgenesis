"""Independent V2 spatial reconstruction, including failed development attempts."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
from random import Random


def tuples(value):
    return tuple(tuples(v) for v in value) if isinstance(value, list) else value


def reconstruct(directory):
    root = Path(directory)
    def read(name):
        return json.loads((root / name).read_text(encoding='utf-8'))
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    meta, initial, final = read('metadata.json'), read('initial.json'), read('final.json')
    c = meta['config']
    width, height = c['width'], c['height']
    streams = {}
    for name in ('resources', 'order', 'ties', 'sensors', 'birth'):
        streams[name] = Random()
        streams[name].setstate(tuples(initial['rng'][name]))
    food = list(initial['food'])
    positions = {o['id']: (o['x'], o['y']) for o in initial['lineage']}
    endpoints = dict(positions)
    occupied = {p: i for i, p in positions.items()}
    require(len(occupied) == len(positions), 'initial overlap')
    events = defaultdict(list)
    with (root / 'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event = json.loads(line)
            if event['tick']:
                events[event['tick']].append(event)
    def adjacent(p):
        x, y = p
        return [((x+1)%width,y), ((x-1)%width,y), (x,(y+1)%height), (x,(y-1)%height)]
    decisions = 0
    with (root / 'steps.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            added = 0
            for site in range(len(food)):
                if streams['resources'].randrange(1000) < c['renewal_per_thousand']:
                    delta = min(c['renewal_amount'], c['capacity'] - food[site])
                    food[site] += delta
                    added += delta
            require(row['resource_added'] == added, 'resource reconstruction')
            order = list(positions)
            streams['order'].shuffle(order)
            require([r['id'] for r in row['actors']] == order, 'actor shuffle reconstruction')
            tick_events = iter(events.pop(row['tick'], []))
            for r in row['actors']:
                identifier = r['id']
                position = positions[identifier]
                energy = r['energy_before'] - r['basal'] - r['decision']
                if energy > 0:
                    decisions += 1
                    local = [food[y*width+x] for x,y in [position] + adjacent(position)]
                    scaled = [1000 * f // c['capacity'] if c['capacity'] else 0 for f in local]
                    require(r['inputs'][:5] == scaled, 'local food inputs')
                    require(r['permutation'] == streams['sensors'].randrange(24), 'sensor RNG')
                    require(r['tie_ticket'] == streams['ties'].randrange(60), 'tie RNG')
                    target = adjacent(position)[r['action']-1] if r['action'] else position
                    blocked = bool(r['action'] and target in occupied)
                    require(type(r['blocked']) is bool and r['blocked'] == blocked, 'blocked action')
                    energy -= r['movement']
                    if energy > 0:
                        if r['action'] and not blocked:
                            del occupied[position]
                            position = target
                            positions[identifier] = position
                            occupied[position] = identifier
                        x,y = position
                        intake = min(c['feeding_limit'], food[y*width+x])
                        require(r['intake'] == intake, 'spatial intake')
                        food[y*width+x] -= intake
                        energy += intake
                        free = [p for p in adjacent(position) if p not in occupied]
                        expected_birth = energy >= c['birth_threshold'] and bool(free)
                        require(('development_attempt' in r) == expected_birth, 'spatial attempt eligibility')
                        if expected_birth:
                            child_position = streams['birth'].choice(free)
                            attempt = next(tick_events, None)
                            require(attempt is not None and attempt['event'] == 'development'
                                    and attempt['id'] == r['development_attempt']
                                    and attempt['parent'] == identifier
                                    and (attempt['x'],attempt['y']) == child_position, 'attempt position')
                            if attempt['valid']:
                                event = next(tick_events, None)
                                require(event is not None and event['event'] == 'birth'
                                        and event['id'] == attempt['id']
                                        and (event['x'],event['y']) == child_position, 'viable child position')
                                positions[event['id']] = child_position
                                endpoints[event['id']] = child_position
                                occupied[child_position] = event['id']
                else:
                    require(r['blocked'] is False, 'blocked flag before decision')
                endpoints[identifier] = position
                if energy <= 0:
                    event = next(tick_events, None)
                    require(event is not None and event['event'] == 'death' and event['id'] == identifier, 'spatial death')
                    del occupied[position]
                    del positions[identifier]
            require(next(tick_events, None) is None, 'extra spatial event')
    require(not events, 'remaining events')
    require(food == final['food'], 'final food reconstruction')
    require(endpoints == {o['id']: (o['x'],o['y']) for o in final['lineage']}, 'final position reconstruction')
    for name, rng in streams.items():
        require(rng.getstate() == tuples(final['rng'][name]), f'final {name} RNG')
    return {'decisions': decisions, 'spatial_reconstruction': True,
            'rng_streams_checked': list(streams),
            'spatial_audit_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
