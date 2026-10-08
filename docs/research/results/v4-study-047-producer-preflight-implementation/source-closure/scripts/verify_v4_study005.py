"""Verify complete activity cohort and exact registered window observations."""
from fractions import Fraction
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from bitgenesis.v4.hereditary_audit import audit


def programs(units):
    return Counter(tuple(u['program']) for u in units if u is not None)


def table(counts):
    return [dict(program=list(p),count=n) for p,n in sorted(counts.items())]


def windows(rows,initial_set):
    if [r['tick'] for r in rows]!=list(range(1,501)):
        raise ValueError('incomplete or duplicate transition window')
    result=[]
    for low,high in ((1,100),(101,500)):
        group=rows[low-1:high]
        counts=[programs(r['units']) for r in group]
        result.append(dict(start=low,end=high,
            mean_occupied_fraction=str(Fraction(sum(sum(c.values()) for c in counts),256*len(group))),
            mean_distinct_programs=str(Fraction(sum(len(c) for c in counts),len(group))),
            mean_initially_absent_units=str(Fraction(sum(sum(n for p,n in c.items() if p not in initial_set) for c in counts),len(group))),
            formations=sum(sum(p['reason']=='formed' for p in r['material']['proposals']) for r in group),
            dissolutions=sum(len(r['material']['dissolved']) for r in group),
            mutations=sum(sum(p.get('mutated',False) for p in r['material']['proposals']) for r in group),
            imported=sum(r['imported'] for r in group),rejected_import=sum(r['rejected_import'] for r in group),
            leakage=sum(r['driven']['leakage'] for r in group),bond_cost=sum(r['driven']['interaction']['spent'] for r in group),
            construction_cost=sum(r['material']['construction_spent'] for r in group),copy_cost=sum(r['material']['copy_spent'] for r in group)))
    return result


def verify(root):
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    meta=read(root/'metadata.json')
    if (meta['status'],meta['completed_runs'],meta['planned_runs'])!=('complete',20,20):
        raise ValueError('incomplete study')
    if meta['protocol_sha256']!=sha256(Path('experiments/v4/study-005.md').read_bytes()).hexdigest():
        raise ValueError('protocol mismatch')
    rows=read(root/'results.json')
    expected=set(product(range(96000,96005),(250,500),(0,100)))
    if len(rows)!=20 or {(r['seed'],r['drive'],r['mutation']) for r in rows}!=expected:
        raise ValueError('cohort grid mismatch')
    source_hashes={p.name:sha256(p.read_bytes()).hexdigest() for p in Path('src/bitgenesis/v4').glob('*.py')}
    checks=[]
    initial_by_seed={}
    rng_by_seed={}
    observations={}
    for r in rows:
        name=f"seed-{r['seed']}-drive-{r['drive']}-mutation-{r['mutation']}"
        directory=root/name
        m=read(directory/'metadata.json')
        config=dict(seed=r['seed'],steps=500,width=16,height=16,occupancy=250,max_energy=64,
                    bond_cost=1,exchange=True,max_site_records=128256,
                    drive_per_thousand=r['drive'],drive_amount=8,capacity=64,leak=1,initial_raw=1,threshold=16,construction_cost=4,copy_cost=1,
                    program_mode='random',mutation_per_thousand=r['mutation'])
        if any(m[k]!=v for k,v in config.items()) or m['git_commit']!=meta['git_commit'] or m['git_dirty'] is not False:
            raise ValueError('configuration/source mismatch')
        if m['source_sha256']!=source_hashes:
            raise ValueError('source byte mismatch')
        checked=audit(directory)
        if checked!=read(directory/'audit.json') or checked['summary']!=r['summary']:
            raise ValueError('audit/summary mismatch')
        initial=read(directory/'initial.json')
        final=read(directory/'final.json')
        final_rng=[final[k] for k in ('drive_rng','direction_rng','mutation_rng')]
        if r['seed'] in initial_by_seed and (initial_by_seed[r['seed']]!=initial or rng_by_seed[r['seed']]!=final_rng):
            raise ValueError('paired initialization/random counts mismatch')
        initial_by_seed[r['seed']]=initial
        rng_by_seed[r['seed']]=final_rng
        with (directory/'steps.jsonl').open() as stream:
            trajectory=[json.loads(line) for line in stream]
        initial_counts=programs(initial['units'])
        final_counts=programs(final['units'])
        observation=windows(trajectory,set(initial_counts))
        if r['mutation']==0 and any(set(programs(t['units']))-set(initial_counts) for t in trajectory):
            raise ValueError('no-mutation negative control')
        observations[(r['seed'],r['drive'],r['mutation'])]=Fraction(sum(n for p,n in final_counts.items() if p not in initial_counts),256)
        checks.append(dict(directory=name,windows=observation,audit=checked,
            initial_program_counts=table(initial_counts),final_program_counts=table(final_counts),
            final_material_counts=[sum(u is not None and u['material']==label for u in final['units']) for label in range(4)],
            final_initially_absent_fraction=str(observations[r['seed'],r['drive'],r['mutation']])))
        print(f'Verified {name}',flush=True)
    contrasts=[]
    for seed,drive in product(range(96000,96005),(250,500)):
        contrasts.append(dict(seed=seed,drive=drive,difference=str(observations[seed,drive,100]-observations[seed,drive,0])))
    means=[dict(drive=drive,mean=str(sum((Fraction(r['difference']) for r in contrasts if r['drive']==drive),Fraction())/5)) for drive in (250,500)]
    return dict(scope='complete cohort, independent dynamics and registered windows; bounded program variation only',
                checks=checks,contrasts=contrasts,contrast_means=means,source_sha256=source_hashes,
                results_sha256=sha256((root/'results.json').read_bytes()).hexdigest(),
                script_sha256=sha256(Path(__file__).read_bytes()).hexdigest())


if __name__=='__main__':
    root=Path('data/v4-study-005')
    result=verify(root)
    with (root/'verification.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print('Verified20 runs and40 windows')
