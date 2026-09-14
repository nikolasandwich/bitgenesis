"""Post hoc horizon sensitivity of the complete campaign-021 cohort; no simulation."""

import argparse
import hashlib
import json
from pathlib import Path


def survival_intervals(pairs, horizon):
    """Integer post-step states: extinction at t is already absent at t."""
    if type(horizon) is not int or horizon < 1 or not pairs:
        raise ValueError('Positive horizon and paired observations required')
    for pair in pairs:
        if len(pair) != 2 or any(t is not None and (type(t) is not int or not 1 <= t <= horizon) for t in pair):
            raise ValueError('Invalid extinction or censoring time')
    boundaries = sorted({0, horizon + 1, *(t for pair in pairs for t in pair if t is not None)})
    result = []
    for start, stop in zip(boundaries, boundaries[1:]):
        states = [(a is None or a > start, b is None or b > start) for a, b in pairs]
        counts = {name: sum(state == value for state in states) for name, value in (
            ('both_alive', (True, True)), ('capacity_96_only', (False, True)),
            ('capacity_24_only', (True, False)), ('both_extinct', (False, False)))}
        result.append(dict(start_tick=start, end_tick=stop-1, **counts,
                           signed_discordance=counts['capacity_96_only']-counts['capacity_24_only']))
    return result


def analyze(report):
    fields = ('arm', 'birth_threshold', 'renewal', 'food_capacity', 'seed')
    renewals = ('frequent-small', 'reference', 'rare-large')
    grid = {('block', t, n, c, s) for t in (40, 160) for n in renewals for c in (24, 96) for s in range(1800, 1810)}
    runs = report['runs']
    if len(runs) != 120 or {tuple(r[k] for k in fields) for r in runs} != grid:
        raise ValueError('Complete 120-world cohort required')
    index = {tuple(r[k] for k in fields): r for r in runs}
    for r in runs:
        t = r['extinction_tick']
        if r['tick'] != 10000 or r['right_censored'] != (t is None) or (r['population'] > 0) != (t is None):
            raise ValueError('Endpoint and censoring mismatch')
        survival_intervals([(t, t)], 10000)
        for h in (100, 500, 5000):
            if (r[f'population_at_{h}'] > 0) != (t is None or t > h):
                raise ValueError('Checkpoint and extinction mismatch')
    groups = []
    for threshold in (40, 160):
        for renewal in renewals:
            pairs = [tuple(index['block', threshold, renewal, c, s]['extinction_tick'] for c in (24, 96)) for s in range(1800, 1810)]
            intervals = survival_intervals(pairs, 10000)
            terminal = next(g for g in report['capacity_comparisons'] if (g['birth_threshold'], g['renewal']) == (threshold, renewal))
            if any(intervals[-1][k] != terminal[k] for k in ('both_alive', 'capacity_96_only', 'capacity_24_only', 'both_extinct', 'signed_discordance')):
                raise ValueError('Primary paired endpoint changed')
            groups.append(dict(birth_threshold=threshold, renewal=renewal, intervals=intervals,
                positive_horizon_ticks=sum(i['end_tick']-max(i['start_tick'], 1)+1 for i in intervals if i['signed_discordance'] > 0),
                negative_horizon_ticks=sum(i['end_tick']-max(i['start_tick'], 1)+1 for i in intervals if i['signed_discordance'] < 0),
                zero_horizon_ticks=sum(max(0, i['end_tick']-max(i['start_tick'], 1)+1) for i in intervals if i['signed_discordance'] == 0)))
    return dict(analysis='campaign-021-horizon-sensitivity-posthoc-1', groups=groups,
        scope='All integer post-step horizons 1..10000 from complete verified extinction times. Horizons are correlated descriptive views, not independent replicates, p-values or replacement primary outcomes. No new simulation or causal mediation claim.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification', type=Path, default=Path('docs/research/results/campaign-021-verification.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze(json.loads(args.verification.read_text(encoding='utf-8')))
    report['metric_report_sha256'] = hashlib.sha256(args.verification.read_bytes()).hexdigest()
    report['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps([{k: v for k, v in g.items() if k != 'intervals'} for g in report['groups']], indent=2))


if __name__ == '__main__':
    main()
