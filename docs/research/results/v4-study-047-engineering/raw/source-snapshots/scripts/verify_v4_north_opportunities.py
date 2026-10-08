"""Study026 independent saved-tape physics and actor opportunity recount."""
from itertools import product
import json
import math
from pathlib import Path
from time import monotonic
from bitgenesis.v4.exchange_branch_audit import physical_step

GENOTYPES = ('homogeneous', 'heterogeneous')
MODES = ('random-direction', 'random-feed', 'random-both')
GRID = tuple(product(GENOTYPES, MODES, (False, True), range(120000, 120020)))
REASONS = ('dissolved', 'energy', 'occupied', 'raw_material', 'collision', 'formed')
OUTPUT = Path('data/v4-study-026')
ACTOR_KEYS = set('tick site identity root direction proposed accepted energy_before energy_interaction target target_occupied raw_available reason encoded_material formed_material'.split())


def require(ok, message):
    if not ok:
        raise ValueError(message)


def same(actual, expected, message):
    require(json.dumps(actual, sort_keys=True, allow_nan=False) ==
            json.dumps(expected, sort_keys=True, allow_nan=False), message)


def recount(case, genotype):
    require(genotype in GENOTYPES and case['mode'] in MODES and
            type(case['exchange']) is bool and type(case['seed']) is int and
            case['seed'] in range(120000, 120020), 'fixed case identity')
    config = case['config']
    same(config, dict(width=16, height=16, capacity=64, leak=1, bond_cost=1,
                     threshold=16, construction_cost=4, copy_cost=1,
                     mutation_per_thousand=0), 'fixed physics')
    units = case['initial']['units']; raw = case['initial']['raw']
    require(len(units) == len(raw) == 256, 'complete initial world')
    expected_units = [None] * 256
    expected_raw = [0] * 256
    for identity, site in enumerate((85, 86, 204)):
        program = [3]*4 if identity == 2 else [0, 0, 0, identity+1 if genotype == 'heterogeneous' else 0]
        expected_units[site] = dict(material=3 if identity == 2 else 0, energy=64, program=program)
    for site in (101, 102, 117, 118):
        expected_raw[site] = 1
    same(units, expected_units, 'fixed genotype and initial units')
    same(raw, expected_raw, 'fixed initial raw')
    same(case['initial']['tick'], 0, 'initial tick')
    ids = []; parents = []; deaths = []
    for unit in units:
        ids.append(len(parents) if unit is not None else None)
        if unit is not None:
            parents.append(None); deaths.append(None)
    require(len(parents) == 3, 'three founders')
    same(case['initial']['site_ids'], ids, 'initial identities')
    require(len(case['rows']) == 32, '32 saved steps')
    steps = []
    for tick, row in enumerate(case['rows'], 1):
        saved = row['physical']
        require(row['tick'] == saved['tick'] == tick, 'sequential ticks')
        physical = physical_step(units, raw, config, saved, case['exchange'])
        same(saved, physical, 'entire physical ledger')
        require(physical['energy_after'] == physical['energy_before'] + physical['imported'] - physical['spent'], 'energy balance')
        old = ids.copy()
        middle = physical['interaction_units']
        dissolved = set(physical['material']['dissolved'])
        stock = [amount + int(site in dissolved) for site, amount in enumerate(raw)]
        proposals = {p['source']: p for p in physical['material']['proposals']}
        actors = []
        for site, identity in enumerate(old):
            if identity is None:
                continue
            root = identity
            while parents[root] is not None:
                require(type(parents[root]) is int and 0 <= parents[root] < root, 'acyclic ancestry')
                root = parents[root]
            require(root in (0, 1, 2), 'founder root')
            direction = physical['directions'][site]
            dx, dy = ((1, 0), (-1, 0), (0, 1), (0, -1))[direction]
            target = ((site // 16 + dy) % 16) * 16 + (site % 16 + dx) % 16
            reason = 'dissolved' if site in dissolved else proposals[site]['reason']
            proposed = saved['driven']['inputs'][site]['proposed']
            actors.append(dict(tick=tick, site=site, identity=identity, root=root, direction=direction,
                proposed=proposed, accepted=min(proposed, 64-units[site]['energy']),
                energy_before=units[site]['energy'], energy_interaction=middle[site]['energy'],
                target=target, target_occupied=middle[target] is not None and target not in dissolved,
                raw_available=stock[target], reason=reason, encoded_material=units[site]['program'][direction],
                formed_material=proposals[site]['material'] if reason == 'formed' else None))
        for site in dissolved:
            require(ids[site] is not None, 'death identity')
            deaths[ids[site]] = tick; ids[site] = None
        for p in physical['material']['proposals']:
            if p['reason'] == 'formed':
                require(old[p['source']] is not None and ids[p['target']] is None, 'birth parent and vacancy')
                ids[p['target']] = len(parents); parents.append(old[p['source']]); deaths.append(None)
        same(row['site_ids'], ids, 'complete birth death identity differences')
        units, raw = physical['units'], physical['raw']
        require(all((u is None) == (identity is None) for u, identity in zip(units, ids)), 'living identity correspondence')
        steps.append(actors)
    same(case['final'], dict(tick=32, units=units, raw=raw, site_ids=ids, parents=parents), 'final state and ancestry')
    return dict(genotype=genotype, mode=case['mode'], seed=case['seed'], exchange=case['exchange'], steps=steps)


def aggregate(records):
    require(type(records) is list and len(records) == 240, '240 records')
    same([[r[k] for k in ('genotype', 'mode', 'exchange', 'seed')] for r in records],
         [list(key) for key in GRID], 'complete ordered grid')
    for record in records:
        require(set(record) == {'genotype', 'mode', 'exchange', 'seed', 'steps'}, 'record schema')
        require(type(record['steps']) is list and len(record['steps']) == 32, '32 actor lists')
        for tick, actors in enumerate(record['steps'], 1):
            require(type(actors) is list, 'actor list')
            sites = []
            for a in actors:
                require(type(a) is dict and set(a) == ACTOR_KEYS, 'exact actor schema')
                for key in ACTOR_KEYS - {'target_occupied', 'reason', 'formed_material'}:
                    require(type(a[key]) is int and a[key] >= 0, 'native nonnegative actor integers')
                require(a['tick'] == tick and a['site'] < 256 and a['target'] < 256 and a['root'] in (0, 1, 2) and a['direction'] < 4 and a['encoded_material'] < 4, 'actor bounds')
                require(type(a['target_occupied']) is bool and a['reason'] in REASONS, 'actor predicate and reason')
                require(a['accepted'] <= a['proposed'] and a['energy_before'] <= 64, 'actor input bounds')
                require((type(a['formed_material']) is int and 0 <= a['formed_material'] < 4) if a['reason'] == 'formed' else a['formed_material'] is None, 'formed material presence')
                sites.append(a['site'])
            require(sites == sorted(set(sites)), 'ordered unique actor sites')
    cells = []
    for offset in range(0, 240, 20):
        selected = records[offset:offset+20]
        def totals(target):
            actors = [a for r in selected for step in r['steps'] for a in step if not target or a['root'] in (0, 1)]
            north = [a for a in actors if a['direction'] == 3]
            masks = {str(i): 0 for i in range(8)}
            for a in north:
                if a['reason'] != 'dissolved':
                    masks[str(int(a['energy_interaction'] < 16) + 2*int(a['target_occupied']) + 4*int(a['raw_available'] < 1))] += 1
            return dict(actor_steps=len(actors), proposed=sum(a['proposed'] for a in actors),
                accepted=sum(a['accepted'] for a in actors), north_tickets=len(north),
                north_proposals=sum(a['reason'] != 'dissolved' for a in north),
                north_nonzero_formed=sum(a['reason'] == 'formed' and a['formed_material'] != 0 for a in north),
                reasons={reason: sum(a['reason'] == reason for a in actors) for reason in REASONS},
                north_reasons={reason: sum(a['reason'] == reason for a in north) for reason in REASONS}, north_predicates=masks)
        first = selected[0]
        cells.append(dict(genotype=first['genotype'], mode=first['mode'], exchange=first['exchange'], cases=20, all=totals(False), target=totals(True)))
    return cells


def main():
    from scripts.north_opportunity_inputs import bindings, read, digest, input_paths, source_cases
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
        paths = input_paths(errors)
        input_before = snapshot({p: Path(p) for p in paths}, errors)
        before = snapshot({n: root/n for n in names}, errors)
        bound = bindings()
        require(len(bound) == 389, '389 bound inputs')
        same(input_before, bound, 'readable input inventory')
        same(digest(Path(__file__)), bound['scripts/verify_v4_north_opportunities.py'], 'running verifier binding')
        meta = read(root/'metadata.json')
        for key, value in dict(status='complete', planned_cases=240, completed_cases=240, saved_steps=7680,
                new_simulation_steps=0, new_environment_sources=0, reused_environment_sources=20,
                new_independent_initial_worlds=0, time_limit_seconds=300, storage_limit_bytes=67108864).items():
            same(meta[key], value, 'metadata ' + key)
        require(type(meta['git_commit']) is str and len(meta['git_commit']) == 40 and all(c in '0123456789abcdef' for c in meta['git_commit']), 'recorded commit')
        require(type(meta['elapsed_seconds']) in (float, int) and math.isfinite(meta['elapsed_seconds']) and 0 <= meta['elapsed_seconds'] < 300, 'analysis time budget')
        same(meta['input_sha256'], bound, 'before bindings')
        same(meta['input_sha256_after'], bound, 'after bindings')
        same(meta['output_sha256'], {n: before[n] for n in names[1:]}, 'output hashes')
        require({p.name for p in root.iterdir()} == set(names), 'exclusive output inventory')
        saved = read(root/'records.json')
        require(type(saved) is list and len(saved) == 240, '240 saved records')
        sources = list(source_cases())
        require(len(sources) == 240, '240 sources')
        records = []
        for index, (genotype, path) in enumerate(sources):
            budget()
            case = read(path)
            same([genotype, case['mode'], case['exchange'], case['seed']], list(GRID[index]), 'source order')
            record = recount(case, genotype)
            same(saved[index], record, 'entire independent actor ledger')
            records.append(record)
        same(read(root/'summary.json'), aggregate(records), 'all twelve cells')
        same(bindings(), bound, 'inputs unchanged')
        same({n: digest(root/n) for n in names}, before, 'outputs unchanged')
        proof = dict(status='verified', cases=240, saved_steps=7680, input_files=389,
            new_simulation_steps=0, new_environment_sources=0, reused_environment_sources=20,
            new_independent_initial_worlds=0, files_sha256=before, verifier_sha256=digest(Path(__file__)),
            elapsed_seconds=monotonic()-started,
            scope='independent dictionary physics, full physical ledgers, identity differences, parent chains, all actor opportunities and twelve summary cells')
        payload = json.dumps(proof, indent=2, allow_nan=False) + '\n'
        budget(len(payload.encode()))
        with proof_path.open('x') as stream:
            stream.write(payload)
        print('verified 240 cases, 7680 saved steps and 389 bindings')
    except BaseException as error:
        failure = root/'verification-failure.json'
        if root.is_dir() and not failure.exists():
            after_errors = {}
            evidence = dict(status='failed', error=f'{type(error).__name__}: {error}',
                input_paths=paths, input_sha256=input_before, files_sha256_before=before,
                input_sha256_after=snapshot({p: Path(p) for p in paths}, after_errors),
                files_sha256_after=snapshot({n: root/n for n in names}, after_errors),
                read_errors_before=errors, read_errors_after=after_errors)
            with failure.open('x') as stream:
                stream.write(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
        raise


if __name__ == '__main__':
    main()
