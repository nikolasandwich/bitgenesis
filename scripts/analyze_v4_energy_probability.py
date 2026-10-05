"""Study031: integer path weights for an isolated absorbing energy process."""
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import subprocess
import time

from scripts.run_v4_north_energy import SELECTION_KEYS, ordered_selection, require

OUTPUT = Path('data/v4-study-031')


def _advance(alive, hit, dead):
    """Advance integer weights; absorbed paths acquire every possible next ticket."""
    following = [0]*15
    first_hit = first_death = 0
    for energy, count in enumerate(alive, 1):
        for next_energy, weight in ((energy-1, 63), (energy+7, 1)):
            paths = count*weight
            if next_energy == 0:
                first_death += paths
            elif next_energy >= 16:
                first_hit += paths
            else:
                following[next_energy-1] += paths
    return following, hit*64+first_hit, dead*64+first_death, first_hit, first_death


def curve(max_horizon=32):
    require(type(max_horizon) is int and 0 <= max_horizon <= 32, 'horizon integer0..32')
    alive = [0]*15
    alive[4] = 1
    hit = dead = 0
    denominator = 1
    rows = []
    for horizon in range(max_horizon+1):
        first_hit = first_death = 0
        if horizon:
            alive, hit, dead, first_hit, first_death = _advance(alive, hit, dead)
            denominator *= 64
        require(hit+dead+sum(alive) == denominator, 'integer probability conservation')
        def serialize(count):
            return str(Fraction(count, denominator))
        rows.append(dict(horizon=horizon, alive=[serialize(n) for n in alive],
                         first_hit=serialize(first_hit), first_death=serialize(first_death),
                         hit=serialize(hit), dead=serialize(dead), surviving=serialize(sum(alive))))
    return rows


def build(timing_records):
    require(type(timing_records) is list and len(timing_records) == 52, 'complete52 timing records')
    for record in timing_records:
        require(type(record) is dict and type(record.get('selection')) is dict and
                set(record['selection']) == set(SELECTION_KEYS), 'complete nine selection fields')
        require(type(record.get('birth_tick')) is int and record['birth_tick'] == record['selection']['tick'] and
                6 <= record['birth_tick'] <= 22, 'birth tick and fixed10..26 horizon')
    ordered_selection([r['selection'] for r in timing_records])
    rows = curve()
    cohort = []
    for record in timing_records:
        horizon = 32-record['birth_tick']
        cohort.append(dict(selection=deepcopy(record['selection']), horizon=horizon,
                           **{k: rows[horizon][k] for k in ('hit','dead','surviving')}))
    summary = []
    for genotype in ('homogeneous','heterogeneous'):
        for exchange in (False, True):
            chosen = [r for r in cohort if (r['selection']['genotype'], r['selection']['exchange']) == (genotype, exchange)]
            sums = {k: sum((Fraction(r[k]) for r in chosen), Fraction(0)) for k in ('hit','dead','surviving')}
            summary.append(dict(genotype=genotype, exchange=exchange, n=len(chosen),
                                expected_hits=str(sums['hit']),
                                **{'mean_'+k: str(v/len(chosen)) for k,v in sums.items()}))
    return dict(curve=rows, cohort=cohort), summary


def main():
    from scripts.energy_probability_inputs import bindings, input_paths, read, save, digest
    require(not subprocess.check_output(['git','status','--porcelain'], text=True).strip(), 'clean launch')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    inventory = []
    meta = dict(status='running', planned_horizons=33, completed_horizons=0, cohort_states=52, max_horizon=32,
                new_full_world_steps=0, new_phase_transitions=0, new_environment_sources=0,
                reused_environment_sources=20, selected_environment_sources=11, new_independent_initial_worlds=0,
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
        save(OUTPUT/'records.json', dict(curve=[], cohort=[]))
        before = bindings()
        require(before == meta['input_sha256'] and len(before) == 503, 'validated503 initial inputs')
        budget()
        records, summary = build(read(Path('data/v4-study-030/records.json')))
        save(OUTPUT/'records.json', records)
        meta.update(completed_horizons=len(records['curve']), elapsed_seconds=time.monotonic()-started)
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
