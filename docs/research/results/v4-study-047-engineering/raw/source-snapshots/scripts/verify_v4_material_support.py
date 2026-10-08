"""Study033 independent local-stock audit after full dictionary physics replay."""
from itertools import product
import json
import math
from pathlib import Path
from time import monotonic
from scripts import verify_v4_north_opportunities as old

GENOTYPES = ('homogeneous', 'heterogeneous')
MODES = ('random-direction', 'random-feed', 'random-both')
GRID = tuple(product(GENOTYPES, MODES, (False, True), range(120000, 120020)))
CATEGORIES = ('no_initial_material', 'occupied', 'available', 'other')
REASONS = ('energy', 'occupied', 'raw_material', 'collision', 'formed')
OUTPUT = Path('data/v4-study-033')
IDENTITY = ('genotype', 'mode', 'exchange', 'seed')
EVENT_KEYS = set('tick site identity root target initial_stock raw_available target_occupied category energy_ready reason'.split())
RECORD_KEYS = set(IDENTITY) | set('support checked_snapshots checked_sites violations north_tickets north_dissolved events'.split())


def require(ok, message):
    if not ok:
        raise ValueError(message)


def same(actual, expected, message):
    require(json.dumps(actual, sort_keys=True, allow_nan=False) == json.dumps(expected, sort_keys=True, allow_nan=False), message)


def natural(value):
    return type(value) is int and value >= 0


def category(initial, raw, occupied):
    if initial == 0 and raw == 0 and not occupied:
        return 'no_initial_material'
    if initial == 1 and occupied and raw == 0:
        return 'occupied'
    if initial == 1 and not occupied and raw == 1:
        return 'available'
    return 'other'


def inventory(snapshot):
    require(type(snapshot) is dict, 'snapshot object')
    units, raw = snapshot['units'], snapshot['raw']
    require(type(units) is list and type(raw) is list and len(units) == len(raw) == 256, '256 snapshot sites')
    require(all(natural(n) for n in raw), 'nonnegative integer raw')
    require(all(u is None or type(u) is dict for u in units), 'unit objects')
    return [raw[site] + int(units[site] is not None) for site in range(256)]


def analyze_case(case, actors):
    require(type(actors) is dict and actors.get('genotype') in GENOTYPES, 'actor genotype')
    replayed = old.recount(case, actors['genotype'])
    same(replayed, actors, 'entire independently replayed 026 actor record')
    same([case[k] for k in IDENTITY[1:]], [actors[k] for k in IDENTITY[1:]], 'case actor identity')
    require(type(case['rows']) is list and len(case['rows']) == 32, '32 saved rows')
    require(type(actors['steps']) is list and len(actors['steps']) == 32, '32 actor lists')
    same(case['initial']['tick'], 0, 'initial tick')
    initial = inventory(case['initial'])
    result = {k: actors[k] for k in IDENTITY}
    result.update(support=[s for s,n in enumerate(initial) if n > 0], checked_snapshots=33,
                  checked_sites=8448, violations=[], north_tickets=dict(all=0, target=0),
                  north_dissolved=dict(all=0, target=0), events=[])
    snapshots = [case['initial']]
    for tick, row in enumerate(case['rows'], 1):
        same(row['tick'], tick, 'sequential row tick')
        same(row['physical']['tick'], tick, 'sequential physical tick')
        snapshots.append(row['physical'])
    for tick, snapshot in enumerate(snapshots):
        current = inventory(snapshot)
        for site, (expected, actual) in enumerate(zip(initial, current)):
            if expected != actual:
                result['violations'].append(dict(tick=tick, site=site, expected=expected, actual=actual))
    for tick, step in enumerate(actors['steps'], 1):
        require(type(step) is list, 'actor list')
        sites = []
        for actor in step:
            require(type(actor) is dict and natural(actor['site']) and actor['site'] < 256, 'actor site')
            same(actor['tick'], tick, 'actor tick')
            sites.append(actor['site'])
            if actor['direction'] != 3:
                continue
            scopes = ('all', 'target') if actor['root'] in (0, 1) else ('all',)
            for scope in scopes:
                result['north_tickets'][scope] += 1
            if actor['reason'] == 'dissolved':
                for scope in scopes:
                    result['north_dissolved'][scope] += 1
                continue
            target = actor['target']
            require(natural(target) and target < 256, 'target site')
            event = {k: actor[k] for k in ('tick', 'site', 'identity', 'root', 'target', 'raw_available', 'target_occupied', 'reason')}
            event.update(initial_stock=initial[target], energy_ready=actor['energy_interaction'] >= 16,
                         category=category(initial[target], actor['raw_available'], actor['target_occupied']))
            result['events'].append(event)
        require(sites == sorted(set(sites)), 'ordered unique actor sites')
    return result


def validate(record):
    require(type(record) is dict and set(record) == RECORD_KEYS, 'record schema')
    require(record['genotype'] in GENOTYPES and record['mode'] in MODES and type(record['exchange']) is bool and natural(record['seed']) and record['seed'] in range(120000, 120020), 'case identity types')
    same(record['checked_snapshots'], 33, '33 checked snapshots')
    same(record['checked_sites'], 8448, '8448 checked sites')
    support = record['support']
    require(type(support) is list and all(natural(s) and s < 256 for s in support) and support == sorted(set(support)), 'support sites')
    require(type(record['violations']) is list, 'violations list')
    positions = []
    for violation in record['violations']:
        require(type(violation) is dict and set(violation) == {'tick', 'site', 'expected', 'actual'}, 'violation schema')
        require(all(natural(n) for n in violation.values()), 'violation integers')
        require(violation['tick'] <= 32 and violation['site'] < 256 and violation['expected'] != violation['actual'], 'violation bounds and difference')
        positions.append((violation['tick'], violation['site']))
    require(positions == sorted(set(positions)), 'ordered unique violations')
    require(type(record['events']) is list, 'events list')
    positions = []
    for event in record['events']:
        require(type(event) is dict and set(event) == EVENT_KEYS, 'event schema')
        require(all(natural(event[k]) for k in ('tick', 'site', 'identity', 'root', 'target', 'initial_stock', 'raw_available')), 'event nonnegative integers')
        require(1 <= event['tick'] <= 32 and event['site'] < 256 and event['target'] < 256 and event['root'] in (0, 1, 2), 'event bounds')
        require(type(event['target_occupied']) is bool and type(event['energy_ready']) is bool, 'event boolean predicates')
        require(type(event['reason']) is str and event['reason'] in REASONS, 'surviving event reason')
        require(type(event['category']) is str and event['category'] in CATEGORIES, 'event category')
        same(event['category'], category(event['initial_stock'], event['raw_available'], event['target_occupied']), 'category definition')
        require((event['initial_stock'] > 0) == (event['target'] in support), 'event initial support')
        positions.append((event['tick'], event['site']))
    require(positions == sorted(set(positions)), 'ordered unique events')
    for key in ('north_tickets', 'north_dissolved'):
        require(type(record[key]) is dict and set(record[key]) == {'all', 'target'} and all(natural(n) for n in record[key].values()), 'scope count schema')
        require(record[key]['target'] <= record[key]['all'], 'target subset count')
    for scope in ('all', 'target'):
        proposals = sum(scope == 'all' or e['root'] in (0, 1) for e in record['events'])
        require(record['north_tickets'][scope] == record['north_dissolved'][scope] + proposals, 'tickets equal dissolved plus proposals')


def summarize(records):
    require(type(records) is list and len(records) == 240, '240 records')
    for record in records:
        validate(record)
    same([[r[k] for k in IDENTITY] for r in records], [list(key) for key in GRID], 'complete ordered grid')
    cells = []
    for offset in range(0, 240, 20):
        selected = records[offset:offset+20]
        cell = {k: selected[0][k] for k in IDENTITY[:3]}
        cell.update(n=20, checked_snapshots=sum(r['checked_snapshots'] for r in selected),
                    checked_sites=sum(r['checked_sites'] for r in selected),
                    violation_count=sum(len(r['violations']) for r in selected), scopes={})
        for scope in ('all', 'target'):
            events = [e for r in selected for e in r['events'] if scope == 'all' or e['root'] in (0, 1)]
            categories = {}
            for name in CATEGORIES:
                chosen = [e for e in events if e['category'] == name]
                categories[name] = dict(n=len(chosen), energy_ready=sum(e['energy_ready'] for e in chosen),
                                        reasons={reason: sum(e['reason'] == reason for e in chosen) for reason in REASONS})
            cell['scopes'][scope] = dict(north_tickets=sum(r['north_tickets'][scope] for r in selected),
                north_dissolved=sum(r['north_dissolved'][scope] for r in selected), north_proposals=len(events), categories=categories)
        cells.append(cell)
    return cells


def write_proof(path, proof, budget):
    payload = json.dumps(proof, indent=2, allow_nan=False) + '\n'
    budget(len(payload.encode()))
    created = False
    try:
        with path.open('x') as stream:
            created = True
            stream.write(payload)
        budget()
    except BaseException:
        if created:
            path.unlink()
        raise


def main():
    from scripts.material_support_inputs import bindings, read, digest, input_paths, source_cases
    root = OUTPUT
    proof_path = root / 'independent-verification.json'
    require(not proof_path.exists(), 'proof already exists')
    started = monotonic()
    names = ('metadata.json', 'records.json', 'summary.json')
    before = {}; input_before = {}; errors = {}; paths = []

    def snapshot(mapping, failures):
        hashes = {}
        for name, path in mapping.items():
            try:
                hashes[name] = digest(path)
            except Exception as error:
                failures[name] = f'{type(error).__name__}: {error}'
        return hashes

    def budget(extra=0):
        require(monotonic() - started < 300, 'verification time budget')
        require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) + extra < 67108864, 'verification storage budget')

    try:
        before = snapshot({n: root/n for n in names}, errors)
        paths = input_paths(errors)
        input_before = snapshot({p: Path(p) for p in paths}, errors)
        bound = bindings()
        require(type(bound) is dict and len(bound) == 401, '401 bound inputs')
        same(input_before, bound, 'readable input inventory')
        require(not errors, 'input inventory and read errors')
        same(digest(Path(__file__)), bound['scripts/verify_v4_material_support.py'], 'running verifier binding')
        meta = read(root/'metadata.json')
        for key, value in dict(status='complete', planned_cases=240, completed_cases=240, saved_steps=7680,
                checked_snapshots=7920, checked_sites=2027520, new_simulation_steps=0, new_environment_sources=0,
                reused_environment_sources=20, new_independent_initial_worlds=0, time_limit_seconds=300,
                storage_limit_bytes=67108864).items():
            same(meta[key], value, 'metadata ' + key)
        require(type(meta['git_commit']) is str and len(meta['git_commit']) == 40 and all(c in '0123456789abcdef' for c in meta['git_commit']), 'recorded commit')
        require(type(meta['elapsed_seconds']) in (float, int) and math.isfinite(meta['elapsed_seconds']) and 0 <= meta['elapsed_seconds'] < 300, 'analysis time budget')
        same(meta['input_paths'], paths, 'metadata input paths')
        same(meta['input_sha256'], bound, 'before bindings')
        same(meta['input_sha256_after'], bound, 'after bindings')
        for key in ('input_inventory_errors', 'input_read_errors_before'):
            if key in meta:
                same(meta[key], {}, 'metadata ' + key)
        same(meta['output_sha256'], {n: before[n] for n in names[1:]}, 'output hashes')
        require({p.name for p in root.iterdir()} == set(names) and all((root/n).is_file() and not (root/n).is_symlink() for n in names), 'exclusive output inventory')
        saved = read(root/'records.json')
        require(type(saved) is list and len(saved) == 240, '240 saved records')
        actors = read(Path('data/v4-study-026/records.json'))
        require(type(actors) is list and len(actors) == 240, '240 bound actor records')
        sources = list(source_cases())
        require(len(sources) == 240, '240 sources')
        records = []
        for index, (genotype, path) in enumerate(sources):
            budget()
            case = read(path)
            same([genotype, case['mode'], case['exchange'], case['seed']], list(GRID[index]), 'source order')
            same([actors[index][k] for k in IDENTITY], list(GRID[index]), 'actor order')
            record = analyze_case(case, actors[index])
            same(saved[index], record, 'entire independent material support record')
            records.append(record)
        same(read(root/'summary.json'), summarize(records), 'all twelve cells')
        same(bindings(), bound, 'inputs unchanged')
        same({n: digest(root/n) for n in names}, before, 'outputs unchanged')
        require({p.name for p in root.iterdir()} == set(names), 'exclusive output inventory after verification')
        proof = dict(status='verified', cases=240, saved_steps=7680, checked_snapshots=7920, checked_sites=2027520,
            input_files=401, new_simulation_steps=0, new_environment_sources=0, reused_environment_sources=20,
            new_independent_initial_worlds=0, input_paths=paths, input_sha256=input_before, input_sha256_after=bound,
            files_sha256=before, verifier_sha256=digest(Path(__file__)), elapsed_seconds=monotonic()-started,
            scope='independent full dictionary physics replay, all site inventories, all surviving north targets and twelve summary cells')
        write_proof(proof_path, proof, budget)
        print('verified 240 cases, 7680 saved steps, 7920 snapshots, 2027520 sites and 401 bindings')
    except BaseException as error:
        failure = root/'verification-failure.json'
        if root.is_dir() and not failure.exists():
            after_errors = {}
            evidence = dict(status='failed', error=f'{type(error).__name__}: {error}',
                input_paths=paths, input_sha256=input_before, files_sha256_before=before,
                input_sha256_after=snapshot({p: Path(p) for p in paths}, after_errors),
                files_sha256_after=snapshot({n: root/n for n in names}, after_errors),
                read_errors_before=errors, read_errors_after=after_errors,
                completed_cases=len(records) if 'records' in locals() else 0,
                elapsed_seconds=monotonic()-started)
            with failure.open('x') as stream:
                stream.write(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
        raise


if __name__ == '__main__':
    main()
