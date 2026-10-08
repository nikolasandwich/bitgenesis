"""Study032: exact eventual absorption of the isolated energy process.

Every block of 15 empty inputs has probability (63/64)**15 and forces
absorption. Thus P(T>15n) <= (1-(63/64)**15)**n and E[T] <= 15/(63/64)**15.
"""
from fractions import Fraction
from pathlib import Path
import subprocess
import time

OUTPUT = Path('data/v4-study-032')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def gauss_jordan(matrix, rhs):
    """Solve a square exact system with one or more right-hand columns."""
    n = len(matrix)
    require(n > 0 and len(rhs) == n and all(len(row) == n for row in matrix), 'square system')
    width = len(rhs[0])
    require(width > 0 and all(len(row) == width for row in rhs), 'right hand dimensions')
    augmented = [[Fraction(v) for v in a+b] for a,b in zip(matrix,rhs)]
    for column in range(n):
        pivot = next((i for i in range(column,n) if augmented[i][column]), None)
        require(pivot is not None, 'singular system')
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [v/scale for v in augmented[column]]
        for row in range(n):
            if row != column:
                scale = augmented[row][column]
                augmented[row] = [v-scale*w for v,w in zip(augmented[row],augmented[column])]
    return [row[n:] for row in augmented]


def solve_states():
    matrix = [[0]*15 for _ in range(15)]
    rhs = []
    for e in range(1,16):
        matrix[e-1][e-1] = 64
        if e > 1:
            matrix[e-1][e-2] = -63
        if e+7 < 16:
            matrix[e-1][e+6] = -1
        rhs.append([int(e+7 >= 16),64])
    values = gauss_jordan(matrix,rhs)
    hit = {0:Fraction(0), **{e:Fraction(1) for e in range(16,23)}}
    mean = {e:Fraction(0) for e in (0,*range(16,23))}
    for e,(h,t) in enumerate(values,1):
        hit[e],mean[e] = h,t
    states = []
    for e in range(1,16):
        h,t = hit[e],mean[e]
        d = 1-h
        require(0 <= h <= 1 and 0 <= d <= 1 and h+d == 1 and t > 0, 'state probability/time bounds')
        require(64*h == 63*hit[e-1]+hit[e+7], 'hit Bellman equation')
        require(64*t == 64+63*mean[e-1]+mean[e+7], 'time Bellman equation')
        states.append(dict(energy=e,hit=str(h),dead=str(d),mean_steps=str(t)))
    return states


def rational(value):
    require(type(value) is str, 'rational string')
    result = Fraction(value)
    require(str(result) == value, 'canonical rational')
    return result


def build(prior_records):
    states = solve_states()
    rows = prior_records['curve']
    require(type(rows) is list and len(rows) == 33, 'complete33 finite curve')
    hits = [rational(s['hit']) for s in states]
    means = [rational(s['mean_steps']) for s in states]
    finite = []
    elapsed = Fraction(0)
    for horizon,row in enumerate(rows):
        require(type(row['horizon']) is int and row['horizon'] == horizon, 'ordered horizons0..32')
        require(type(row['alive']) is list and len(row['alive']) == 15, 'fifteen alive weights')
        alive = [rational(v) for v in row['alive']]
        hit,dead,surviving = (rational(row[k]) for k in ('hit','dead','surviving'))
        require(all(v >= 0 for v in alive) and 0 <= hit <= 1 and 0 <= dead <= 1 and
                sum(alive) == surviving and hit+dead+surviving == 1, 'finite probability conservation')
        additional = sum((a*h for a,h in zip(alive,hits)),Fraction(0))
        remaining = sum((a*t for a,t in zip(alive,means)),Fraction(0))
        require(0 <= additional <= surviving and remaining >= 0, 'bounded tail contributions')
        require(hit+additional == hits[4], 'finite hit reconstruction')
        require(elapsed+remaining == means[4], 'finite mean reconstruction')
        finite.append(dict(horizon=horizon,hit_reconstructed=str(hit+additional),
                           mean_steps_reconstructed=str(elapsed+remaining),additional_hit=str(additional),
                           remaining_mean_steps=str(remaining)))
        elapsed += surviving
    summary = dict(initial_energy=5,eventual_hit=states[4]['hit'],eventual_dead=states[4]['dead'],
                   mean_absorption_steps=states[4]['mean_steps'],at_32_hit=rows[32]['hit'],
                   additional_hit_after_32=finite[32]['additional_hit'],
                   remaining_mean_steps_after_32=finite[32]['remaining_mean_steps'],at_32_surviving=rows[32]['surviving'])
    return dict(states=states,finite_checks=finite),summary


def main():
    from scripts.energy_absorption_inputs import bindings, input_paths, read, save, digest
    require(not subprocess.check_output(['git','status','--porcelain'], text=True).strip(), 'clean launch')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    inventory = []
    meta = dict(status='running', planned_states=15, completed_states=0, finite_horizons=33, initial_energy=5,
                new_full_world_steps=0, new_phase_transitions=0, new_environment_sources=0,
                new_independent_initial_worlds=0,
                time_limit_seconds=60, storage_limit_bytes=8388608)
    def budget():
        require(time.monotonic()-started < 60 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file()) < 8388608,
                'bounded execution')
    def hashes():
        return {str(p.relative_to(OUTPUT)): digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p != OUTPUT/'metadata.json'}
    def input_hashes(error_key):
        values = {}
        meta[error_key] = {}
        for path in inventory:
            try:
                values[path] = digest(path)
            except BaseException as exc:
                meta[error_key][path] = repr(exc)
        return values
    try:
        meta['git_commit'] = subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip()
        meta['input_inventory_errors'] = {}
        inventory = input_paths(meta['input_inventory_errors'])
        meta['input_paths'] = inventory
        meta['input_sha256'] = input_hashes('input_read_errors_before')
        save(OUTPUT/'metadata.json', meta)
        save(OUTPUT/'records.json', dict(states=[], finite_checks=[]))
        before = bindings()
        require(before == meta['input_sha256'] and len(before) == 515, 'validated515 initial inputs')
        budget()
        records, summary = build(read(Path('data/v4-study-031/records.json')))
        save(OUTPUT/'records.json', records)
        meta.update(completed_states=len(records['states']), elapsed_seconds=time.monotonic()-started)
        save(OUTPUT/'metadata.json', meta)
        budget()
        save(OUTPUT/'summary.json', summary)
        meta['input_sha256_after'] = bindings()
        require(before == meta['input_sha256_after'], 'unchanged inputs')
        meta.update(status='complete', elapsed_seconds=time.monotonic()-started, output_sha256=hashes())
        budget()
        save(OUTPUT/'metadata.json', meta)
        budget()
    except BaseException as exc:
        meta.update(status='failed', error=repr(exc), elapsed_seconds=time.monotonic()-started)
        try:
            meta['input_sha256_after'] = bindings()
            if meta.get('input_sha256') != meta['input_sha256_after']:
                meta['finalization_error'] = 'inputs changed during failure'
        except BaseException as err:
            meta['finalization_error'] = repr(err)
            meta['input_sha256_after'] = input_hashes('input_read_errors')
        try:
            meta['output_sha256'] = hashes()
        except BaseException as err:
            meta['output_hash_error'] = repr(err)
        save(OUTPUT/'metadata.json', meta)
        raise


if __name__ == '__main__':
    main()
