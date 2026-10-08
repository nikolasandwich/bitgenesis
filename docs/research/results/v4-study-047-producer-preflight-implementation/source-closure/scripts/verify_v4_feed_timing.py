"""Study030 independent saved physics, identity and timing verification."""
from copy import deepcopy
import json
import math
from pathlib import Path
from time import monotonic
from scripts import verify_v4_child_energy as energy_verifier
from scripts.verify_v4_child_energy import same, require, KEYS, GENOTYPES, validate_selection

OUTPUT = Path('data/v4-study-030')
TOTALS = ('steps', 'proposal_events', 'before_death_events', 'death_events',
          'after_death_events', 'proposed', 'before_death_proposed', 'death_proposed',
          'after_death_proposed', 'site_accepted', 'child_accepted', 'other_accepted', 'rejected')
PHASES = ('before_death', 'death', 'after_death')
ROW_KEYS = {'tick', 'phase', 'identity_before', 'identity_after', 'proposed',
            'site_accepted', 'child_accepted', 'other_accepted', 'rejected'}
RECORD_KEYS = {'selection', 'child_identity', 'child_site', 'birth_tick', 'death_tick',
               'rows', 'totals', 'first_proposed_tick', 'first_proposed_phase', 'first_after_death_tick'}


def phase(tick, death):
    return 'before_death' if tick < death else 'death' if tick == death else 'after_death'


def totals(rows):
    result = dict.fromkeys(TOTALS, 0)
    for row in rows:
        result['steps'] += 1
        result['proposal_events'] += int(row['proposed'] > 0)
        result[row['phase'] + '_events'] += int(row['proposed'] > 0)
        result[row['phase'] + '_proposed'] += row['proposed']
        for key in ('proposed', 'site_accepted', 'child_accepted', 'other_accepted', 'rejected'):
            result[key] += row[key]
    return result


def validate_record(record):
    require(type(record) is dict and set(record) == RECORD_KEYS, 'timing record schema')
    s = record['selection']
    require(type(s) is dict and set(s) == set(KEYS), 'selection schema')
    require(s['genotype'] in GENOTYPES and s['mode'] == 'random-both' and type(s['exchange']) is bool, 'selection cell')
    require(all(type(s[k]) is int for k in KEYS[2:] if k != 'exchange'), 'selection integers')
    for key in ('child_identity', 'child_site', 'birth_tick', 'death_tick'):
        require(type(record[key]) is int and record[key] >= 0, 'record integer')
    birth, death, child = (record[k] for k in ('birth_tick', 'death_tick', 'child_identity'))
    same(birth, s['tick'], 'birth selection')
    require(birth < death <= 32 and record['child_site'] < 256, 'lifetime and site')
    rows = record['rows']
    require(type(rows) is list and len(rows) == 32 - birth, 'complete timing window')
    identity = child
    for tick, row in enumerate(rows, birth + 1):
        require(type(row) is dict and set(row) == ROW_KEYS, 'timing row schema')
        same(row['tick'], tick, 'timing tick')
        same(row['phase'], phase(tick, death), 'timing phase')
        for key in ('identity_before', 'identity_after'):
            require(row[key] is None or type(row[key]) is int and row[key] >= 0, 'identity type')
        same(row['identity_before'], identity, 'identity continuity')
        same(row['identity_before'] == child, tick <= death, 'original identity lifetime')
        same(row['identity_after'] == child, tick < death, 'original identity death')
        identity = row['identity_after']
        for key in ('proposed', 'site_accepted', 'child_accepted', 'other_accepted', 'rejected'):
            require(type(row[key]) is int and row[key] >= 0, 'nonnegative timing amount')
        require(row['proposed'] in (0, 8), 'original input ticket')
        same(row['site_accepted'] + row['rejected'], row['proposed'], 'input conservation')
        same(row['child_accepted'], row['site_accepted'] if tick <= death else 0, 'child attribution')
        same(row['other_accepted'], row['site_accepted'] - row['child_accepted'], 'other attribution')
        if row['identity_before'] is None:
            same(row['site_accepted'], 0, 'empty site rejects')
    same(record['totals'], totals(rows), 'thirteen timing totals')
    proposed = [r for r in rows if r['proposed'] > 0]
    after = [r for r in proposed if r['phase'] == 'after_death']
    same(record['first_proposed_tick'], proposed[0]['tick'] if proposed else None, 'first proposed tick')
    same(record['first_proposed_phase'], proposed[0]['phase'] if proposed else None, 'first proposed phase')
    same(record['first_after_death_tick'], after[0]['tick'] if after else None, 'first postdeath tick')


def recount(branch, energy, *, on_step=None):
    independently_replayed = energy_verifier.recount(branch, on_step=on_step)
    same(energy, independently_replayed, 'entire independent 029 energy')
    site, child, death = (independently_replayed[k] for k in ('child_site', 'child_identity', 'death_tick'))
    previous = branch['initial']['site_ids'][site]
    rows = []
    for saved in branch['rows']:
        flow = saved['physical']['driven']['inputs'][site]
        accepted = flow['accepted']
        child_accepted = accepted if previous == child else 0
        row = dict(tick=saved['tick'], phase=phase(saved['tick'], death),
            identity_before=previous, identity_after=saved['site_ids'][site],
            proposed=flow['proposed'], site_accepted=accepted, child_accepted=child_accepted,
            other_accepted=accepted-child_accepted, rejected=flow['proposed']-accepted)
        rows.append(row)
        previous = row['identity_after']
    proposed = [r for r in rows if r['proposed'] > 0]
    after = [r for r in proposed if r['phase'] == 'after_death']
    result = {k: deepcopy(independently_replayed[k]) for k in
              ('selection', 'child_identity', 'child_site', 'birth_tick', 'death_tick')}
    result.update(rows=rows, totals=totals(rows), first_proposed_tick=proposed[0]['tick'] if proposed else None,
        first_proposed_phase=proposed[0]['phase'] if proposed else None,
        first_after_death_tick=after[0]['tick'] if after else None)
    validate_record(result)
    same(result['totals']['child_accepted'], energy['totals']['accepted'], '029 accepted total')
    for timing, old in zip(rows, energy['rows']):
        same([timing['tick'], timing['proposed'], timing['child_accepted']],
             [old['tick'], old['proposed'], old['accepted']], '029 living timing row')
    return result


def aggregate(records):
    require(type(records) is list, 'record list')
    for record in records:
        validate_record(record)
    validate_selection([r['selection'] for r in records])
    cells = []
    for genotype in GENOTYPES:
        for exchange in (False, True):
            group = [r for r in records if r['selection']['genotype'] == genotype and r['selection']['exchange'] == exchange]
            counts = {name: sum(r['first_proposed_phase'] == p for r in group) for name, p in
                      (('no_proposal', None), ('first_before_death', 'before_death'),
                       ('first_at_death', 'death'), ('first_after_death', 'after_death'))}
            counts.update(any_after_death=sum(r['first_after_death_tick'] is not None for r in group),
                any_child_accepted=sum(r['totals']['child_accepted'] > 0 for r in group),
                any_other_accepted=sum(r['totals']['other_accepted'] > 0 for r in group))
            cells.append(dict(genotype=genotype, exchange=exchange, n=len(group),
                totals={k: sum(r['totals'][k] for r in group) for k in TOTALS}, **counts))
    paired = {}
    for index, record in enumerate(records):
        key = tuple(record['selection'][k] for k in KEYS[1:])
        genotype = record['selection']['genotype']
        require(genotype not in paired.setdefault(key, {}), 'unique paired record')
        paired[key][genotype] = index
    require(len(paired) == 26 and all(set(p) == set(GENOTYPES) for p in paired.values()), '26 complete pairs')
    pairs = []
    for index, record in enumerate(records):
        if record['selection']['genotype'] != 'homogeneous':
            continue
        selection = {k: record['selection'][k] for k in KEYS[1:]}
        other_index = paired[tuple(selection.values())]['heterogeneous']
        other = records[other_index]
        for key in ('child_site', 'birth_tick'):
            same(other[key], record[key], 'paired ' + key)
        same([(r['tick'], r['proposed']) for r in other['rows']],
             [(r['tick'], r['proposed']) for r in record['rows']], 'paired complete tickets')
        pairs.append(dict(selection=selection, homogeneous_index=index, heterogeneous_index=other_index,
            delta={k: other['totals'][k]-record['totals'][k] for k in TOTALS},
            phase_shift_ticks=[a['tick'] for a, b in zip(record['rows'], other['rows'])
                               if a['proposed'] > 0 and a['phase'] != b['phase']]))
    return dict(cells=cells, pairs=pairs)


def check_budget(root, started, extra=0):
    require(monotonic() - started < 300, 'verification time budget')
    require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) + extra < 33554432, 'verification storage budget')


def main():
    from scripts.feed_timing_inputs import bindings, read, digest, input_paths, source_cases
    root = OUTPUT
    proof_path = root / 'independent-verification.json'
    require(not proof_path.exists(), 'proof already exists')
    started = monotonic()
    paths, input_before, before, errors = [], {}, {}, {}
    completed = steps = site_steps = live_start_steps = 0
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
        same(len(bound), 491, '491 bound inputs')
        same(paths, sorted(bound), 'complete inventory')
        same(input_before, bound, 'readable inputs')
        same(digest(Path(__file__)), bound['scripts/verify_v4_feed_timing.py'], 'running verifier')
        meta = read(root / 'metadata.json')
        fixed = dict(status='complete', planned_branches=52, completed_branches=52,
            saved_world_steps=996, site_steps=996, live_start_steps=268, new_full_world_steps=0, new_phase_transitions=0,
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
        energies = read(Path('data/v4-study-029/records.json'))
        require(type(energies) is list and len(energies) == 52, '52 energy records')
        saved = read(root / 'records.json')
        require(type(saved) is list and len(saved) == 52, '52 saved records')
        records = []

        def counted_step():
            nonlocal steps
            steps += 1
            budget()

        for index, source in enumerate(sources):
            budget()
            result = recount(read(source), energies[index], on_step=counted_step)
            same(saved[index], result, 'entire independent record')
            records.append(result)
            completed += 1
            site_steps += len(result['rows'])
            live_start_steps += sum(r['identity_before'] == result['child_identity'] for r in result['rows'])
        same(steps, 996, '996 replayed saved world steps')
        same(site_steps, 996, '996 recounted site steps')
        same(live_start_steps, 268, '268 live start steps')
        same(read(root / 'summary.json'), aggregate(records), 'independent summary and pairs')
        same(bindings(), bound, 'inputs unchanged')
        after_errors = {}
        same(snapshot({n: root / n for n in names}, after_errors), before, 'outputs unchanged')
        same(after_errors, {}, 'readable outputs after')
        require({p.name for p in root.iterdir()} == set(names), 'exclusive output inventory after')
        proof = dict(status='verified', input_files=491, branches=52, saved_world_steps=steps,
            site_steps=site_steps, live_start_steps=live_start_steps, pairs=26, new_full_world_steps=0, new_phase_transitions=0,
            new_environment_sources=0, reused_environment_sources=20, selected_environment_sources=11,
            new_independent_initial_worlds=0, files_sha256=before,
            verifier_sha256=digest(Path(__file__)), input_paths=paths, input_sha256=input_before,
            input_sha256_after=bound, elapsed_seconds=monotonic()-started, time_limit_seconds=300,
            storage_limit_bytes=33554432,
            scope='independent saved dictionary physics, plain identities and parents, full-window site timing and 26 pairs')
        payload = json.dumps(proof, indent=2, allow_nan=False) + '\n'
        budget(len(payload.encode()))
        with proof_path.open('x') as stream:
            stream.write(payload)
        budget()
        print('verified 52 timing records, 996 saved/site steps, 268 live start steps, 26 pairs and 491 inputs')
    except BaseException as error:
        failure = root / 'verification-failure.json'
        if root.is_dir() and not failure.exists():
            after_errors = {}
            evidence = dict(status='failed', error=f'{type(error).__name__}: {error}',
                completed_branches=completed, saved_world_steps=steps, site_steps=site_steps, live_start_steps=live_start_steps,
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
