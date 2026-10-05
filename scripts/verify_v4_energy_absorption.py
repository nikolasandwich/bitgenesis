"""Study032 independent integer boundary recurrence and Cramer verification."""
from fractions import Fraction
import json
import math
from pathlib import Path
from time import monotonic

from scripts.verify_v4_child_energy import require, same

OUTPUT = Path('data/v4-study-032')


def determinant(matrix):
    """Integer Bareiss determinant with row pivoting; no floating arithmetic."""
    n = len(matrix)
    require(n > 0 and all(len(row) == n for row in matrix), 'square matrix')
    require(all(type(x) is int for row in matrix for x in row), 'integer matrix')
    a = [list(row) for row in matrix]
    sign, previous = 1, 1
    for k in range(n-1):
        pivot = next((i for i in range(k, n) if a[i][k]), None)
        if pivot is None:
            return 0
        if pivot != k:
            a[k], a[pivot] = a[pivot], a[k]
            sign = -sign
        for i in range(k+1, n):
            for j in range(k+1, n):
                numerator = a[k][k]*a[i][j] - a[i][k]*a[k][j]
                require(numerator % previous == 0, 'Bareiss exact division')
                a[i][j] = numerator // previous
            a[i][k] = 0
        previous = a[k][k]
    return sign*a[-1][-1]


def cramer(matrix, rhs):
    require(len(rhs) == len(matrix) and all(type(x) is int for x in rhs), 'integer rhs')
    denominator = determinant(matrix)
    require(denominator != 0, 'singular boundary system')
    return [Fraction(determinant([[rhs[i] if j == col else x for j, x in enumerate(row)]
                                  for i, row in enumerate(matrix)]), denominator)
            for col in range(len(matrix))]


def boundary_forms(forcing):
    """Return affine forms at energies 0..22 in seven unknown values 1..7."""
    require(type(forcing) is int, 'integer forcing')
    forms = [([0]*7, 0)]
    forms.extend(([int(i == j) for i in range(7)], 0) for j in range(7))
    for e in range(1, 16):
        a, ac = forms[e]
        b, bc = forms[e-1]
        forms.append(([64*x-63*y for x, y in zip(a, b)], 64*ac-63*bc-forcing))
    return forms


def rational(value):
    require(type(value) is str, 'fraction string')
    result = Fraction(value)
    same(str(result), value, 'canonical fraction')
    return result


def validate_states(states):
    require(type(states) is list and len(states) == 15, '15 states')
    h, t = [Fraction(0)], [Fraction(0)]
    for e, row in enumerate(states, 1):
        same(set(row), {'energy', 'hit', 'dead', 'mean_steps'}, 'state schema')
        same(row['energy'], e, 'state energy')
        hit, dead, mean = [rational(row[k]) for k in ('hit', 'dead', 'mean_steps')]
        require(0 <= hit <= 1 and 0 <= dead <= 1 and hit+dead == 1 and mean > 0,
                'state probabilities and time')
        h.append(hit)
        t.append(mean)
    h.extend([Fraction(1)]*7)
    t.extend([Fraction(0)]*7)
    for e in range(1, 16):
        same(64*h[e]-63*h[e-1]-h[e+7], Fraction(0), 'hit Bellman equation')
        same(64*t[e]-63*t[e-1]-t[e+7], Fraction(64), 'time Bellman equation')


def solve_states():
    solutions = []
    for forcing, boundary in ((0, 1), (64, 0)):
        forms = boundary_forms(forcing)
        seeds = cramer([a for a, c in forms[16:23]], [boundary-c for a, c in forms[16:23]])
        solutions.append([sum((a*x for a, x in zip(coeff, seeds)), Fraction(const))
                          for coeff, const in forms[1:16]])
    states = [dict(energy=e, hit=str(h), dead=str(1-h), mean_steps=str(t))
              for e, (h, t) in enumerate(zip(*solutions), 1)]
    validate_states(states)
    return states


def build(prior_records):
    require(type(prior_records) is dict and type(prior_records.get('curve')) is list
            and len(prior_records['curve']) == 33, '33 prior horizons')
    require(type(prior_records.get('cohort')) is list and len(prior_records['cohort']) == 52, '52 prior cohort')
    states = solve_states()
    hits = [rational(s['hit']) for s in states]
    means = [rational(s['mean_steps']) for s in states]
    checks, elapsed = [], Fraction(0)
    for horizon, row in enumerate(prior_records['curve']):
        same(row['horizon'], horizon, 'prior horizon order')
        require(type(row['alive']) is list and len(row['alive']) == 15, '15 prior alive masses')
        alive = [rational(x) for x in row['alive']]
        hit, dead, surviving = [rational(row[k]) for k in ('hit', 'dead', 'surviving')]
        require(all(x >= 0 for x in alive) and min(hit, dead, surviving) >= 0, 'nonnegative prior mass')
        same(sum(alive, Fraction(0)), surviving, 'surviving mass')
        same(hit+dead+surviving, Fraction(1), 'prior probability conservation')
        additional = sum((a*h for a, h in zip(alive, hits)), Fraction(0))
        remaining = sum((a*t for a, t in zip(alive, means)), Fraction(0))
        require(0 <= additional <= surviving and remaining >= 0, 'tail contribution bounds')
        same(hit+additional, hits[4], 'eventual hit reconstruction')
        same(elapsed+remaining, means[4], 'mean time reconstruction')
        checks.append(dict(horizon=horizon, hit_reconstructed=str(hit+additional),
                           mean_steps_reconstructed=str(elapsed+remaining), additional_hit=str(additional),
                           remaining_mean_steps=str(remaining)))
        elapsed += surviving
    last = prior_records['curve'][-1]
    summary = dict(initial_energy=5, eventual_hit=states[4]['hit'], eventual_dead=states[4]['dead'],
                   mean_absorption_steps=states[4]['mean_steps'], at_32_hit=last['hit'],
                   additional_hit_after_32=checks[-1]['additional_hit'],
                   remaining_mean_steps_after_32=checks[-1]['remaining_mean_steps'], at_32_surviving=last['surviving'])
    return dict(states=states, finite_checks=checks), summary


def check_budget(root, started, extra=0):
    require(monotonic()-started < 60, 'verification time budget')
    require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) + extra < 8388608,
            'verification storage budget')


def main():
    from scripts.energy_absorption_inputs import bindings, read, digest, input_paths
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
        same(len(bound), 515, '515 bound inputs')
        same(paths, sorted(bound), 'complete inventory')
        same(input_before, bound, 'readable inputs')
        same(errors, {}, 'readable initial inventory and outputs')
        same(digest(Path(__file__)), bound['scripts/verify_v4_energy_absorption.py'], 'running verifier')
        meta = read(root / 'metadata.json')
        fixed = dict(status='complete', planned_states=15, completed_states=15,
                     finite_horizons=33, initial_energy=5, new_full_world_steps=0, new_phase_transitions=0,
                     new_environment_sources=0,
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
        records, summary = build(read(Path('data/v4-study-031/records.json')))
        completed = len(records['states'])
        same(completed, 15, '15 exact states')
        same(len(records['finite_checks']), 33, '33 exact reconstructions')
        same(read(root / 'records.json'), records, 'independent 15 states and 33 finite reconstructions')
        same(read(root / 'summary.json'), summary, 'independent exact absorption summary')
        same(bindings(), bound, 'inputs unchanged')
        after_errors = {}
        input_after = snapshot({p: Path(p) for p in paths}, after_errors)
        same(input_after, input_before, 'all inputs unchanged')
        same(snapshot({n: root / n for n in names}, after_errors), before, 'outputs unchanged')
        same(after_errors, {}, 'readable outputs after')
        require({p.name for p in root.iterdir()} == set(names), 'exclusive output inventory after')
        proof = dict(status='verified', input_files=515, planned_states=15, completed_states=completed,
                     finite_horizons=33, initial_energy=5,
                     new_full_world_steps=0, new_phase_transitions=0, new_environment_sources=0,
                     new_independent_initial_worlds=0,
                     files_sha256=before, verifier_sha256=digest(Path(__file__)), input_paths=paths,
                     input_sha256=input_before, input_sha256_after=input_after,
                     elapsed_seconds=monotonic()-started, time_limit_seconds=60, storage_limit_bytes=8388608,
                     scope='independent seven-boundary affine recurrence, integer Bareiss determinants and Cramer fractions; 15 states and 33 finite reconstructions')
        payload = json.dumps(proof, indent=2, allow_nan=False) + '\n'
        check_budget(root, started, len(payload.encode()))
        with proof_path.open('x') as stream:
            stream.write(payload)
        check_budget(root, started)
        print('verified 15 exact states, 33 finite reconstructions and 515 inputs')
    except BaseException as error:
        failure = root / 'verification-failure.json'
        if root.is_dir() and not failure.exists():
            after_errors = {}
            evidence = dict(status='failed', error=f'{type(error).__name__}: {error}', completed_states=completed,
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
