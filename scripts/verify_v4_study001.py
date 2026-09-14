"""Verify complete activity cohort and exact registered window observations."""
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from bitgenesis.v4.driven_audit import audit


def windows(rows):
    if [r['tick'] for r in rows]!=list(range(1,501)):
        raise ValueError('incomplete or duplicate transition window')
    result=[]
    for low,high in ((1,100),(101,250),(251,500)):
        group=rows[low-1:high]
        result.append(dict(start=low,end=high,
            active_fraction=str(Fraction(sum(bool(r['interaction']['bonds']) for r in group),len(group))),
            mean_bonds=str(Fraction(sum(len(r['interaction']['bonds']) for r in group),len(group))),
            mean_largest_component=str(Fraction(sum(max(map(len,r['components']),default=0) for r in group),len(group))),
            imported=sum(r['imported'] for r in group),rejected_import=sum(r['rejected_import'] for r in group),
            leakage=sum(r['leakage'] for r in group),bond_cost=sum(r['interaction']['spent'] for r in group)))
    return result


def verify(root):
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    meta=read(root/'metadata.json')
    if (meta['status'],meta['completed_runs'],meta['planned_runs'])!=('complete',20,20):
        raise ValueError('incomplete study')
    if meta['protocol_sha256']!=sha256(Path('experiments/v4/study-001.md').read_bytes()).hexdigest():
        raise ValueError('protocol mismatch')
    rows=read(root/'results.json')
    expected=set(product(range(91000,91005),(0,500),(False,True)))
    if len(rows)!=20 or {(r['seed'],r['drive'],r['exchange']) for r in rows}!=expected:
        raise ValueError('cohort grid mismatch')
    checks=[]
    initial_by_seed={}
    rng_by_seed={}
    observations={}
    for r in rows:
        name=f"seed-{r['seed']}-drive-{r['drive']}-exchange-{int(r['exchange'])}"
        directory=root/name
        m=read(directory/'metadata.json')
        config=dict(seed=r['seed'],steps=500,width=16,height=16,occupancy=750,max_energy=64,
                    bond_cost=1,exchange=r['exchange'],max_site_records=128256,
                    drive_per_thousand=r['drive'],drive_amount=8,capacity=64,leak=1)
        if any(m[k]!=v for k,v in config.items()) or m['git_commit']!=meta['git_commit'] or m['git_dirty'] is not False:
            raise ValueError('configuration/source mismatch')
        checked=audit(directory)
        if checked!=read(directory/'audit.json') or checked['summary']!=r['summary']:
            raise ValueError('audit/summary mismatch')
        initial=read(directory/'initial.json')
        final_rng=read(directory/'final.json')['drive_rng']
        if r['seed'] in initial_by_seed and (initial_by_seed[r['seed']]!=initial or rng_by_seed[r['seed']]!=final_rng):
            raise ValueError('paired initialization/random counts mismatch')
        initial_by_seed[r['seed']]=initial
        rng_by_seed[r['seed']]=final_rng
        with (directory/'steps.jsonl').open() as stream:
            observation=windows([json.loads(line) for line in stream])
        observations[(r['seed'],r['drive'],r['exchange'])]=observation[-1]
        checks.append(dict(directory=name,windows=observation,audit=checked))
    contrasts=[]
    for seed in range(91000,91005):
        for factor,fixed_values in (('drive',(False,True)),('exchange',(0,500))):
            for fixed in fixed_values:
                low=observations[(seed,0,fixed)] if factor=='drive' else observations[(seed,fixed,False)]
                high=observations[(seed,500,fixed)] if factor=='drive' else observations[(seed,fixed,True)]
                contrasts.append(dict(seed=seed,factor=factor,fixed=fixed,
                    late_active_fraction_difference=str(Fraction(high['active_fraction'])-Fraction(low['active_fraction']))))
    return dict(scope='complete cohort, independent dynamics and registered windows; fixed-site activity only',
                checks=checks,contrasts=contrasts,
                results_sha256=sha256((root/'results.json').read_bytes()).hexdigest(),
                script_sha256=sha256(Path(__file__).read_bytes()).hexdigest())


if __name__=='__main__':
    root=Path('data/v4-study-001')
    result=verify(root)
    with (root/'verification.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print('Verified20 runs and60 windows')
