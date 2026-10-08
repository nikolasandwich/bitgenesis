"""Fixed artificial-input ablation; environmental tapes are not initial worlds."""
from dataclasses import asdict
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import platform
import random
import subprocess
import time

from bitgenesis.v4.hereditary_growing import step
from bitgenesis.v4.heredity import HeritableUnit
from bitgenesis.v4.lineage import Observer
from bitgenesis.v4.structure import snapshot
from scripts.analyze_v4_structure_copies import analyze, episodes
from scripts.copy_ablation_inputs import bindings, digest
from scripts.run_v4_copy_control import CONFIG, normalize

MODES = ('random-direction', 'random-feed', 'random-both')
SEEDS = range(120000, 120020)
GRID = tuple(product(SEEDS, MODES, (False, True)))
OUTPUT = Path('data/v4-study-019')
SECONDS = 600
STORAGE = 268435456
SUMMARY_INTS = ('seed', 'steps', 'births', 'deaths', 'living', 'initial_energy',
                'final_energy', 'imported', 'rejected_import', 'spent', 'proposed',
                'initial_mass', 'final_mass', 'longest')
SUMMARY_KEYS = set(SUMMARY_INTS) | {'mode', 'exchange', 'genetic_counts', 'episodes', 'persistent10', 'ever'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(seed, mode, exchange):
    require(type(seed) is int and seed in SEEDS and type(mode) is str and mode in MODES
            and type(exchange) is bool, 'strict fixed case identity')
    return seed, mode, exchange


def tapes(seed):
    require(type(seed) is int and seed in SEEDS, 'fixed environment seed')
    streams = [random.Random(int.from_bytes(hashlib.sha256(
        f'v4-copy-ablation-1:{seed}:{kind}'.encode('ascii')).digest(), 'big'))
        for kind in ('directions', 'feeds')]
    return [dict(directions=[streams[0].randrange(4) for _ in range(256)],
                 feed_sites=streams[1].sample(range(256), 4)) for _ in range(32)]


def run_case(seed, mode, exchange):
    identity(seed, mode, exchange)
    inputs = tapes(seed)
    units = [None] * 256
    raw = [0] * 256
    for site, material in ((85, 0), (86, 0), (204, 3)):
        units[site] = HeritableUnit(material, 64, (material,) * 4)
    for site in (101, 102, 117, 118):
        raw[site] = 1

    def serialized():
        return normalize([None if u is None else asdict(u) for u in units])

    observer = Observer(serialized())
    initial = dict(tick=0, units=serialized(), raw=list(raw), site_ids=list(observer.alive),
                   observation=snapshot(serialized(), observer.alive, 16, 16, phase='final'))
    rows = []
    for tick, tape in enumerate(inputs, 1):
        feed_sites = tape['feed_sites'] if mode != 'random-direction' else (85, 86, 117, 118)
        proposals = [8 if site in feed_sites else 0 for site in range(256)]
        directions = [1 if site % 16 == 6 else 0 for site in range(256)]
        if tick == 1:
            directions[85] = directions[86] = 2
        if tick == 2:
            directions[101] = directions[102] = 2
        if mode != 'random-feed':
            directions = list(tape['directions'])
        tickets = [(999, 0, 1)] * 256
        units, raw, record = step(units, raw, proposals=proposals, directions=directions,
                                  mutation_tickets=tickets, exchange=exchange, **CONFIG)
        physical = normalize(dict(tick=tick, units=serialized(), raw=list(raw),
                                  energy=sum(u.energy for u in units if u is not None),
                                  directions=directions, mutation_tickets=tickets, **record))
        observer.accept(physical)
        rows.append(dict(tick=tick, site_ids=list(observer.alive), physical=physical,
                         observation=snapshot(physical['units'], observer.alive, 16, 16, phase='final')))
    lineage = observer.result()
    final = dict(tick=32, units=serialized(), raw=list(raw), site_ids=list(observer.alive),
                 parents=[v['parent'] for v in lineage['individuals']])
    copies = analyze(initial, rows, final)
    require(len(copies) == 1 and copies[0]['component'] == 0 and copies[0]['anchor_members'] == [0, 1],
            'fixed eligible original parent')
    copy = copies[0]
    longest = copy['longest']['descendant_genetic']
    summary = dict(seed=seed, mode=mode, exchange=exchange, steps=32,
                   births=lineage['summary']['births'], deaths=lineage['summary']['deaths'],
                   living=sum(u is not None for u in units), initial_energy=192,
                   final_energy=sum(u.energy for u in units if u is not None),
                   imported=sum(r['physical']['imported'] for r in rows),
                   rejected_import=sum(r['physical']['rejected_import'] for r in rows),
                   spent=sum(r['physical']['spent'] for r in rows), proposed=1024,
                   initial_mass=7, final_mass=sum(raw) + sum(u is not None for u in units),
                   genetic_counts=copy['series']['descendant_genetic'],
                   episodes=copy['episodes']['descendant_genetic'], longest=longest,
                   persistent10=longest >= 10, ever=longest > 0)
    validate_summary(summary)
    return dict(seed=seed, mode=mode, exchange=exchange, config=dict(CONFIG), initial=initial,
                rows=rows, final=final, copy_parents=copies, summary=summary)


def validate_summary(row):
    require(type(row) is dict and set(row) == SUMMARY_KEYS, 'complete exact case summary')
    key = identity(row['seed'], row['mode'], row['exchange'])
    require(all(type(row[k]) is int and row[k] >= 0 for k in SUMMARY_INTS), 'native nonnegative summary integers')
    require(type(row['persistent10']) is bool and type(row['ever']) is bool, 'strict event booleans')
    counts = row['genetic_counts']
    require(type(counts) is list and len(counts) == 32 and all(type(v) is int and 0 <= v <= 128 for v in counts), '32 bounded genetic counts')
    spans = row['episodes']
    require(type(spans) is list and all(type(p) is list and len(p) == 2 and all(type(v) is int for v in p) for p in spans), 'strict inclusive episodes')
    expected = episodes(counts)
    longest = max((b-a+1 for a, b in expected), default=0)
    require(spans == expected and row['longest'] == longest and row['persistent10'] == (longest >= 10)
            and row['ever'] == (longest > 0), 'consistent genetic event summary')
    require(row['steps'] == 32 and row['proposed'] == 1024 and row['initial_energy'] == 192
            and row['initial_mass'] == row['final_mass'] == 7, 'fixed horizon and initial state')
    require(row['living'] == 3 + row['births'] - row['deaths'] and row['living'] <= 7,
            'population ledger')
    require(row['imported'] + row['rejected_import'] == 1024 and
            row['final_energy'] == 192 + row['imported'] - row['spent'], 'energy ledger')
    return key


def summarize(summaries):
    require(type(summaries) is list and len(summaries) == 120, 'complete 120 summaries')
    keys = [validate_summary(row) for row in summaries]
    require(len(set(keys)) == 120 and set(keys) == set(GRID), 'unique complete case grid')
    index = dict(zip(keys, summaries))
    cells, pairs, groups = [], [], []
    for mode, exchange in product(MODES, (False, True)):
        rows = [index[seed, mode, exchange] for seed in SEEDS]
        successes = sum(row['persistent10'] for row in rows)
        ever_count = sum(row['ever'] for row in rows)
        cell = dict(mode=mode, exchange=exchange, n=20, successes=successes, ever_count=ever_count,
                    success_fraction=str(Fraction(successes, 20)), ever_fraction=str(Fraction(ever_count, 20)))
        for field in ('longest', 'births', 'deaths', 'living', 'imported', 'rejected_import', 'spent'):
            cell['mean_' + field] = str(Fraction(sum(row[field] for row in rows), 20))
        cells.append(cell)
    for seed, mode in product(SEEDS, MODES):
        off, on = (index[seed, mode, exchange]['persistent10'] for exchange in (False, True))
        pairs.append(dict(seed=seed, mode=mode, off=off, on=on, difference=int(on)-int(off)))
    for mode in MODES:
        selected = [p for p in pairs if p['mode'] == mode]
        groups.append(dict(mode=mode, n=20,
                           on_only=sum(p['on'] and not p['off'] for p in selected),
                           off_only=sum(p['off'] and not p['on'] for p in selected),
                           both=sum(p['on'] and p['off'] for p in selected),
                           neither=sum(not p['on'] and not p['off'] for p in selected),
                           mean_difference=str(Fraction(sum(p['difference'] for p in selected), 20))))
    return dict(cells=cells, pairs=pairs, groups=groups)


def save(path, value):
    path.write_text(json.dumps(value, separators=(',', ':')) + '\n')


def main():
    require(not subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip(), 'clean launch required')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    results = []
    meta = dict(status='running', planned_cases=120, completed_cases=0, new_simulation_steps=0,
                new_independent_initial_worlds=0, new_environment_sources=20, artificial_initial_state=True,
                python_version=platform.python_version(), time_limit_seconds=SECONDS, storage_limit_bytes=STORAGE)
    save(OUTPUT/'metadata.json', meta)
    save(OUTPUT/'results.json', results)

    def budget():
        require(time.monotonic()-started < SECONDS, 'time budget exceeded')
        require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file()) < STORAGE, 'storage budget exceeded')

    try:
        (OUTPUT/'cases').mkdir()
        meta['git_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        meta['input_sha256'] = bindings()
        require(len(meta['input_sha256']) == 57, '57 bound inputs required')
        save(OUTPUT/'metadata.json', meta)
        for seed, mode, exchange in GRID:
            budget()
            require(bindings() == meta['input_sha256'], 'bound inputs changed during run')
            case = run_case(seed, mode, exchange)
            require(validate_summary(case['summary']) == (seed, mode, exchange), 'case summary identity')
            filename = f'seed-{seed}-{mode}-exchange-{str(exchange).lower()}.json'
            save(OUTPUT/'cases'/filename, case)
            results.append(case['summary'])
            save(OUTPUT/'results.json', results)
            meta.update(completed_cases=len(results), new_simulation_steps=32*len(results))
            save(OUTPUT/'metadata.json', meta)
            budget()
            require(bindings() == meta['input_sha256'], 'bound inputs changed after case')
            print(f'{len(results)}/120 ablation cases saved', flush=True)
        summary = summarize(results)
        budget()
        require(bindings() == meta['input_sha256'], 'bound inputs changed')
        save(OUTPUT/'summary.json', summary)
        meta['status'] = 'complete'
    except BaseException as error:
        meta.update(status='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        failure = None
        try:
            meta['input_sha256_after'] = bindings()
            require(meta.get('input_sha256') == meta['input_sha256_after'], 'bound inputs changed at finalization')
            budget()
        except BaseException as error:
            failure = f'{type(error).__name__}: {error}'
            meta.update(status='failed', finalization_error=failure)
        meta['elapsed_seconds'] = time.monotonic()-started
        meta['output_sha256'] = {str(p.relative_to(OUTPUT)): digest(p) for p in sorted(OUTPUT.rglob('*.json'))
                                 if p != OUTPUT/'metadata.json'}
        save(OUTPUT/'metadata.json', meta)
        if failure is not None and 'error' not in meta:
            raise ValueError(failure)


if __name__ == '__main__':
    main()
