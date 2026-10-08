"""Independent Study029 dictionary physics, identities and energy recount."""
from copy import deepcopy
import json
import math
from pathlib import Path
from time import monotonic

from bitgenesis.v4.exchange_branch_audit import physical_step
from bitgenesis.v4.structure_audit import reconstruct
from scripts.verify_v4_north_energy import KEYS, validate_selection

OUTPUT = Path('data/v4-study-029')
CONFIG = dict(width=16, height=16, capacity=64, leak=1, bond_cost=1,
              threshold=16, construction_cost=4, copy_cost=1, mutation_per_thousand=0)
TOTALS = ('steps', 'proposed', 'accepted', 'leakage', 'bond_cost', 'exchange_in',
          'exchange_out', 'formation_spent', 'offspring_energy', 'final_energy')
ROW_KEYS = {'tick', 'energy_before', 'proposed', 'accepted', 'leakage', 'bond_cost',
            'exchange_in', 'exchange_out', 'energy_interaction', 'formation_spent',
            'offspring_energy', 'energy_after', 'dissolved'}
RECORD_KEYS = {'selection', 'child_identity', 'child_site', 'birth_tick', 'death_tick',
               'initial_energy', 'rows', 'totals'}
GENOTYPES = ('homogeneous', 'heterogeneous')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(actual, expected, message):
    # JSON equality must not silently equate bool and int.
    require(type(actual) is type(expected), message + ' type')
    if isinstance(expected, dict):
        require(actual.keys() == expected.keys(), message + ' keys')
        for key in expected:
            same(actual[key], expected[key], message + '.' + str(key))
    elif isinstance(expected, list):
        require(len(actual) == len(expected), message + ' length')
        for index, value in enumerate(expected):
            same(actual[index], value, message + '[' + str(index) + ']')
    else:
        require(actual == expected, message)


def extract_row(original, physical, site, dissolved):
    flow = physical['driven']['inputs'][site]
    interaction = physical['driven']['interaction']
    formed = [p for p in physical['material']['proposals']
              if p['source'] == site and p['reason'] == 'formed']
    result = dict(tick=physical['tick'], energy_before=original[site]['energy'],
        proposed=flow['proposed'], accepted=flow['accepted'], leakage=flow['leakage'],
        bond_cost=sum(site in edge for edge in interaction['bonds']),
        exchange_in=sum(t['amount'] for t in interaction['transfers'] if t['recipient'] == site),
        exchange_out=sum(t['amount'] for t in interaction['transfers'] if t['donor'] == site),
        energy_interaction=physical['interaction_units'][site]['energy'],
        formation_spent=sum(p['construction_cost'] + p['copy_cost'] for p in formed),
        offspring_energy=sum(p['child_energy'] for p in formed),
        energy_after=0 if dissolved else physical['units'][site]['energy'], dissolved=dissolved)
    validate_row(result)
    return result


def validate_row(row):
    require(type(row) is dict and set(row) == ROW_KEYS, 'row schema')
    require(type(row['dissolved']) is bool, 'dissolution boolean')
    require(all(type(v) is int and v >= 0 for k, v in row.items() if k != 'dissolved'), 'row nonnegative integers')
    require(row['energy_before'] > 0 and row['accepted'] <= row['proposed'], 'living child and accepted input')
    same(row['energy_interaction'], row['energy_before'] + row['accepted'] - row['leakage']
         - row['bond_cost'] + row['exchange_in'] - row['exchange_out'], 'interaction ledger')
    same(row['energy_after'], row['energy_interaction'] - row['formation_spent'] - row['offspring_energy'], 'formation ledger')
    if row['dissolved']:
        same(row['energy_interaction'], 0, 'death interaction energy')
        same(row['energy_after'], 0, 'dead identity energy')
    else:
        require(row['energy_after'] > 0, 'living final child')


def totals(rows):
    result = {key: sum(row[key] for row in rows) for key in TOTALS[1:-1]}
    return dict(steps=len(rows), **result, final_energy=rows[-1]['energy_after'])


def validate_record(record):
    require(type(record) is dict and set(record) == RECORD_KEYS, 'record schema')
    s = record['selection']
    require(type(s) is dict and set(s) == set(KEYS), 'selection schema')
    require(s['genotype'] in GENOTYPES and s['mode'] == 'random-both' and type(s['exchange']) is bool, 'selection cell')
    require(all(type(s[k]) is int for k in KEYS[2:] if k != 'exchange'), 'selection integers')
    for key in ('child_identity', 'child_site', 'birth_tick', 'death_tick', 'initial_energy'):
        require(type(record[key]) is int and record[key] >= 0, 'record integer ' + key)
    same(record['birth_tick'], s['tick'], 'birth tick')
    require(record['birth_tick'] < record['death_tick'] <= 32 and record['child_site'] < 256, 'child lifetime and site')
    same(record['initial_energy'], 5, 'child initial energy')
    rows = record['rows']
    require(type(rows) is list and bool(rows), 'child rows')
    energy = 5
    for offset, row in enumerate(rows, record['birth_tick'] + 1):
        validate_row(row)
        same(row['tick'], offset, 'consecutive child ticks')
        same(row['energy_before'], energy, 'child energy continuity')
        same(row['dissolved'], offset == record['death_tick'], 'death exactly last row')
        energy = row['energy_after']
    same(rows[-1]['tick'], record['death_tick'], 'complete child lifetime')
    same(record['totals'], totals(rows), 'child totals')
    t = record['totals']
    same(t['steps'], record['death_tick'] - record['birth_tick'], 'lifetime steps')
    same(5 + t['accepted'] - t['leakage'] - t['bond_cost'] + t['exchange_in']
         - t['exchange_out'] - t['formation_spent'] - t['offspring_energy'], t['final_energy'], 'lifetime ledger')
    same(t['final_energy'], 0, 'all children dissolved')


def recount(branch, *, on_step=None):
    initial = branch['initial']
    units, raw = deepcopy(initial['units']), deepcopy(initial['raw'])
    ids, parents = initial['site_ids'].copy(), initial['parents'].copy()
    child = initial['injected_child']
    require(type(child) is int and 0 <= child < len(parents), 'child identity')
    require(len(ids) == len(units) == len(raw) == 256, 'world arrays')
    living = [i for i in ids if i is not None]
    require(all(type(i) is int and 0 <= i < len(parents) for i in living) and len(set(living)) == len(living), 'unique living identities')
    require(all(parent is None or type(parent) is int and 0 <= parent < i for i, parent in enumerate(parents)), 'plain ancestry')
    require(all((identity is None) == (unit is None) for identity, unit in zip(ids, units)), 'initial occupancy')
    require(ids.count(child) == 1, 'initial injected identity')
    site = ids.index(child)
    selection = branch['selection']
    require(type(selection['identity']) is int and 0 <= selection['identity'] < len(parents), 'selected parent identity')
    same(parents[child], selection['identity'], 'injected child selected parent')
    same(ids[selection['site']], selection['identity'], 'selected parent site')
    ancestor = selection['identity']
    while parents[ancestor] is not None:
        ancestor = parents[ancestor]
    same(ancestor, selection['root'], 'selected parent founder root')
    same(units[site]['energy'], 5, 'injected energy')
    same(initial['tick'], branch['selection']['tick'], 'initial birth tick')
    same(initial['observation'], reconstruct(units, ids, 16, 16, 'final'), 'initial observation')
    records = []
    death = None
    same(len(branch['rows']), 32 - initial['tick'], 'entire saved continuation')
    for tick, saved in enumerate(branch['rows'], initial['tick'] + 1):
        same(saved['tick'], tick, 'saved tick')
        physical = physical_step(units, raw, CONFIG, saved['physical'], branch['selection']['exchange'])
        same(physical['tick'], tick, 'physical tick')
        same(saved['physical'], physical, 'entire independently replayed physical')
        if on_step is not None:
            on_step()
        old = ids.copy()
        alive = child in old
        if alive:
            same(old[site], child, 'child fixed site')
        for dissolved_site in physical['material']['dissolved']:
            require(ids[dissolved_site] is not None, 'dissolved identity exists')
            if ids[dissolved_site] == child:
                require(death is None, 'single child death')
                death = tick
            ids[dissolved_site] = None
        for proposal in physical['material']['proposals']:
            if proposal['reason'] == 'formed':
                source, target = proposal['source'], proposal['target']
                require(old[source] is not None and ids[target] is None, 'parent identity and vacancy')
                ids[target] = len(parents)
                parents.append(old[source])
        if alive:
            records.append(extract_row(units, physical, site, death == tick))
        same(saved['site_ids'], ids, 'plain step identities')
        same(saved['observation'], reconstruct(physical['units'], ids, 16, 16, 'final'), 'step observation')
        units, raw = physical['units'], physical['raw']
    same(branch['final'], dict(tick=32, units=units, raw=raw, site_ids=ids, parents=parents), 'final plain state')
    require(death is not None and child not in ids, 'observed child death')
    same(branch['child_fate']['identity'], child, 'saved child identity')
    same(branch['child_fate']['birth_tick'], initial['tick'], 'saved child birth')
    same(branch['child_fate']['death_tick'], death, 'saved child death')
    same(branch['child_fate']['alive_final'], False, 'saved dead child')
    result = dict(selection=deepcopy(branch['selection']), child_identity=child, child_site=site,
        birth_tick=initial['tick'], death_tick=death, initial_energy=5, rows=records, totals=totals(records))
    validate_record(result)
    return result


def aggregate(records):
    require(type(records) is list, 'record list')
    validate_selection([r['selection'] for r in records])
    for record in records:
        validate_record(record)
    cells = []
    for genotype in GENOTYPES:
        for exchange in (False, True):
            group = [r for r in records if r['selection']['genotype'] == genotype and r['selection']['exchange'] == exchange]
            cells.append(dict(genotype=genotype, exchange=exchange, n=len(group),
                totals={key: sum(r['totals'][key] for r in group) for key in TOTALS},
                zero_accepted=sum(r['totals']['accepted'] == 0 for r in group),
                received_exchange=sum(r['totals']['exchange_in'] > 0 for r in group),
                paid_bond=sum(r['totals']['bond_cost'] > 0 for r in group)))
    same([c['totals']['steps'] for c in cells], [64, 26, 129, 49], 'fixed four cell child steps')
    same(sum(r['totals']['steps'] for r in records), 268, '268 child steps')
    pair_keys = KEYS[1:]
    by_key = {}
    for index, record in enumerate(records):
        key = tuple(record['selection'][k] for k in pair_keys)
        genotype = record['selection']['genotype']
        require(genotype not in by_key.setdefault(key, {}), 'unique paired record')
        by_key[key][genotype] = index
    require(len(by_key) == 26 and all(set(v) == set(GENOTYPES) for v in by_key.values()), '26 complete pairs')
    pairs = []
    for index, record in enumerate(records):
        if record['selection']['genotype'] != 'homogeneous':
            continue
        selection = {k: record['selection'][k] for k in pair_keys}
        other_index = by_key[tuple(selection.values())]['heterogeneous']
        other = records[other_index]
        pairs.append(dict(selection=selection, homogeneous_index=index, heterogeneous_index=other_index,
            delta={k: other['totals'][k] - record['totals'][k] for k in TOTALS}))
    return dict(cells=cells, pairs=pairs)


def check_budget(root, started, extra=0):
    require(monotonic() - started < 300, 'verification time budget')
    require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) + extra < 33554432, 'verification storage budget')


def main():
    from scripts.child_energy_inputs import bindings, read, digest, input_paths, source_cases
    root = OUTPUT
    proof_path = root / 'independent-verification.json'
    require(not proof_path.exists(), 'proof already exists')
    started = monotonic()
    paths, input_before, before, errors = [], {}, {}, {}
    completed = steps = child_steps = 0
    names = ('metadata.json', 'records.json', 'summary.json')

    def snapshot(mapping, failures):
        result = {}
        for name, path in mapping.items():
            try:
                result[name] = digest(path)
            except Exception as error:
                failures[name] = f'{type(error).__name__}: {error}'
        return result

    def budget(extra=0):
        check_budget(root, started, extra)

    try:
        paths = input_paths(errors)
        input_before = snapshot({p: Path(p) for p in paths}, errors)
        before = snapshot({n: root / n for n in names}, errors)
        bound = bindings()
        same(len(bound), 479, '479 bound inputs')
        same(paths, sorted(bound), 'complete inventory')
        same(input_before, bound, 'readable inputs')
        same(digest(Path(__file__)), bound['scripts/verify_v4_child_energy.py'], 'running verifier')
        meta = read(root / 'metadata.json')
        fixed = dict(status='complete', planned_branches=52, completed_branches=52,
            saved_world_steps=996, child_steps=268, new_full_world_steps=0, new_phase_transitions=0,
            new_environment_sources=0, reused_environment_sources=20, selected_environment_sources=11,
            new_independent_initial_worlds=0, time_limit_seconds=300, storage_limit_bytes=33554432)
        expected = set(fixed) | {'git_commit', 'elapsed_seconds', 'input_paths', 'input_sha256', 'input_sha256_after', 'output_sha256'}
        optional = {'input_inventory_errors', 'input_read_errors_before'}
        require(expected <= set(meta) <= expected | optional, 'metadata schema')
        for key in optional & set(meta):
            same(meta[key], {}, 'successful ' + key)
        for key, value in fixed.items():
            same(meta[key], value, 'metadata ' + key)
        commit = meta['git_commit']
        require(type(commit) is str and len(commit) == 40 and all(c in '0123456789abcdef' for c in commit), 'recorded commit')
        elapsed = meta['elapsed_seconds']
        require(type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed < 300, 'run time budget')
        same(meta['input_paths'], paths, 'metadata paths')
        same(meta['input_sha256'], bound, 'before bindings')
        same(meta['input_sha256_after'], bound, 'after bindings')
        same(meta['output_sha256'], {n: before[n] for n in names[1:]}, 'output hashes')
        require({p.name for p in root.iterdir()} == set(names), 'exclusive output inventory')
        sources = list(source_cases())
        same(len(sources), 52, '52 source cases')
        same([p.name for p in sources], [f'branch-{i:03d}.json' for i in range(52)], 'source case order')
        saved = read(root / 'records.json')
        require(type(saved) is list and len(saved) == 52, '52 saved records')
        records = []

        def counted_step():
            nonlocal steps
            steps += 1
            budget()

        for index, source in enumerate(sources):
            budget()
            result = recount(read(source), on_step=counted_step)
            same(saved[index], result, 'entire independent record')
            records.append(result)
            completed += 1
            child_steps += len(result['rows'])
        same(steps, 996, '996 replayed saved world steps')
        same(child_steps, 268, '268 recounted child steps')
        same(read(root / 'summary.json'), aggregate(records), 'independent summary and pairs')
        same(bindings(), bound, 'inputs unchanged')
        after_errors = {}
        same(snapshot({n: root / n for n in names}, after_errors), before, 'outputs unchanged')
        same(after_errors, {}, 'readable outputs after')
        require({p.name for p in root.iterdir()} == set(names), 'exclusive output inventory after')
        proof = dict(status='verified', input_files=479, branches=52, saved_world_steps=steps,
            child_steps=child_steps, pairs=26, new_full_world_steps=0, new_phase_transitions=0,
            new_environment_sources=0, reused_environment_sources=20, selected_environment_sources=11,
            new_independent_initial_worlds=0, files_sha256=before,
            verifier_sha256=digest(Path(__file__)), input_paths=paths, input_sha256=input_before,
            input_sha256_after=bound, elapsed_seconds=monotonic()-started, time_limit_seconds=300,
            storage_limit_bytes=33554432,
            scope='independent saved dictionary physics, plain identities and parents, child energy rows and 26 pairs')
        payload = json.dumps(proof, indent=2, allow_nan=False) + '\n'
        budget(len(payload.encode()))
        with proof_path.open('x') as stream:
            stream.write(payload)
        budget()
        print('verified 52 child lifetimes, 996 saved world steps, 268 child steps, 26 pairs and 479 inputs')
    except BaseException as error:
        failure = root / 'verification-failure.json'
        if root.is_dir() and not failure.exists():
            after_errors = {}
            evidence = dict(status='failed', error=f'{type(error).__name__}: {error}',
                completed_branches=completed, saved_world_steps=steps, child_steps=child_steps,
                new_full_world_steps=0, input_paths=paths, input_sha256=input_before,
                files_sha256_before=before,
                input_sha256_after=snapshot({p: Path(p) for p in paths}, after_errors),
                files_sha256_after=snapshot({n: root / n for n in names}, after_errors),
                read_errors_before=errors, read_errors_after=after_errors)
            with failure.open('x') as stream:
                stream.write(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
        raise


if __name__ == '__main__':
    main()
