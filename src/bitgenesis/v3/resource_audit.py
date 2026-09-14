"""Independent substrate replay at recorded feeding sites; not a spatial audit."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from random import Random


def tuples(value):
    return tuple(tuples(v) for v in value) if isinstance(value, list) else value


def audit(directory):
    root = Path(directory)
    def read(name):
        return json.loads((root / name).read_text(encoding='utf-8'))
    def require(ok, message):
        if not ok:
            raise ValueError(message)
    meta, initial, final, summary = map(read, ('metadata.json', 'initial.json', 'final.json', 'summary.json'))
    require(meta['status'] == 'complete' and meta['schema'] == 'v3-run-1'
            and meta['rules'] == 'v3-world-1' and meta['resource_rules'] == 'v3-resources-1', 'unsupported run')
    names = ('initial.json', 'steps.jsonl', 'events.jsonl', 'final.json', 'summary.json')
    hashes = {name: sha256((root / name).read_bytes()).hexdigest() for name in names}
    require(meta['output_sha256'] == hashes, 'output hash mismatch')
    c = meta['config']
    a, b = list(initial['food']), list(initial['substrate_b'])
    require(a == [c['initial_food']] * (c['width'] * c['height'])
            and b == [c['initial_b']] * len(a), 'initial stocks mismatch')
    rng = Random()
    rng.setstate(tuples(initial['rng']['resources']))
    lineage = {o['id']: o for o in final['lineage']}
    energy = sum(a) + sum(b) + sum(o['energy'] for o in initial['lineage'])
    flows = dict(external_a=0, consumed_a=0, consumed_b=0, released_b=0,
                 feeding_energy=0, feeding_dissipation=0)
    ticks = actors = feedings = 0
    with (root / 'steps.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            ticks += 1
            require(row['tick'] == ticks and row['energy_before'] == energy, 'tick/energy discontinuity')
            added = 0
            for site in range(len(a)):
                if rng.randrange(1000) < c['renewal_per_thousand']:
                    increment = min(c['renewal_amount'], c['capacity'] - a[site])
                    a[site] += increment
                    added += increment
            require(added == row['resource_added'], 'renewal mismatch')
            flows['external_a'] += added
            spent = 0
            for actor in row['actors']:
                actors += 1
                f = actor['feeding']
                if f is None:
                    require(actor['intake'] == actor['dissipated'] == 0, 'missing feeding record')
                else:
                    feedings += 1
                    site = f['site']
                    require(type(site) is int and 0 <= site < len(a), 'invalid feeding site')
                    allocation = lineage[actor['id']]['genome']['allocation_a']
                    require(type(allocation) is int and 0 <= allocation <= 16, 'invalid allocation')
                    qa = c['feeding_limit'] * allocation // 16
                    ca, cb = min(a[site], qa), min(b[site], c['feeding_limit'] - qa)
                    gain = ca // 2 + cb // 2
                    released = min(ca - ca // 2, c['capacity'] - b[site] + cb) if c['recycling'] else 0
                    loss = ca + cb - gain - released
                    expected = dict(site=site, a_before=a[site], b_before=b[site], allocation_a=allocation,
                        remaining_a=a[site]-ca, remaining_b=b[site]-cb+released,
                        consumed_a=ca, consumed_b=cb, energy_gain=gain, released_b=released, dissipated=loss)
                    require(f == expected, 'feeding conversion or stock mismatch')
                    require(actor['intake'] == gain and actor['dissipated'] == loss, 'actor feeding mismatch')
                    a[site], b[site] = expected['remaining_a'], expected['remaining_b']
                    for key, value in (('consumed_a', ca), ('consumed_b', cb), ('released_b', released),
                                       ('feeding_energy', gain), ('feeding_dissipation', loss)):
                        flows[key] += value
                costs = sum(actor[k] for k in ('basal', 'decision', 'movement', 'birth_cost',
                                               'development_cost', 'failure_loss'))
                require(actor['energy_after'] == actor['energy_before'] + actor['intake']
                        - costs - actor['child_energy'], 'individual energy mismatch')
                spent += costs + actor['dissipated']
            energy += added - spent
            require(row['spent'] == spent and row['energy_after'] == energy, 'world energy mismatch')
    require(ticks == meta['steps'] == meta['completed_steps'] == final['tick'] == summary['steps'], 'horizon mismatch')
    require(a == final['food'] and b == final['substrate_b'], 'terminal stocks mismatch')
    require(rng.getstate() == tuples(final['rng']['resources']), 'resource random endpoint mismatch')
    require(flows == summary['resource_flows'] and actors == summary['actor_records'], 'flow summary mismatch')
    require(sum(a) == summary['remaining_a'] and sum(b) == summary['remaining_b'], 'stock summary mismatch')
    require(energy == summary['total_energy'] == sum(a) + sum(b)
            + sum(o['energy'] for o in final['lineage'] if o['death_tick'] is None), 'final energy mismatch')
    return dict(scope='resource RNG, substrate transfers at recorded sites and arithmetic ledgers; '
                'not positions, decisions, actor eligibility, construction or ancestry',
                ticks=ticks, actors=actors, feedings=feedings, resource_flows=flows,
                output_sha256=hashes, script_sha256=sha256(Path(__file__).read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.directory)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result, indent=2))
