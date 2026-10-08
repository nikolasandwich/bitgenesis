"""Study031 independent backward terminal-event probability verification."""
from copy import deepcopy
from fractions import Fraction
from functools import cache
import json
import math
from pathlib import Path
from time import monotonic

from scripts.verify_v4_child_energy import GENOTYPES, require, same, validate_selection

OUTPUT = Path('data/v4-study-031')


def terminal_probability(steps, energy, target):
    """Backward expectation of a terminal indicator, with absorbing boundaries."""
    require(type(steps) is int and 0 <= steps <= 32, 'terminal horizon')
    require(type(energy) is int and energy >= 0, 'terminal energy')
    require(target in ('hit', 'dead') or type(target) is int and 1 <= target <= 15,
            'terminal target')
    return _terminal(steps, energy, target)


@cache
def _terminal(steps, energy, target):
    if energy == 0:
        return Fraction(target == 'dead')
    if energy >= 16:
        return Fraction(target == 'hit')
    if steps == 0:
        return Fraction(energy == target)
    return (Fraction(63, 64) * _terminal(steps-1, energy-1, target)
            + Fraction(1, 64) * _terminal(steps-1, energy+7, target))


def curve(max_horizon=32):
    require(type(max_horizon) is int and 0 <= max_horizon <= 32, 'horizon integer 0..32')
    result = []
    previous_hit = previous_dead = Fraction(0)
    for horizon in range(max_horizon+1):
        hit = terminal_probability(horizon, 5, 'hit')
        dead = terminal_probability(horizon, 5, 'dead')
        alive = [terminal_probability(horizon, 5, energy) for energy in range(1, 16)]
        surviving = sum(alive, Fraction(0))
        require(hit + dead + surviving == 1, 'terminal probability mass')
        require(hit >= previous_hit and dead >= previous_dead, 'absorbing cumulative probabilities')
        require(all(p >= 0 for p in alive), 'nonnegative terminal probabilities')
        result.append(dict(horizon=horizon, alive=list(map(str, alive)),
                           first_hit=str(hit-previous_hit), first_death=str(dead-previous_dead),
                           hit=str(hit), dead=str(dead), surviving=str(surviving)))
        previous_hit, previous_dead = hit, dead
    return result


def build(timing_records):
    require(type(timing_records) is list and len(timing_records) == 52, '52 timing records')
    for record in timing_records:
        require(type(record) is dict and type(record.get('selection')) is dict, 'timing selection')
        require(type(record.get('birth_tick')) is int and 6 <= record['birth_tick'] <= 22,
                'fixed birth tick range')
        same(record['birth_tick'], record['selection'].get('tick'), 'birth selection tick')
    validate_selection([record['selection'] for record in timing_records])
    distribution = curve()
    cohort = []
    for record in timing_records:
        horizon = 32-record['birth_tick']
        row = distribution[horizon]
        cohort.append(dict(selection=deepcopy(record['selection']), horizon=horizon,
                           **{key: row[key] for key in ('hit', 'dead', 'surviving')}))
    summary = []
    for genotype in GENOTYPES:
        for exchange in (False, True):
            group = [r for r in cohort if r['selection']['genotype'] == genotype
                     and r['selection']['exchange'] == exchange]
            totals = {key: sum((Fraction(r[key]) for r in group), Fraction(0))
                      for key in ('hit', 'dead', 'surviving')}
            summary.append(dict(genotype=genotype, exchange=exchange, n=len(group),
                                expected_hits=str(totals['hit']),
                                **{'mean_'+key: str(value/len(group)) for key, value in totals.items()}))
    return dict(curve=distribution, cohort=cohort), summary


def check_budget(root, started, extra=0):
    require(monotonic()-started < 60, 'verification time budget')
    require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) + extra < 8388608,
            'verification storage budget')


def main():
    from scripts.energy_probability_inputs import bindings, read, digest, input_paths
    root = OUTPUT
    proof_path = root / 'independent-verification.json'
    require(not proof_path.exists(), 'proof already exists')
    started = monotonic()
    paths, input_before, before, errors = [], {}, {}, {}
    completed = 0
    names = ('metadata.json', 'records.json', 'summary.json')

    def snapshot(mapping, failures):
        result = {}
        for name, path in mapping.items():
            try:
                result[name] = digest(path)
            except Exception as error:
                failures[name] = f'{type(error).__name__}: {error}'
        return result

    try:
        paths = input_paths(errors)
        input_before = snapshot({p: Path(p) for p in paths}, errors)
        before = snapshot({n: root / n for n in names}, errors)
        bound = bindings()
        same(len(bound), 503, '503 bound inputs')
        same(paths, sorted(bound), 'complete inventory')
        same(input_before, bound, 'readable inputs')
        same(errors, {}, 'readable initial inventory and outputs')
        same(digest(Path(__file__)), bound['scripts/verify_v4_energy_probability.py'], 'running verifier')
        meta = read(root / 'metadata.json')
        fixed = dict(status='complete', planned_horizons=33, completed_horizons=33,
                     cohort_states=52, max_horizon=32, new_full_world_steps=0, new_phase_transitions=0,
                     new_environment_sources=0, reused_environment_sources=20, selected_environment_sources=11,
                     new_independent_initial_worlds=0, time_limit_seconds=60, storage_limit_bytes=8388608)
        expected = set(fixed) | {'git_commit', 'elapsed_seconds', 'input_paths', 'input_sha256',
                                 'input_sha256_after', 'output_sha256'}
        optional = {'input_inventory_errors', 'input_read_errors_before'}
        require(type(meta) is dict and expected <= set(meta) <= expected | optional, 'metadata schema')
        for key in optional & set(meta):
            same(meta[key], {}, 'successful ' + key)
        for key, value in fixed.items():
            same(meta[key], value, 'metadata ' + key)
        commit = meta['git_commit']
        require(type(commit) is str and len(commit) == 40 and all(c in '0123456789abcdef' for c in commit),
                'recorded commit')
        elapsed = meta['elapsed_seconds']
        require(type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed < 60, 'run time budget')
        same(meta['input_paths'], paths, 'metadata paths')
        same(meta['input_sha256'], bound, 'before bindings')
        same(meta['input_sha256_after'], bound, 'after bindings')
        same(meta['output_sha256'], {n: before[n] for n in names[1:]}, 'output hashes')
        require({p.name for p in root.iterdir()} == set(names), 'exclusive output inventory')
        check_budget(root, started)
        records, summary = build(read(Path('data/v4-study-030/records.json')))
        completed = len(records['curve'])
        same(completed, 33, '33 exact horizons')
        same(read(root / 'records.json'), records, 'independent 33 distributions and 52 cohort mappings')
        same(read(root / 'summary.json'), summary, 'independent four-cell linear expectations')
        same(bindings(), bound, 'inputs unchanged')
        after_errors = {}
        input_after = snapshot({p: Path(p) for p in paths}, after_errors)
        same(input_after, input_before, 'all inputs unchanged')
        same(snapshot({n: root / n for n in names}, after_errors), before, 'outputs unchanged')
        same(after_errors, {}, 'readable outputs after')
        require({p.name for p in root.iterdir()} == set(names), 'exclusive output inventory after')
        proof = dict(status='verified', input_files=503, planned_horizons=33, completed_horizons=completed,
                     cohort_states=52, max_horizon=32, summary_cells=4,
                     new_full_world_steps=0, new_phase_transitions=0, new_environment_sources=0,
                     reused_environment_sources=20, selected_environment_sources=11, new_independent_initial_worlds=0,
                     files_sha256=before, verifier_sha256=digest(Path(__file__)), input_paths=paths,
                     input_sha256=input_before, input_sha256_after=input_after,
                     elapsed_seconds=monotonic()-started, time_limit_seconds=60, storage_limit_bytes=8388608,
                     scope='independent Fraction backward terminal indicators; 33 complete distributions, 52 mappings and four linear expectations')
        payload = json.dumps(proof, indent=2, allow_nan=False) + '\n'
        check_budget(root, started, len(payload.encode()))
        with proof_path.open('x') as stream:
            stream.write(payload)
        check_budget(root, started)
        print('verified 33 exact distributions, 52 cohort mappings, four summaries and 503 inputs')
    except BaseException as error:
        failure = root / 'verification-failure.json'
        if root.is_dir() and not failure.exists():
            after_errors = {}
            evidence = dict(status='failed', error=f'{type(error).__name__}: {error}', completed_horizons=completed,
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
