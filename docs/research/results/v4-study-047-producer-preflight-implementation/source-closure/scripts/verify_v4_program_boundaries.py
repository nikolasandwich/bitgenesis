"""Study024 independent reuse of the 020/021 verification algorithms.

New formation events are derived from identity differences, never proposals.
"""
import json
import math
from itertools import product
from pathlib import Path
from time import monotonic
from scripts import verify_v4_copy_episodes as phases
from scripts import verify_v4_copy_members as members

GENOTYPES = ('homogeneous', 'heterogeneous')
GRID = tuple(product(GENOTYPES, (False, True), range(120000, 120020)))
OUTPUT = Path('data/v4-study-024')


def require(value, message):
    if not value:
        raise ValueError(message)


def same(actual, expected, message):
    require(json.dumps(actual, sort_keys=True, separators=(',', ':'), allow_nan=False) ==
            json.dumps(expected, sort_keys=True, separators=(',', ':'), allow_nan=False), message)


def recount(case, genotype):
    require(genotype in GENOTYPES, 'known genotype')
    require(type(case['seed']) is int and 120000 <= case['seed'] < 120020 and
            type(case['exchange']) is bool and case['mode'] == 'random-direction', 'strict case identity')
    require(len(case['rows']) == 32, '32 complete source rows')
    phase_record = phases.recount(case)
    label = f"seed-{case['seed']}-random-direction-exchange-{str(case['exchange']).lower()}"
    member_record = members.recount(case, label)
    previous = {identity for identity in case['initial']['site_ids'] if identity is not None}
    parents = case['final']['parents']
    formations = []
    for row in case['rows']:
        current = {identity: site for site, identity in enumerate(row['site_ids']) if identity is not None}
        formations.append([dict(child=child, parent=parents[child], site=current[child],
            material=row['physical']['units'][current[child]]['material'])
            for child in sorted(current.keys() - previous)])
        previous = set(current)
    return dict(genotype=genotype, seed=case['seed'], exchange=case['exchange'],
                phases=phase_record, members=member_record, formations=formations)


def aggregate(records):
    same([[r['genotype'], r['exchange'], r['seed']] for r in records],
         [list(key) for key in GRID], 'complete ordered 80-case grid')
    cells = []
    for genotype, exchange in product(GENOTYPES, (False, True)):
        selected = [r for r in records if r['genotype'] == genotype and r['exchange'] == exchange]
        phase_steps = [s for r in selected for s in r['phases']['steps']]
        member_steps = [s for r in selected for s in r['members']['steps']]
        episodes = [e for r in selected for e in r['members']['episodes']]
        for record in selected:
            require(len(record['phases']['steps']) == len(record['members']['steps']) ==
                    len(record['formations']) == 32, 'complete saved ledgers')
        cell = dict(genotype=genotype, exchange=exchange, cases=len(selected),
            episodes=sum(len(r['phases']['episodes']) for r in selected),
            double_steps=sum(len(s['final']) >= 2 for s in phase_steps),
            stable_pair_episodes=sum(e['stable_pair'] for e in episodes),
            max_same_pair_run=max((e['max_same_pair_run'] for e in episodes), default=0),
            all_new_double_steps=sum(s['new_only_count'] >= 2 for s in member_steps))
        cell.update({name: sum(s['crossings'][index] for s in phase_steps)
                     for index, name in enumerate(phases.FLAGS)})
        cell['hidden'] = sum(s['hidden'] for s in phase_steps)
        cell['nonzero_births'] = sum(event['material'] != 0 for r in selected
                                    for step in r['formations'] for event in step)
        cells.append(cell)
    return cells


def main():
    from scripts.program_boundary_inputs import bindings, read, digest, source_cases
    root = OUTPUT
    proof_path = root / 'independent-verification.json'
    if proof_path.exists():
        raise FileExistsError(proof_path)
    started = monotonic()
    bound = {}
    before = {}
    names = ('metadata.json', 'records.json', 'summary.json')
    try:
        before = {name: digest(root / name) for name in names}
        meta = read(root / 'metadata.json')
        bound = meta.get('input_sha256', {})
        bound = bindings()
        expected = dict(status='complete', planned_cases=80, completed_cases=80, saved_steps=2560,
            new_simulation_steps=0, new_environment_sources=0, reused_environment_sources=20,
            new_independent_initial_worlds=0, time_limit_seconds=300, storage_limit_bytes=33554432)
        for key, value in expected.items():
            same(meta[key], value, 'metadata ' + key)
        require(type(meta['git_commit']) is str and len(meta['git_commit']) == 40 and
                all(c in '0123456789abcdef' for c in meta['git_commit']), 'recorded commit')
        require(type(meta['elapsed_seconds']) in (int, float) and math.isfinite(meta['elapsed_seconds'])
                and 0 <= meta['elapsed_seconds'] < 300, 'analysis time budget')
        same(meta['input_sha256'], bound, 'before bindings')
        same(meta['input_sha256_after'], bound, 'after bindings')
        same(bound['scripts/verify_v4_program_boundaries.py'], digest(Path(__file__)), 'running verifier binding')
        same(meta['output_sha256'], {name: before[name] for name in names[1:]}, 'exact output hashes')
        saved = read(root / 'records.json')
        require(type(saved) is list and len(saved) == 80, '80 saved records')
        sources = list(source_cases())
        require(len(sources) == 80, '80 source cases')
        records = []
        for index, (genotype, path) in enumerate(sources):
            require(monotonic() - started < 300, 'verification time budget')
            require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) < 33554432, 'storage budget')
            case = read(path)
            same([genotype, case['exchange'], case['seed']], list(GRID[index]), 'source identity order')
            record = recount(case, genotype)
            same(saved[index], record, 'all independent stage member and formation fields')
            records.append(record)
        same(aggregate(records), read(root / 'summary.json'), 'all four summary cells')
        same(bindings(), bound, 'inputs unchanged during verification')
        same({name: digest(root / name) for name in names}, before, 'outputs unchanged during verification')
        proof = dict(status='verified', cases=80, saved_steps=2560,
            new_simulation_steps=0, new_environment_sources=0, reused_environment_sources=20,
            new_independent_initial_worlds=0, input_files=len(bound), files_sha256=before,
            verifier_sha256=digest(Path(__file__)), elapsed_seconds=monotonic()-started,
            scope='reused independent 020 phase and 021 member reconstruction; identity-difference formation ledger; all 80 cases and four cells')
        require(proof['elapsed_seconds'] < 300, 'verification time budget')
        payload = json.dumps(proof, indent=2) + '\n'
        require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) + len(payload.encode()) < 33554432, 'proof storage budget')
        with proof_path.open('x') as stream:
            stream.write(payload)
        print('verified all 80 cases and 2560 saved boundary ledgers')
    except BaseException as error:
        failure = root / 'verification-failure.json'
        if root.is_dir() and not failure.exists():
            evidence = dict(status='failed', error=f'{type(error).__name__}: {error}',
                            files_sha256_before=before, input_sha256=bound)
            for field, paths in (('files_sha256_after', {name: root / name for name in names}),
                                 ('input_sha256_after', {name: Path(name) for name in bound})):
                hashes, errors = {}, {}
                for name, path in paths.items():
                    try:
                        hashes[name] = digest(path)
                    except Exception as failure_error:
                        errors[name] = f'{type(failure_error).__name__}: {failure_error}'
                evidence[field] = hashes
                if errors:
                    evidence[field + '_errors'] = errors
            with failure.open('x') as stream:
                stream.write(json.dumps(evidence, indent=2) + '\n')
        raise


if __name__ == '__main__':
    main()
