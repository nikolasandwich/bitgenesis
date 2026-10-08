"""Independent dictionary reconstruction of the fixed Study027 phase intervention."""
from copy import deepcopy
import json
import math
from pathlib import Path
from time import monotonic
from bitgenesis.v4.growing_audit import reconstruct_material
from scripts import verify_v4_north_opportunities as prior

OUTPUT = Path('data/v4-study-027')
KEYS = ('genotype', 'mode', 'seed', 'exchange', 'tick', 'site', 'identity', 'root', 'energy_before')
REASONS = ('energy', 'occupied', 'raw_material', 'collision', 'formed')
require, same = prior.require, prior.same


def select(records):
    prior.aggregate(records)
    selected = []
    for r in records:
        for actors in r['steps']:
            for a in actors:
                if (a['root'] in (0, 1) and a['direction'] == 3 and a['reason'] != 'dissolved'
                        and 0 < a['energy_interaction'] < 16 and not a['target_occupied'] and a['raw_available'] >= 1):
                    selected.append(dict(**{k: r[k] for k in KEYS[:4]}, **{k: a[k] for k in KEYS[4:-1]}, energy_before=a['energy_interaction']))
    validate_selection(selected)
    return selected


def validate_selection(selected):
    require(len(selected) == 52, '52 fixed probes')
    order = []
    for s in selected:
        require(set(s) == set(KEYS), 'selection schema')
        require(s['genotype'] in prior.GENOTYPES and s['mode'] == 'random-both' and type(s['exchange']) is bool, 'selection cell')
        require(all(type(s[k]) is int for k in KEYS[2:] if k != 'exchange'), 'selection integers')
        require(s['seed'] in range(120000, 120020) and 1 <= s['tick'] <= 32 and 0 <= s['site'] < 256 and s['identity'] >= 0 and s['root'] in (0, 1) and 0 < s['energy_before'] < 16, 'selection bounds')
        order.append((prior.GENOTYPES.index(s['genotype']), s['exchange'], s['seed'], s['tick'], s['site']))
    require(order == sorted(set(order)), 'ordered unique probes')
    same([sum(s['genotype'] == g and s['exchange'] == e for s in selected) for g in prior.GENOTYPES for e in (False, True)], [21, 5, 21, 5], 'fixed four cell counts')


def phase(initial):
    require(set(initial) == {'units', 'raw', 'directions', 'mutation_tickets'}, 'initial schema')
    require(all(type(initial[k]) is list and len(initial[k]) == 256 for k in initial), 'complete phase arrays')
    require(all(type(n) is int and n >= 0 for n in initial['raw']), 'raw amounts')
    require(all(type(d) is int and 0 <= d < 4 for d in initial['directions']), 'direction tickets')
    require(all(type(t) is list and len(t) == 3 and all(type(n) is int for n in t)
                and 0 <= t[0] < 1000 and 0 <= t[1] < 4 and 1 <= t[2] < 4 for t in initial['mutation_tickets']), 'mutation tickets')
    for u in initial['units']:
        if u is not None:
            require(type(u) is dict and set(u) == {'material', 'energy', 'program'}, 'unit schema')
            require(type(u['energy']) is int and 0 <= u['energy'] <= 64 and type(u['material']) is int and 0 <= u['material'] < 4, 'unit bounds')
            require(type(u['program']) is list and len(u['program']) == 4 and all(type(n) is int and 0 <= n < 4 for n in u['program']), 'unit program')
    original = deepcopy(initial['units'])
    plain = [None if u is None else dict(material=u['material'], energy=u['energy']) for u in original]
    units, raw, material = reconstruct_material(plain, initial['raw'], 16, 16, initial['directions'], 16, 5)
    programs = {i: list(u['program']) for i, u in enumerate(original) if u is not None}
    births = 0
    for p in material['proposals']:
        if p['reason'] != 'formed':
            continue
        source, target = p['source'], p['target']
        parent = original[source]
        child = list(parent['program'])
        expressed = parent['program'][initial['directions'][source]]
        programs[target] = child
        units[target]['material'] = expressed
        p.update(parent_material=parent['material'], material=expressed, parent_program=list(parent['program']), child_program=child,
                 mutation_ticket=list(initial['mutation_tickets'][source]), mutated=False, construction_cost=4, copy_cost=1)
        births += 1
    units = [None if u is None else dict(**u, program=programs[i]) for i, u in enumerate(units)]
    material.update(construction_spent=4*births, copy_spent=births)
    require(material['material_before'] == material['material_after'], 'phase material conservation')
    require(material['energy_after'] == material['energy_before'] - material['spent'], 'phase energy ledger')
    return dict(units=units, raw=raw, material=material)


def verify_probe(case, selection):
    s = selection
    require(set(s) == set(KEYS), 'selection schema')
    same([case[k] for k in ('mode', 'seed', 'exchange')], [s[k] for k in ('mode', 'seed', 'exchange')], 'source key')
    require(type(s['tick']) is int and 1 <= s['tick'] <= len(case['rows']), 'probe tick')
    row = case['rows'][s['tick']-1]
    same(row['tick'], s['tick'], 'saved tick')
    old = case['initial'] if s['tick'] == 1 else case['rows'][s['tick']-2]
    same(old['site_ids'][s['site']], s['identity'], 'source identity')
    root = s['identity']; parents = case['final']['parents']
    while parents[root] is not None:
        require(type(parents[root]) is int and 0 <= parents[root] < root, 'source ancestry')
        root = parents[root]
    same(root, s['root'], 'source root')
    require(root in (0, 1), 'target founder')
    p = row['physical']
    initial = dict(units=deepcopy(p['interaction_units']), raw=deepcopy(old['raw'] if s['tick'] == 1 else old['physical']['raw']),
                   directions=deepcopy(p['directions']), mutation_tickets=deepcopy(p['mutation_tickets']))
    unit = initial['units'][s['site']]
    require(unit is not None and 0 < unit['energy'] < 16 and initial['directions'][s['site']] == 3, 'eligible source')
    same(unit['energy'], s['energy_before'], 'source energy')
    target = (s['site']-16) % 256
    require(initial['units'][target] is None or initial['units'][target]['energy'] == 0, 'eligible target vacancy')
    require(initial['raw'][target] + int(initial['units'][target] is not None and initial['units'][target]['energy'] == 0) >= 1, 'eligible target raw')
    control = phase(initial)
    same(control, {k: p[k] for k in ('units', 'raw', 'material')}, 'entire saved control')
    treated_initial = deepcopy(initial)
    treated_initial['units'][s['site']]['energy'] = 16
    treated = phase(treated_initial)
    added = 16 - s['energy_before']
    require(treated['material']['energy_after'] == control['material']['energy_before'] + added - treated['material']['spent'], 'external energy ledger')
    return dict(deepcopy(s), added_energy=added, initial=initial, control=control, treated=treated)


def aggregate(records):
    validate_selection([{k: r[k] for k in KEYS} for r in records])
    for r in records:
        require(set(r) == set(KEYS) | {'added_energy', 'initial', 'control', 'treated'}, 'record schema')
        same(r['added_energy'], 16-r['energy_before'], 'added energy')
        same(r['initial']['units'][r['site']]['energy'], r['energy_before'], 'initial selected energy')
        start = sum(u['energy'] for u in r['initial']['units'] if u is not None)
        mass = sum(r['initial']['raw']) + sum(u is not None for u in r['initial']['units'])
        for arm, added in (('control', 0), ('treated', r['added_energy'])):
            result = r[arm]; m = result['material']
            same(m['energy_before'], start+added, 'arm initial energy')
            same(m['energy_after'], start+added-m['spent'], 'arm energy balance')
            same(sum(u['energy'] for u in result['units'] if u is not None), m['energy_after'], 'arm units energy')
            same(m['material_before'], mass, 'arm initial mass')
            same(m['material_after'], mass, 'arm mass balance')
            same(sum(result['raw'])+sum(u is not None for u in result['units']), mass, 'arm units mass')
    cells = []
    for genotype in prior.GENOTYPES:
        for exchange in (False, True):
            rows = [r for r in records if r['genotype'] == genotype and r['exchange'] == exchange]
            cell = dict(genotype=genotype, exchange=exchange, probes=len(rows), control_formed=0, treated_formed=0,
                        nonzero_treated=0, added_energy=0, treated_reasons=dict.fromkeys(REASONS, 0),
                        total_formed_delta=0, spent_delta=0, energy_after_delta=0, other_reason_changes=0)
            for r in rows:
                c, t = r['control']['material'], r['treated']['material']
                cp = {p['source']: p for p in c['proposals']}; tp = {p['source']: p for p in t['proposals']}
                require(cp.keys() == tp.keys() and r['site'] in cp, 'proposal sources')
                a, b = cp[r['site']], tp[r['site']]
                cell['control_formed'] += a['reason'] == 'formed'
                cell['treated_formed'] += b['reason'] == 'formed'
                cell['nonzero_treated'] += b['reason'] == 'formed' and b['material'] != 0
                cell['added_energy'] += r['added_energy']
                cell['treated_reasons'][b['reason']] += 1
                cell['total_formed_delta'] += sum(p['reason'] == 'formed' for p in tp.values()) - sum(p['reason'] == 'formed' for p in cp.values())
                cell['spent_delta'] += t['spent'] - c['spent']
                cell['energy_after_delta'] += t['energy_after'] - c['energy_after']
                cell['other_reason_changes'] += sum(cp[source]['reason'] != tp[source]['reason'] for source in cp if source != r['site'])
            cells.append(cell)
    return cells


def main():
    from scripts.north_energy_inputs import bindings, read, digest, input_paths, source_cases
    root = OUTPUT
    proof_path = root/'independent-verification.json'
    require(not proof_path.exists(), 'proof already exists')
    started = monotonic()
    names = ('metadata.json', 'records.json', 'summary.json')
    before = {}; input_before = {}; errors = {}; paths = []
    completed = 0
    def snapshot(mapping, failures):
        hashes = {}
        for name, path in mapping.items():
            try:
                hashes[name] = digest(path)
            except Exception as error:
                failures[name] = f'{type(error).__name__}: {error}'
        return hashes
    def budget(extra=0):
        require(monotonic()-started < 300, 'verification time budget')
        require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file())+extra < 33554432, 'verification storage budget')
    try:
        paths = input_paths(errors)
        input_before = snapshot({p: Path(p) for p in paths}, errors)
        before = snapshot({n: root/n for n in names}, errors)
        bound = bindings()
        require(len(bound) == 401, '401 bound inputs')
        same(paths, sorted(bound), 'complete input paths')
        same(input_before, bound, 'readable input inventory')
        same(digest(Path(__file__)), bound['scripts/verify_v4_north_energy.py'], 'running verifier binding')
        meta = read(root/'metadata.json')
        for key, value in dict(status='complete', planned_probes=52, completed_probes=52, new_phase_transitions=104,
                               new_full_world_steps=0, new_environment_sources=0, reused_environment_sources=20,
                               new_independent_initial_worlds=0, time_limit_seconds=300, storage_limit_bytes=33554432).items():
            same(meta[key], value, 'metadata '+key)
        require(type(meta['git_commit']) is str and len(meta['git_commit']) == 40 and all(c in '0123456789abcdef' for c in meta['git_commit']), 'recorded commit')
        require(type(meta['elapsed_seconds']) in (int, float) and math.isfinite(meta['elapsed_seconds']) and 0 <= meta['elapsed_seconds'] < 300, 'run time budget')
        same(meta['input_paths'], paths, 'metadata input paths')
        same(meta['input_sha256'], bound, 'before bindings')
        same(meta['input_sha256_after'], bound, 'after bindings')
        same(meta['output_sha256'], {n: before[n] for n in names[1:]}, 'output hashes')
        require({p.name for p in root.iterdir()} == set(names), 'exclusive output inventory')
        saved = read(root/'records.json')
        require(type(saved) is list and len(saved) == 52, '52 saved records')
        sources = list(source_cases()); require(len(sources) == 240, '240 source cases')
        actors = []; cases = {}
        old_saved = read(Path('data/v4-study-026/records.json'))
        require(type(old_saved) is list and len(old_saved) == 240, '240 original records')
        for index, (genotype, path) in enumerate(sources):
            budget()
            case = read(path)
            key = (genotype, case['mode'], case['exchange'], case['seed'])
            same(list(key), list(prior.GRID[index]), 'source order')
            reconstructed = prior.recount(case, genotype)
            same(reconstructed, old_saved[index], 'entire original actor record')
            actors.append(reconstructed)
            cases[key] = path
        selection = select(actors)
        records = []
        for index, s in enumerate(selection):
            budget()
            case = read(cases[(s['genotype'], s['mode'], s['exchange'], s['seed'])])
            record = verify_probe(case, s)
            same(saved[index], record, 'entire independently reconstructed probe')
            records.append(record); completed += 1
        same(read(root/'summary.json'), aggregate(records), 'all four summary cells')
        same(bindings(), bound, 'inputs unchanged')
        same({n: digest(root/n) for n in names}, before, 'outputs unchanged')
        proof = dict(status='verified', input_files=401, probes=52, new_phase_transitions=104, replayed_saved_steps=7680,
                     new_full_world_steps=0, new_environment_sources=0, reused_environment_sources=20,
                     new_independent_initial_worlds=0, files_sha256=before, verifier_sha256=digest(Path(__file__)),
                     input_paths=paths, input_sha256=input_before, input_sha256_after=bound,
                     elapsed_seconds=monotonic()-started, time_limit_seconds=300, storage_limit_bytes=33554432,
                     scope='independently recounted 240 actor ledgers, fixed 52 selections, dictionary hereditary phase pairs and four summary cells')
        payload = json.dumps(proof, indent=2, allow_nan=False)+'\n'
        budget(len(payload.encode()))
        with proof_path.open('x') as stream:
            stream.write(payload)
        budget()
        print('verified 52 probes, 104 phase transitions, 7680 replayed saved steps and 401 bindings')
    except BaseException as error:
        failure = root/'verification-failure.json'
        if root.is_dir() and not failure.exists():
            after_errors = {}
            evidence = dict(status='failed', error=f'{type(error).__name__}: {error}', completed_probes=completed,
                            input_paths=paths, input_sha256=input_before, files_sha256_before=before,
                            input_sha256_after=snapshot({p: Path(p) for p in paths}, after_errors),
                            files_sha256_after=snapshot({n: root/n for n in names}, after_errors),
                            read_errors_before=errors, read_errors_after=after_errors)
            with failure.open('x') as stream:
                stream.write(json.dumps(evidence, indent=2, allow_nan=False)+'\n')
        raise


if __name__ == '__main__':
    main()
