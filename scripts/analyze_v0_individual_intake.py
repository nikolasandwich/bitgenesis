"""Per-individual intake accounting on verified campaign-017 early action records."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path


def individuals(feeding, terminal, founders=80, horizon=100):
    """Include every born ID, even one dying before feeding or born at the horizon."""
    records = {i: dict(id=i, birth_tick=0, death_tick=None, feeding_attempts=0,
                      food_eaten=0, action_ticks=0) for i in range(founders)}
    feeds, deaths = defaultdict(list), defaultdict(list)
    for rows, grouped in ((feeding, feeds), (terminal, deaths)):
        for row in rows:
            if type(row['tick']) is not int or not 1 <= row['tick'] <= horizon:
                raise ValueError('Invalid observation tick')
            grouped[row['tick']].append(row)
    living = set(records)
    for tick in range(1, horizon + 1):
        f, d = feeds[tick], deaths[tick]
        fi, di = {r['id'] for r in f}, {r['id'] for r in d}
        if len(fi) != len(f) or len(di) != len(d) or fi & di or fi | di != living:
            raise ValueError('Action population is not partitioned')
        for i in living:
            records[i]['action_ticks'] += 1
        children = []
        for row in f:
            value = row['eaten']
            if type(value) is not int or not 0 <= value <= 8:
                raise ValueError('Invalid intake')
            r = records[row['id']]
            r['feeding_attempts'] += 1
            r['food_eaten'] += value
            if row['child_id'] is not None:
                children.append(row['child_id'])
        if sorted(children) != list(range(len(records), len(records) + len(children))):
            raise ValueError('Newborn IDs are not consecutive')
        for i in children:
            records[i] = dict(id=i, birth_tick=tick, death_tick=None,
                              feeding_attempts=0, food_eaten=0, action_ticks=0)
        for i in di:
            records[i]['death_tick'] = tick
        living = (living - di) | set(children)
    return list(records.values())


def cohort(rows):
    n = len(rows)
    total = sum(r['food_eaten'] for r in rows)
    top_count = (n + 4) // 5
    return dict(individuals=n, food_eaten=total,
                zero_intake_individuals=sum(r['food_eaten'] == 0 for r in rows),
                zero_action_individuals=sum(r['action_ticks'] == 0 for r in rows),
                feeding_attempts=sum(r['feeding_attempts'] for r in rows),
                action_ticks=sum(r['action_ticks'] for r in rows),
                top_count=top_count,
                top_intake_share=(sum(sorted((r['food_eaten'] for r in rows),
                                            reverse=True)[:top_count]) / total
                                  if total else None))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('data/action-replay-017'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    vp = root / 'docs/research/results/action-replay-017.json'
    records = json.loads(vp.read_text(encoding='utf-8'))['results']
    if len(records) != 40 or {(r['arm'], r['birth_threshold'], r['seed']) for r in records} != {
        (a, t, s) for a in ('dispersed', 'block') for t in (40, 160) for s in range(1400, 1410)}:
        raise ValueError('Incomplete verified grid')
    results, flat, hashes = [], [], {}
    for r in records:
        key = {k:r[k] for k in ('arm', 'birth_threshold', 'seed')}
        prefix = f"{r['arm']}-threshold-{r['birth_threshold']}-seed-{r['seed']}"
        streams = []
        for kind in ('feeding', 'terminal'):
            path = args.input / f'{prefix}-{kind}.jsonl'
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != r[kind + '_sha256']:
                raise ValueError('Input differs from verified replay')
            hashes[path.name] = digest
            streams.append([json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()])
        people = individuals(*streams)
        if sum(p['death_tick'] is not None for p in people) != r['total_deaths']:
            raise ValueError('Death total differs')
        if sum(p['food_eaten'] for p in people) != sum(f['eaten'] for f in streams[0]):
            raise ValueError('Intake allocation differs')
        for p in people:
            expected = (p['death_tick'] or 100) - p['birth_tick']
            if p['action_ticks'] != expected or p['feeding_attempts'] != expected - (p['death_tick'] is not None):
                raise ValueError('Individual exposure differs from lifecycle')
            flat.append(dict(**key, **p, cohort='founder' if p['id'] < 80 else 'descendant'))
        results.append(dict(**key,
                            founders=cohort([p for p in people if p['id'] < 80]),
                            descendants=cohort([p for p in people if p['id'] >= 80])))
    groups = []
    for arm in ('dispersed', 'block'):
        for threshold in (40, 160):
            subset = [r for r in results if r['arm'] == arm and r['birth_threshold'] == threshold]
            groups.append(dict(arm=arm, birth_threshold=threshold, founder_ranges={
                k:[min(r['founders'][k] for r in subset), max(r['founders'][k] for r in subset)]
                for k in ('food_eaten', 'zero_intake_individuals', 'top_intake_share', 'action_ticks')},
                descendant_food_range=[min(r['descendants']['food_eaten'] for r in subset),
                                       max(r['descendants']['food_eaten'] for r in subset)]))
    report = dict(scope='Retrospective ticks 1–100; realized individual intake, not resource entitlement or causal deprivation. Exposure and reproduction differ. Fixed founder cohort includes all 80 IDs, including zero intake. Descendants include horizon births.',
                  results=results, groups=groups, input_sha256=hashes,
                  verification_sha256=hashlib.sha256(vp.read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    with (args.output/'individuals.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    print(json.dumps(groups, indent=2))


if __name__ == '__main__':
    main()
