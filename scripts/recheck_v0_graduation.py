"""Reproduce the scope23 V0 lineage reassessment from the ten original records."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path


def inspect_lineage(lineage, treatment):
    if treatment not in ('baseline', 'no-mutation'):
        raise ValueError('Unknown treatment')
    index = {r['id']: r for r in lineage}
    if len(index) != len(lineage):
        raise ValueError('Duplicate individual ID')
    counts = Counter(r['parent_id'] for r in lineage if r['parent_id'] is not None)
    if any(parent not in index for parent in counts):
        raise ValueError('Missing parent')
    if any(r['offspring'] != counts[r['id']] for r in lineage):
        raise ValueError('Stored offspring differs from parent edges')
    if any(type(r['genome']) is not int or not 0 <= r['genome'] <= 1000 for r in lineage):
        raise ValueError('Invalid genome')
    founders = [r for r in lineage if r['parent_id'] is None]
    if len(founders) != 80:
        raise ValueError('Expected eighty founders')
    changed = sum(r['genome'] != index[r['parent_id']]['genome']
                  for r in lineage if r['parent_id'] is not None)
    values = {r['genome'] for r in lineage}
    initial = {r['genome'] for r in founders}
    if treatment == 'no-mutation' and (changed or values != initial):
        raise ValueError('No-mutation inheritance changed')
    if treatment == 'baseline' and (not changed or not values-initial):
        raise ValueError('No new inherited variation demonstrated')
    offspring = [r['offspring'] for r in founders]
    if min(offspring) == max(offspring):
        raise ValueError('No differential founder reproduction demonstrated')
    return dict(lineage_records=len(lineage), changed_inheritance=changed,
                new_values=len(values-initial),
                founder_offspring_range=[min(offspring), max(offspring)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected', type=Path,
                        help='Require exact equality with an existing reassessment')
    args = parser.parse_args()
    rows, hashes = [], {}
    for treatment in ('baseline', 'no-mutation'):
        for seed in range(5):
            folder = args.root/f'data/campaign-001/{treatment}-seed-{seed}'
            lineage = json.loads((folder/'lineage.json').read_text(encoding='utf-8'))
            checked = inspect_lineage(lineage, treatment)
            with (folder/'metrics.csv').open(encoding='utf-8', newline='') as stream:
                metrics = list(csv.DictReader(stream))
            if [int(r['tick']) for r in metrics] != list(range(5001)):
                raise ValueError('Incomplete original metric horizon')
            extinction = next((int(r['tick']) for r in metrics if int(r['population']) == 0), None)
            rows.append(dict(treatment=treatment, seed=seed, **checked, extinction_tick=extinction))
            for name in ('lineage.json', 'metrics.csv'):
                path = folder/name
                hashes[path.relative_to(args.root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    engine = args.root/'src/bitgenesis/v0/engine.py'
    digest = hashlib.sha256(engine.read_text(encoding='utf-8').encode()).hexdigest()
    if digest != '8f3ed33ad0ebe802c099e3e6f8ae61f9bcc526b98512f31f48ec40478fbfa7ff':
        raise ValueError('Frozen normalized engine differs')
    report = dict(scope='Current reinspection of five original seeds per arm for V0 variation and differential direct offspring criteria. Not trait causality or V1 evidence.',
                  rows=rows, input_sha256=hashes, normalized_engine_sha256=digest)
    if args.expected and report != json.loads(args.expected.read_text(encoding='utf-8')):
        raise ValueError('Reassessment differs from expected evidence')
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(f'Rechecked {len(rows)} original worlds; no new simulation')


if __name__ == '__main__':
    main()
