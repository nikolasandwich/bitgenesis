"""Re-audit the complete registered population cohort and trace inheritance."""
import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from bitgenesis.v2.audit import audit


def complete_grid(rows):
    expected = {(s, m) for s in range(84000, 84010) for m in (100, 0)}
    seen = {}
    for row in rows:
        key = (row['seed'], row['mutation_per_thousand'])
        if key not in expected or key in seen:
            raise ValueError('unexpected or duplicate trial')
        seen[key] = row
    if set(seen) != expected:
        raise ValueError('incomplete cohort')
    return seen


def inheritance(final):
    lineage = {o['id']: o for o in final['lineage']}
    attempts = final['attempts']
    children = [a for a in attempts if a['parent'] is not None]
    changed = [a for a in children if a['genome'] != lineage[a['parent']]['genome']]
    individuals = []
    for o in lineage.values():
        if o['parent'] is None:
            continue
        parent, founder = lineage[o['parent']], lineage[o['founder']]
        individuals.append({
            'id': o['id'], 'parent': o['parent'], 'founder': o['founder'],
            'generation': o['generation'], 'birth_tick': o['birth_tick'],
            'death_tick': o['death_tick'], 'offspring': o['offspring'],
            'genome_changed_from_parent': o['genome'] != parent['genome'],
            'genome_changed_from_founder': o['genome'] != founder['genome'],
            'controller_changed_from_parent': o['controller'] != parent['controller'],
        })
    return {
        'offspring_attempts': len(children), 'changed_genotype_attempts': len(changed),
        'changed_genotype_successes': sum(a['valid'] for a in changed),
        'changed_individuals_with_offspring': sum(
            o['genome_changed_from_parent'] and o['offspring'] > 0 for o in individuals),
        'founder_attempts': len(attempts) - len(children),
        'failure_reasons': {
            kind: dict(Counter(a['reason'] for a in attempts
                              if not a['valid'] and (a['parent'] is None) == (kind == 'founder')))
            for kind in ('founder', 'offspring')},
        'max_generation': max((o['generation'] for o in lineage.values()), default=None),
        'individuals': individuals,
    }


def verify(root):
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    meta = read(root / 'metadata.json')
    if (meta['status'], meta['completed_runs'], meta['planned_runs']) != ('complete', 20, 20):
        raise ValueError('incomplete execution')
    if meta['protocol_sha256'] != sha256(Path('experiments/v2/study-002.md').read_bytes()).hexdigest():
        raise ValueError('protocol mismatch')
    rows = complete_grid(read(root / 'results.json'))
    checks, pairs = [], []
    for seed in range(84000, 84010):
        initial_reference = None
        for mutation in (100, 0):
            directory = root / f'seed-{seed}-mutation-{mutation}'
            metadata = read(directory / 'metadata.json')
            expected = dict(width=16, height=16, capacity=24, initial_food=12,
                founders=32, initial_energy=640, renewal_per_thousand=15, renewal_amount=4,
                basal_cost=1, decision_cost=1, movement_cost=0, feeding_limit=8,
                birth_threshold=1280, birth_cost=0, mutation_per_thousand=mutation,
                direct_padding_cost=0)
            if (metadata['config'] != expected or metadata['seed'] != seed
                    or metadata['steps'] != 3000 or metadata['encoding'] != 'developmental'
                    or metadata['mode'] != 'intact' or metadata['git_dirty']
                    or metadata['git_commit'] != meta['git_commit']
                    or 'founder_genomes' in metadata):
                raise ValueError('registered configuration/source mismatch')
            checked = audit(directory)
            if checked != read(directory / 'audit.json'):
                raise ValueError('saved audit mismatch')
            if rows[(seed, mutation)] != dict(seed=seed, mutation_per_thousand=mutation, **checked['summary']):
                raise ValueError('execution summary mismatch')
            initial = read(directory / 'initial.json')
            if initial_reference is None:
                initial_reference = initial
            elif initial != initial_reference:
                raise ValueError('paired initialization mismatch')
            extinction = 0 if not initial['lineage'] else None
            with (directory / 'steps.jsonl').open(encoding='utf-8') as stream:
                for line in stream:
                    step = json.loads(line)
                    if not step['population'] and extinction is None:
                        extinction = step['tick']
            trace = inheritance(read(directory / 'final.json'))
            if mutation == 0 and trace['changed_genotype_attempts']:
                raise ValueError('changed genome in zero-mutation arm')
            checks.append(dict(seed=seed, mutation_per_thousand=mutation,
                extinction_tick=extinction, inheritance=trace, audit=checked))
            print(f'verified {len(checks)}/20', flush=True)
        pairs.append({'seed': seed, 'population_mutation': rows[(seed, 100)]['population'],
            'population_no_mutation': rows[(seed, 0)]['population'],
            'difference': rows[(seed, 100)]['population'] - rows[(seed, 0)]['population']})
    return {'scope': 'complete cohort and inheritance accounting; descriptive, not adaptation proof',
        'runs': 20, 'pairs': pairs,
        'mean_population_difference': str(Fraction(sum(p['difference'] for p in pairs), 10)),
        'checks': checks,
        'metadata_sha256': sha256((root / 'metadata.json').read_bytes()).hexdigest(),
        'results_sha256': sha256((root / 'results.json').read_bytes()).hexdigest(),
        'script_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('data/v2-study-002'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('output already exists')
    result = verify(args.input)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(result['mean_population_difference'])
