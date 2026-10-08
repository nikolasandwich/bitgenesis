"""Audit saved local inventory and classify the complete Study026 north ledger."""
from pathlib import Path
import subprocess
import time

GENOTYPES = ('homogeneous', 'heterogeneous')
MODES = ('random-direction', 'random-feed', 'random-both')
CATEGORIES = ('no_initial_material', 'occupied', 'available', 'other')
REASONS = ('energy', 'occupied', 'raw_material', 'collision', 'formed')
GRID = [(g, m, e, s) for g in GENOTYPES for m in MODES for e in (False, True) for s in range(120000, 120020)]
OUTPUT = Path('data/v4-study-033')
EVENT_KEYS = {'tick', 'site', 'identity', 'root', 'target', 'initial_stock', 'raw_available', 'target_occupied', 'category', 'energy_ready', 'reason'}
RECORD_KEYS = {'genotype', 'mode', 'exchange', 'seed', 'support', 'checked_snapshots', 'checked_sites', 'violations', 'north_tickets', 'north_dissolved', 'events'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, minimum=0, maximum=None):
    return type(value) is int and value >= minimum and (maximum is None or value <= maximum)


def identity(record):
    require(type(record) is dict and type(record['exchange']) is bool and integer(record['seed']), 'strict case identity')
    key = tuple(record[k] for k in ('genotype', 'mode', 'exchange', 'seed'))
    require(key in GRID, 'case grid identity')
    return key


def category(stock, raw, occupied):
    if stock == 0 and raw == 0 and not occupied:
        return 'no_initial_material'
    if stock == 1 and occupied and raw == 0:
        return 'occupied'
    if stock == 1 and not occupied and raw == 1:
        return 'available'
    return 'other'


def inventory(snapshot):
    raw, units, ids = (snapshot[k] for k in ('raw', 'units', 'site_ids'))
    require(all(type(v) is list and len(v) == 256 for v in (raw, units, ids)), '256 fixed sites')
    require(all(integer(n) for n in raw), 'nonnegative integer raw')
    seen = set()
    for unit, ident in zip(units, ids):
        require((unit is None) == (ident is None), 'identity occupancy')
        if unit is not None:
            require(type(unit) is dict and integer(ident) and ident not in seen, 'unique occupied identity')
            seen.add(ident)
    return [r + int(u is not None) for r, u in zip(raw, units)]


def analyze_case(case, actors):
    key = identity(actors)
    require(type(case['exchange']) is bool and integer(case['seed']) and
            (case['mode'], case['exchange'], case['seed']) == key[1:], 'case actors identity match')
    require(type(case['rows']) is list and type(actors['steps']) is list and len(case['rows']) == len(actors['steps']) == 32, '32 saved steps')
    initial = inventory(case['initial'])
    parents = case['final']['parents']; roots = []
    for i, parent in enumerate(parents):
        require((i < 3 and parent is None) or (i >= 3 and integer(parent, 0, i-1)), 'root ancestry')
        roots.append(i if parent is None else roots[parent])
    record = dict(zip(('genotype', 'mode', 'exchange', 'seed'), key))
    record.update(support=[s for s, n in enumerate(initial) if n > 0], checked_snapshots=33, checked_sites=8448,
                  violations=[], north_tickets=dict(all=0, target=0), north_dissolved=dict(all=0, target=0), events=[])
    previous = case['initial']
    for tick, (row, step) in enumerate(zip(case['rows'], actors['steps']), 1):
        p = row['physical']
        require(integer(row['tick']) and integer(p['tick']) and row['tick'] == p['tick'] == tick, 'ordered snapshot ticks')
        current = dict(p, site_ids=row['site_ids'])
        actual = inventory(current)
        record['violations'].extend(dict(tick=tick, site=s, expected=n, actual=actual[s]) for s, n in enumerate(initial) if n != actual[s])
        require(type(step) is list and [a['site'] for a in step] == [s for s, ident in enumerate(previous['site_ids']) if ident is not None], 'complete ordered actor coverage')
        for a in step:
            require(all(integer(a[k], 0, 255) for k in ('site', 'target')) and integer(a['tick'], 1, 32) and a['tick'] == tick, 'actor position and tick')
            require(integer(a['identity'], 0, len(roots)-1) and integer(a['root'], 0, 2) and a['identity'] == previous['site_ids'][a['site']] and a['root'] == roots[a['identity']], 'actor identity root')
            require(integer(a['direction'], 0, 3) and integer(a['energy_interaction'], 0, 64) and integer(a['raw_available']) and type(a['target_occupied']) is bool and a['reason'] in (*REASONS, 'dissolved'), 'strict actor state')
            site = a['site']; x, y = site % 16, site // 16
            target = (16*y+(x+1)%16, 16*y+(x-1)%16, 16*((y+1)%16)+x, 16*((y-1)%16)+x)[a['direction']]
            require(a['target'] == target, 'actor target geometry')
            if a['direction'] != 3:
                continue
            for scope in ('all', 'target') if a['root'] in (0, 1) else ('all',):
                record['north_tickets'][scope] += 1
                record['north_dissolved'][scope] += int(a['reason'] == 'dissolved')
            if a['reason'] == 'dissolved':
                continue
            event = {k: a[k] for k in ('tick', 'site', 'identity', 'root', 'target', 'raw_available', 'target_occupied', 'reason')}
            event.update(initial_stock=initial[target], category=category(initial[target], a['raw_available'], a['target_occupied']), energy_ready=a['energy_interaction'] >= 16)
            record['events'].append(event)
        previous = current
    # The final stored state is a duplicate of the last saved snapshot.
    require(all(case['final'][k] == previous[k] for k in ('units', 'raw', 'site_ids')), 'final snapshot match')
    return record


def validate_record(r):
    require(type(r) is dict and set(r) == RECORD_KEYS, 'record schema')
    identity(r)
    require(integer(r['checked_snapshots']) and r['checked_snapshots'] == 33 and integer(r['checked_sites']) and r['checked_sites'] == 8448, 'fixed audit counts')
    require(type(r['support']) is list and all(integer(s, 0, 255) for s in r['support']) and r['support'] == sorted(set(r['support'])), 'support schema')
    require(type(r['violations']) is list, 'violations list')
    order = []
    for v in r['violations']:
        require(type(v) is dict and set(v) == {'tick', 'site', 'expected', 'actual'} and integer(v['tick'], 0, 32) and integer(v['site'], 0, 255) and integer(v['expected']) and integer(v['actual']) and v['expected'] != v['actual'], 'violation schema')
        require((v['expected'] > 0) == (v['site'] in r['support']), 'violation initial support')
        order.append((v['tick'], v['site']))
    require(order == sorted(set(order)), 'ordered unique violations')
    require(type(r['events']) is list, 'events list')
    order = []
    for e in r['events']:
        require(type(e) is dict and set(e) == EVENT_KEYS, 'event schema')
        require(integer(e['tick'], 1, 32) and integer(e['site'], 0, 255) and integer(e['target'], 0, 255) and integer(e['identity']) and integer(e['root'], 0, 2) and integer(e['initial_stock']) and integer(e['raw_available']), 'event integer state')
        require(type(e['energy_ready']) is bool and type(e['target_occupied']) is bool and e['reason'] in REASONS and e['category'] in CATEGORIES, 'event enum/bool state')
        require(e['target'] == (e['site']-16)%256 and (e['initial_stock'] > 0) == (e['target'] in r['support']) and e['category'] == category(e['initial_stock'], e['raw_available'], e['target_occupied']), 'event classification')
        order.append((e['tick'], e['site']))
    require(order == sorted(set(order)), 'ordered unique events')
    for field in ('north_tickets', 'north_dissolved'):
        require(type(r[field]) is dict and set(r[field]) == {'all', 'target'} and all(integer(n) for n in r[field].values()) and r[field]['target'] <= r[field]['all'], 'scope counts')
    for scope in ('all', 'target'):
        count = sum(scope == 'all' or e['root'] in (0, 1) for e in r['events'])
        require(r['north_tickets'][scope] - r['north_dissolved'][scope] == count, 'ticket event accounting')


def summarize(records):
    require(type(records) is list and [identity(r) for r in records] == GRID, 'complete ordered240 grid')
    for r in records:
        validate_record(r)
    result = []
    for offset in range(0, 240, 20):
        group = records[offset:offset+20]
        item = {k: group[0][k] for k in ('genotype', 'mode', 'exchange')}
        item.update(n=20, checked_snapshots=sum(r['checked_snapshots'] for r in group), checked_sites=sum(r['checked_sites'] for r in group), violation_count=sum(len(r['violations']) for r in group), scopes={})
        for scope in ('all', 'target'):
            events = [e for r in group for e in r['events'] if scope == 'all' or e['root'] in (0, 1)]
            categories = {}
            for name in CATEGORIES:
                selected = [e for e in events if e['category'] == name]
                categories[name] = dict(n=len(selected), energy_ready=sum(e['energy_ready'] for e in selected), reasons={reason: sum(e['reason'] == reason for e in selected) for reason in REASONS})
            item['scopes'][scope] = dict(north_tickets=sum(r['north_tickets'][scope] for r in group), north_dissolved=sum(r['north_dissolved'][scope] for r in group), north_proposals=len(events), categories=categories)
        result.append(item)
    return result


def main():
    from scripts.material_support_inputs import bindings, source_cases, input_paths, read, save, digest
    require(not subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip(), 'clean launch')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic(); records = []; inventory = []
    meta = dict(status='running', planned_cases=240, completed_cases=0, saved_steps=0, checked_snapshots=0, checked_sites=0, new_simulation_steps=0,
                new_environment_sources=0, reused_environment_sources=20, new_independent_initial_worlds=0,
                time_limit_seconds=300, storage_limit_bytes=67108864,
                git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip())
    def budget():
        require(time.monotonic()-started < 300 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file()) < 67108864, 'bounded execution')
    def hashes():
        return {str(p.relative_to(OUTPUT)): digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p.name != 'metadata.json'}
    def input_hashes(error_key):
        values = {}; meta[error_key] = {}
        for path in inventory:
            try:
                values[path] = digest(path)
            except BaseException as exc:
                meta[error_key][path] = repr(exc)
        return values
    try:
        meta['input_inventory_errors'] = {}
        inventory = input_paths(meta['input_inventory_errors']); meta['input_paths'] = inventory
        meta['input_sha256'] = input_hashes('input_read_errors_before')
        save(OUTPUT/'metadata.json', meta); save(OUTPUT/'records.json', records)
        before = bindings(); require(len(before) == 401 and before == meta['input_sha256'], 'validated initial inputs')
        ledger = read('data/v4-study-026/records.json')
        require(type(ledger) is list and [identity(a) for a in ledger] == GRID, 'complete ordered026 actors')
        sources = list(source_cases())
        require(len(sources) == 240, 'complete source cases')
        for (genotype, path), actors in zip(sources, ledger):
            budget()
            require(genotype == actors['genotype'], 'source genotype')
            records.append(analyze_case(read(path), actors))
            meta.update(completed_cases=len(records), saved_steps=32*len(records), checked_snapshots=33*len(records), checked_sites=8448*len(records), elapsed_seconds=time.monotonic()-started)
            save(OUTPUT/'records.json', records); save(OUTPUT/'metadata.json', meta)
        save(OUTPUT/'summary.json', summarize(records))
        meta['input_sha256_after'] = bindings(); require(before == meta['input_sha256_after'], 'unchanged inputs')
        meta.update(status='complete', elapsed_seconds=time.monotonic()-started, output_sha256=hashes())
        budget(); save(OUTPUT/'metadata.json', meta); budget()
    except BaseException as exc:
        meta.update(status='failed', error=repr(exc), elapsed_seconds=time.monotonic()-started)
        try:
            meta['input_sha256_after'] = bindings()
            if meta.get('input_sha256') != meta['input_sha256_after']:
                meta['finalization_error'] = 'inputs changed during failure'
        except BaseException as err:
            meta['finalization_error'] = repr(err); meta['input_sha256_after'] = input_hashes('input_read_errors')
        try:
            meta['output_sha256'] = hashes()
        except BaseException as err:
            meta['output_hash_error'] = repr(err)
        save(OUTPUT/'metadata.json', meta)
        raise


if __name__ == '__main__':
    main()
