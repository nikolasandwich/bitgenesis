"""Study047: immutable sources, saved identity structure and past RNG only.

No physics, future environmental draws, copy classification or future result reads.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import _random
import subprocess
import sys
import time

BASE = Path('docs/research/results')
SOURCES = BASE / 'v4-study-047-design-revalidated-sources.json'
CENSUS = BASE / 'v4-study-047-design-revalidated-census.json'
ENCODINGS = ('east', 'west', 'south', 'north', 'homogeneous')
SEEDS = range(120000, 120020)
SECONDS = 600
STORAGE = 128 * 1024**2
CONFIG = dict(width=16, height=16, capacity=64, leak=1, bond_cost=1,
              threshold=16, construction_cost=4, copy_cost=1, mutation_per_thousand=0)
STABLE = (
    'experiments/v4/study-047.md',
    'docs/design/v4-middle-policy-withdrawal.zh-CN.md',
    'scripts/audit_v4_middle_withdrawal_design.py',
    '.kiro/specs/middle-policy-withdrawal/requirements.md',
    '.kiro/specs/middle-policy-withdrawal/design.md',
    '.kiro/specs/middle-policy-withdrawal/research.md',
    'docs/research/results/v4-study-046-validation.json',
    'docs/research/results/v4-study-046-formal-review.json',
    'docs/research/v4-study-046-results.zh-CN.md',
    'docs/research/results/v4-study-047-task-graph-review.json',
    'docs/research/results/v4-study-047-design-sources.json',
    'docs/research/results/v4-study-047-design-census.json',
    'docs/research/results/v4-study-047-design-epochs/epoch-1/preservation.json',
    'docs/research/results/v4-study-047-design-revalidation-run/fault-check.py',
    'docs/research/results/v4-study-047-design-revalidation-run/fault-execution.json',
    'docs/research/results/v4-study-047-design-revalidation-run/fault-stdout.txt',
    'docs/research/results/v4-study-047-design-revalidation-run/fault-stderr.txt',
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read(path: str | Path):
    return json.loads(Path(path).read_text())


def digest(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def object_hash(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def same(actual, expected, label: str) -> None:
    require(canonical(actual) == canonical(expected), label)


def save(path: Path, value, *, exclusive: bool = False) -> None:
    with path.open('x' if exclusive else 'w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def hashes(paths: list[str], *, phase: str = '') -> tuple[dict, dict, BaseException | None]:
    values, errors = {}, {}
    first_error = None
    for path in paths:
        try:
            values[path] = digest(path)
        except BaseException as error:
            errors[path] = repr(error)
            if first_error is None:
                first_error = error
    return values, errors, first_error


def reserve(path: Path, value, owned: set[Path]) -> None:
    with path.open('x') as stream:
        owned.add(path)
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def source_ref(path: str, pointer: str, value) -> dict:
    return dict(path=path, sha256=digest(path), pointer=pointer, value_sha256=object_hash(value))


def proposals(physical: dict) -> list[int]:
    values = physical['driven']['inputs']
    same([v['site'] for v in values], list(range(256)), 'ordered all-site inputs')
    return [v['proposed'] for v in values]


def initial_units(encoding: str) -> list:
    units = [None] * 256
    for site, material in ((85, 0), (86, 0), (204, 3)):
        program = [material] * 4
        if site in (85, 86) and encoding != 'homogeneous':
            program[ENCODINGS.index(encoding)] = site - 84
        units[site] = dict(material=material, energy=64, program=program)
    return units


def new_person(people: list, ids: list, site: int, tick: int, unit: dict,
               parent: int | None, mutated: bool = False) -> None:
    identity = len(people)
    ancestor = None if parent is None else people[parent]
    people.append(dict(id=identity, site=site, birth_tick=tick, death_tick=None,
                       parent=parent, founder=identity if ancestor is None else ancestor['founder'],
                       generation=0 if ancestor is None else ancestor['generation'] + 1,
                       material=unit['material'], program=list(unit['program']),
                       birth_energy=unit['energy'], mutated=mutated, offspring=0))
    ids[site] = identity
    if ancestor is not None:
        ancestor['offspring'] += 1


def accept_saved(row: dict, people: list, ids: list, tick: int) -> tuple[list, list]:
    """Only consume already saved events; never calculate a physical transition."""
    p = row['physical']
    same(row['tick'], tick, 'saved tick')
    same(p['tick'], tick, 'physical tick')
    before = list(ids)
    birth_start = len(people)
    deaths = []
    for site in p['material']['dissolved']:
        identity = ids[site]
        require(identity is not None, 'saved dissolution identity')
        people[identity]['death_tick'] = tick
        deaths.append(identity)
        ids[site] = None
    for item in p['material']['proposals']:
        if item['reason'] != 'formed':
            continue
        parent = ids[item['source']]
        require(parent is not None and people[parent]['birth_tick'] < tick, 'saved old parent')
        require(ids[item['target']] is None, 'saved empty birth target')
        same(people[parent]['program'], item['parent_program'], 'saved parental full program')
        new_person(people, ids, item['target'], tick,
                   dict(material=item['material'], program=item['child_program'], energy=item['child_energy']),
                   parent, item['mutated'])
    same(ids, row['site_ids'], 'saved site identities')
    for identity, unit in zip(ids, p['units']):
        require((identity is None) == (unit is None), 'occupation and identity agree')
        if unit is not None:
            same([people[identity]['program'], people[identity]['material']],
                 [unit['program'], unit['material']], 'saved living program and material')
    require(sum(i is not None for i in ids) == sum(i is not None for i in before)
            + len(people) - birth_start - len(deaths), 'saved population equation')
    return deepcopy(people[birth_start:]), deaths


def finish_method(source: dict, census: dict, paths: list[str], owned: set[Path],
                  sources: Path, census_path: Path, started: float, work_done: bool,
                  failure: BaseException | None, budget) -> None:
    """Attempt every closing action, persist failure and raise the first exception."""
    source['finalization_errors'] = {}
    try:
        after, errors, closing_error = hashes(paths, phase='closing')
        source['files_sha256_after'] = after
        source['input_read_errors_after'] = errors
        if closing_error is not None:
            raise closing_error
        same(after, source['files_sha256'], 'unchanged all method inputs')
        budget()
    except BaseException as error:
        source['finalization_errors']['bindings_and_budget'] = repr(error)
        if failure is None:
            failure = error
    try:
        census['status'] = 'complete' if work_done and failure is None else 'failed'
        census['completed_cases'] = len(census['cases'])
        census['completed_environments'] = len(census['environments'])
        if failure is not None:
            census['error'] = repr(failure)
        if census_path in owned:
            save(census_path, census)
        budget()
    except BaseException as error:
        source['finalization_errors']['census'] = repr(error)
        if failure is None:
            failure = error
    try:
        if census_path in owned:
            source['census_sha256'] = digest(census_path)
    except BaseException as error:
        source['finalization_errors']['output_hash'] = repr(error)
        if failure is None:
            failure = error
    source['status'] = 'complete' if work_done and failure is None else 'failed'
    source['elapsed_seconds'] = time.monotonic() - started
    source['completed_cases'] = len(census['cases'])
    source['completed_environments'] = len(census['environments'])
    if failure is not None:
        source['error'] = repr(failure)
    try:
        if sources in owned:
            save(sources, source)
        budget()
    except BaseException as error:
        if failure is None:
            failure = error
        source.update(status='failed', error=repr(failure))
    if failure is not None:
        # Attempt both independent final writes; never touch an unowned raced file.
        census.update(status='failed', error=repr(failure))
        source.update(status='failed', error=repr(failure))
        if census_path in owned:
            try:
                save(census_path, census)
            except BaseException as error:
                source['finalization_errors']['failed_census_write'] = repr(error)
            try:
                source['census_sha256'] = digest(census_path)
            except BaseException as error:
                source['finalization_errors']['failed_census_hash'] = repr(error)
        if sources in owned:
            try:
                save(sources, source)
            except BaseException:
                pass
        raise failure


def run(sources: Path = SOURCES, census_path: Path = CENSUS) -> None:
    require(not sources.exists() and not census_path.exists(), 'exclusive method outputs already exist')
    require(not Path('data/v4-study-047').exists(), 'future formal directory must not exist')
    started = time.monotonic()
    source = dict(status='running', study='047', task='1.1',
                  started_at_utc=datetime.now(timezone.utc).isoformat(),
                  git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  physical_steps=0, replayed_physical_steps=0, future_environment_draws=0,
                  future_scientific_outputs=False, time_limit_seconds=SECONDS,
                  storage_limit_bytes=STORAGE, input_paths=[], files_sha256={},
                  files_sha256_after={}, input_read_errors_before={}, input_read_errors_after={},
                  binding_exclusions=['mutable spec.json', 'mutable tasks.md', 'parent LOG.md',
                                      'method outputs and reports produced after freeze'])
    census = dict(status='running', study='047', task='1.1', physical_steps=0,
                  replayed_physical_steps=0, future_environment_draws=0,
                  fixed_future_ticks=[33, 64], future_results_available=False,
                  cases=[], environments=[], groups=[])
    paths = []
    owned: set[Path] = set()
    source['capture_stages'] = []
    failure = None
    work_done = False

    def budget() -> None:
        require(time.monotonic() - started < SECONDS, 'method time budget')
        require(sum(p.stat().st_size for p in owned if p.exists()) < STORAGE,
                'method output storage budget')

    def capture(phase: str, wanted: list[str] | dict, expected: dict | None = None) -> None:
        nonlocal paths
        requested = sorted(wanted)
        paths = sorted(set(paths) | set(requested))
        source['input_paths'] = paths
        values, errors, first_error = hashes(requested, phase=phase)
        source['capture_stages'].append(dict(phase=phase, files_sha256=values, read_errors=errors))
        changes = {}
        for path, h in values.items():
            old = source['files_sha256'].setdefault(path, h)
            if old != h:
                changes[path] = dict(before=old, after=h)
        source['input_read_errors_before'].update(errors)
        # Persist captured evidence before a bad hash or source read stops the run.
        try:
            save(sources, source)
        except BaseException as error:
            if first_error is None:
                first_error = error
        if first_error is not None:
            raise first_error
        require(not changes, 'inputs changed during capture: ' + repr(changes))
        if expected is not None:
            same(values, expected, 'immutable hashes at ' + phase)

    try:
        reserve(sources, source, owned)
        reserve(census_path, census, owned)
        runtime_files = [str(Path(random.__file__).resolve()), str(Path(_random.__file__).resolve()),
                         str(Path(sys.executable).resolve())]
        capture('entry_inventory', list(STABLE) + runtime_files)
        preservation = read('docs/research/results/v4-study-047-design-epochs/epoch-1/preservation.json')
        capture('first_method_epoch_archive', preservation['files_sha256'], preservation['files_sha256'])
        historical = read('docs/research/results/v4-study-047-design-sources.json')
        same(historical['files_sha256'], historical['files_sha256_after'], 'first method epoch stable')
        require(historical['status'] == 'complete', 'first method epoch succeeded')
        epoch_expected = dict(historical['files_sha256'])
        for item in preservation['source_epochs']:
            same(epoch_expected.pop(item['original_path']), item['sha256'], 'historical source version')
            epoch_expected[item['archived_path']] = item['sha256']
        capture('first_method_historical_bindings', epoch_expected, epoch_expected)
        source['historical_source_epochs'] = preservation['source_epochs']
        validation = read('docs/research/results/v4-study-046-validation.json')
        review = read('docs/research/results/v4-study-046-formal-review.json')
        require(validation['decision'] == 'GO' and review['verdict'] == 'APPROVED', '046 completed gates')
        same(validation['files_sha256'], validation['files_sha256_after'], '046 stable validation inputs')
        same(review['files_sha256'], review['files_sha256_after'], '046 stable review inputs')
        expected = dict(validation['files_sha256'])
        for path, h in review['files_sha256'].items():
            if path in expected:
                same(expected[path], h, 'overlapping review source hash')
            expected[path] = h
        capture('046_completed_source_closure', expected, expected)
        meta = read('data/v4-study-043/metadata.json')
        proof = read('data/v4-study-043/independent-verification.json')
        require(meta['status'] == 'complete' and proof['status'] == 'verified', '043 complete verified')
        same(meta['input_sha256'], meta['input_sha256_after'], '043 before after')
        same(meta['input_sha256'], proof['input_sha256'], '043 shared source epoch')
        same(proof['input_sha256'], proof['input_sha256_after'], '043 verifier before after')
        capture('043_inputs', meta['input_sha256'], meta['input_sha256'])
        expected.update(meta['input_sha256'])
        for mapping in (meta['output_sha256'], proof['files_sha256']):
            full = {f'data/v4-study-043/{p}': h for p, h in mapping.items()}
            capture('043_outputs', full, full)
            expected.update(full)
        records = read('data/v4-study-043/records.json')
        same([(r['encoding'], r['seed']) for r in records],
             [(e, s) for e in ENCODINGS for s in SEEDS], 'fixed ordered hundred index')
        active_seeds = sorted({r['seed'] for r in records if r['trigger']})
        extra = set(STABLE) | {'data/v4-study-043/independent-verification.json'}
        for seed in SEEDS:
            for mode in ('random-direction', 'random-both'):
                extra.add(f'data/v4-study-019/cases/seed-{seed}-{mode}-exchange-false.json')
        extra.update(r['source'] for r in records)
        extra.update(runtime_files)
        capture('complete_method_inventory', sorted(set(expected) | extra))
        require(not source['input_read_errors_before'], 'all inputs readable')
        for path, h in expected.items():
            same(source['files_sha256'][path], h, 'source closure matches historical validation')
        source['runtime'] = dict(python_version=platform.python_version(), implementation=platform.python_implementation(),
                                 executable=sys.executable, random_module=random.__file__,
                                 random_extension=_random.__file__, random_state_version=random.Random.VERSION,
                                 files_sha256={p: source['files_sha256'][p] for p in runtime_files})
        source['upstream'] = dict(validation046=len(validation['files_sha256']), review046=len(review['files_sha256']),
                                  input043=len(meta['input_sha256']),
                                  source043_production_commit=meta['git_commit'], source043_verification_commit=proof['git_commit'])
        save(sources, source)
        budget()
        past = {}
        fixed_proposals = [8 if s in (85, 86, 117, 118) else 0 for s in range(256)]
        fixed_tickets = [[999, 0, 1] for _ in range(256)]
        for seed in SEEDS:
            budget()
            envpaths = {mode: f'data/v4-study-019/cases/seed-{seed}-{mode}-exchange-false.json'
                        for mode in ('random-direction', 'random-both')}
            originals = {mode: read(path) for mode, path in envpaths.items()}
            for mode, case in originals.items():
                same([case['seed'], case['mode'], case['exchange'], case['config'], len(case['rows'])],
                     [seed, mode, False, CONFIG, 32], 'true original environmental source')
            streams = {kind: random.Random(int.from_bytes(hashlib.sha256(
                f'v4-copy-ablation-1:{seed}:{kind}'.encode('ascii')).digest(), 'big'))
                       for kind in ('directions', 'feeds')}
            tape = []
            for tick in range(1, 33):
                directions = [streams['directions'].randrange(4) for _ in range(256)]
                feeds = streams['feeds'].sample(range(256), 4)
                p = originals['random-direction']['rows'][tick - 1]['physical']
                q = originals['random-both']['rows'][tick - 1]['physical']
                for value in (p, q):
                    same(value['tick'], tick, 'original tick order')
                    same(value['directions'], directions, 'all original directions match reconstructed past')
                    same(value['mutation_tickets'], fixed_tickets, 'original constant mutation tickets')
                same(proposals(p), fixed_proposals, 'true fixed feed in random-direction')
                same(proposals(q), [8 if s in feeds else 0 for s in range(256)], 'historical random feed set')
                tape.append(dict(tick=tick, directions=directions, feed_sites_draw_order=feeds))
            past[seed] = tape
            state = {kind: json.loads(json.dumps(rng.getstate())) for kind, rng in streams.items()}
            census['environments'].append(dict(seed=seed, active_in_047=seed in active_seeds,
                origin_paths=envpaths, past_ticks=32, direction_values=8192, feed_samples=128,
                tape_sha256=object_hash(tape), past_feed_sites_draw_order=[t['feed_sites_draw_order'] for t in tape],
                feed_verification_scope='原输入保存集合，不保存sample顺序；这里有序样本为绑定实现重建',
                states_after_tick32=state, state_sha256={kind: object_hash(v) for kind, v in state.items()}))
        for old in records:
            budget()
            enc, seed = old['encoding'], old['seed']
            case = read(old['source'])
            same([case['seed'], case['mode'], case['exchange'], case['config'], len(case['rows'])],
                 [seed, 'random-direction', False, CONFIG, 32], 'original encoded source')
            same(case['initial']['units'], initial_units(enc), 'own original full program template')
            for tick, row in enumerate(case['rows'], 1):
                same(row['physical']['directions'], past[seed][tick - 1]['directions'], 'same seed cross encoding tape')
                same(row['physical']['mutation_tickets'], fixed_tickets, 'encoded fixed mutation tickets')
                same(proposals(row['physical']), fixed_proposals, 'encoded fixed feed')
            item = {k: deepcopy(old[k]) for k in ('encoding', 'seed', 'source', 'trigger', 't0', 'remaining', 'short_window', 'applicability', 'selection')}
            item.update(future_applicability='conditional_triggered' if old['trigger'] else 'not_applicable_original_32_no_trigger',
                        planned_arms=2 if old['trigger'] else 0, planned_steps_per_arm=32 if old['trigger'] else 0,
                        future_metrics=None, boundary=None)
            if old['trigger']:
                path = f'data/v4-study-043/cases/{enc}-{seed}.json'
                branch = read(path)
                same(branch['selection'], old['selection'], 'same frozen selection')
                arm = branch['ablation']
                t0 = old['t0']
                people, ids = [], [None] * 256
                for site, unit in enumerate(case['initial']['units']):
                    if unit is not None:
                        new_person(people, ids, site, 0, unit, None)
                same(ids, case['initial']['site_ids'], 'original founders and sites')
                for tick, row in enumerate(case['rows'][:t0], 1):
                    accept_saved(row, people, ids, tick)
                initial = arm['initial']
                same(people, initial['individuals'], 'full historical individuals before one removal')
                units, raw = deepcopy(case['rows'][t0 - 1]['physical']['units']), list(case['rows'][t0 - 1]['physical']['raw'])
                removals = []
                for identity in (0, 1):
                    site = ids.index(identity)
                    removals.append(dict(identity=identity, site=site, energy=units[site]['energy']))
                    ids[site] = None
                    units[site] = None
                    raw[site] += 1
                same(initial['removals'], removals, 'one original removal evidence')
                same(initial['energy_export'], sum(r['energy'] for r in removals), 'one original energy export')
                same([initial['tick'], initial['units'], initial['raw'], initial['site_ids'], initial['parents']],
                     [t0, units, raw, ids, [p['parent'] for p in people]], 'original post-removal structural state')
                same(len(arm['rows']), 32 - t0, 'all saved north suffix rows')
                for tick, row in enumerate(arm['rows'], t0 + 1):
                    directions = list(past[seed][tick - 1]['directions'])
                    directions[101] = directions[102] = 3
                    same(row['physical']['directions'], directions, 'only original north mask')
                    same(row['physical']['mutation_tickets'], fixed_tickets, 'north mutation tickets')
                    same(proposals(row['physical']), fixed_proposals, 'north fixed feed')
                    births, deaths = accept_saved(row, people, ids, tick)
                    same([row['births'], row['deaths']], [births, deaths], 'complete saved birth death events')
                final = arm['final']
                last = arm['rows'][-1]['physical'] if arm['rows'] else initial
                same(final, dict(tick=32, units=last['units'], raw=last['raw'], site_ids=ids,
                                 parents=[p['parent'] for p in people], individuals=people), 'full resumable final and observer history')
                alive = [i for i in ids if i is not None]
                require(len(alive) == len(set(alive)), 'unique living identities')
                same(sorted(alive), [p['id'] for p in people if p['death_tick'] is None and p['id'] not in (0, 1)],
                     'external removals separate from natural deaths')
                require(sum(final['raw']) + len(alive) == 7, 'boundary material mass')
                for i, person in enumerate(people):
                    require(person['id'] == i and (person['parent'] is None or type(person['parent']) is int and 0 <= person['parent'] < i),
                            'ordered complete parent history')
                envroot = f"data/v4-study-{'023' if enc == 'north' else '019'}/cases/seed-{seed}-random-direction-exchange-false.json"
                item['boundary'] = dict(final=source_ref(path, '/ablation/final', final),
                    template=source_ref(old['source'], '/initial', case['initial']),
                    historical_removals=source_ref(path, '/ablation/initial/removals', removals),
                    original_environment_root=envroot, physical_tick=32, observer_tick=32, founders=3,
                    next_identity=len(people), living=len(alive), energy=sum(u['energy'] for u in final['units'] if u is not None),
                    material_mass=7, initial_history_count=len(initial['individuals']),
                    saved_prefix_event_ticks=t0, saved_north_event_ticks=32 - t0,
                    history_count=len(people), restored_observer_sha256=object_hash(dict(tick=32, alive=ids, individuals=people, founders=3)),
                    original_export=initial['energy_export'], planned_new_export=0)
            census['cases'].append(item)
        same(len(census['cases']), 100, 'all hundred records')
        same(sum(c['trigger'] for c in census['cases']), 28, 'all 28 eligible')
        for enc in ENCODINGS:
            group = [c for c in census['cases'] if c['encoding'] == enc]
            n = sum(c['trigger'] for c in group)
            census['groups'].append(dict(encoding=enc, original_n=20, selected_n=n, not_applicable=20-n,
                                         historical_short_windows=sum(c['short_window'] for c in group),
                                         planned_arm_steps=64*n))
        same([g['selected_n'] for g in census['groups']], [5, 3, 0, 9, 11], 'fixed encoding cohort')
        same(sum(c['short_window'] for c in census['cases']), 10, 'historical short windows')
        census['counts'] = dict(original_index=100, selected_pairs=28, no_trigger_not_applicable=72,
            unique_active_environment_seeds=14, active_environment_seeds=active_seeds,
            audited_original_environment_seeds=20, regenerated_past_generator_ticks=640,
            regenerated_past_direction_values=163840, generated_future_generator_ticks=0,
            saved_selected_ancestry_ticks=896, saved_north_event_ticks=390,
            planned_formal_steps_per_route=1792, planned_engineering_steps_per_route=64,
            planned_engineering_and_formal_both_routes=3712,
            new_physical_steps=0, replayed_physical_steps=0)
        require(len(active_seeds) == 14, '14 existing active environments')
        source['source_files'] = len(paths)
        source['formal_output_created'] = Path('data/v4-study-047').exists()
        require(not source['formal_output_created'], 'no future directory')
        work_done = True
    except BaseException as error:
        failure = error
        source['error'] = repr(error)
    finally:
        finish_method(source, census, paths, owned, sources, census_path,
                      started, work_done, failure, budget)
    print(json.dumps(dict(status='complete', input_files=len(paths), **census['counts'],
                          elapsed_seconds=source['elapsed_seconds']), ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-prefix', type=Path, default=BASE / 'v4-study-047-design-revalidated')
    args = parser.parse_args()
    run(Path(str(args.output_prefix) + '-sources.json'), Path(str(args.output_prefix) + '-census.json'))
