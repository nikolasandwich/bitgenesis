"""Verify complete growing cohort and exact registered window observations."""
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from bitgenesis.v4.growing_audit import audit


def spatial(units, width=16, height=16):
    remaining={i for i,u in enumerate(units) if u is not None}
    sizes=[]
    while remaining:
        start=min(remaining)
        remaining.remove(start)
        pending=[start]
        size=0
        while pending:
            site=pending.pop()
            size+=1
            x,y=site%width,site//width
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                target=((y+dy)%height)*width+(x+dx)%width
                if target in remaining and units[target]['material']==units[site]['material']:
                    remaining.remove(target)
                    pending.append(target)
        sizes.append(size)
    return len(sizes),max(sizes,default=0)


def windows(rows):
    if [r['tick'] for r in rows]!=list(range(1,301)):
        raise ValueError('incomplete or duplicate transition window')
    result=[]
    for low,high in ((1,100),(101,300)):
        group=rows[low-1:high]
        structures=[spatial(r['units']) for r in group]
        result.append(dict(start=low,end=high,
            occupied_fraction=str(Fraction(sum(sum(u is not None for u in r['units']) for r in group),256*len(group))),
            mean_material_labels=str(Fraction(sum(len({u['material'] for u in r['units'] if u is not None}) for r in group),len(group))),
            mean_spatial_components=str(Fraction(sum(s[0] for s in structures),len(group))),
            mean_largest_spatial_component=str(Fraction(sum(s[1] for s in structures),len(group))),
            formations=sum(sum(p['reason']=='formed' for p in r['material']['proposals']) for r in group),
            dissolutions=sum(len(r['material']['dissolved']) for r in group),
            imported=sum(r['imported'] for r in group),rejected_import=sum(r['rejected_import'] for r in group),
            leakage=sum(r['driven']['leakage'] for r in group),
            bond_cost=sum(r['driven']['interaction']['spent'] for r in group),
            construction_cost=sum(r['material']['spent'] for r in group)))
    return result


def verify(root):
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    meta=read(root/'metadata.json')
    if (meta['status'],meta['completed_runs'],meta['planned_runs'])!=('complete',40,40):
        raise ValueError('incomplete study')
    if meta['protocol_sha256']!=sha256(Path('experiments/v4/study-002.md').read_bytes()).hexdigest():
        raise ValueError('protocol mismatch')
    rows=read(root/'results.json')
    expected=set(product(range(92000,92005),(0,500),(16,65),(False,True)))
    if len(rows)!=40 or {(r['seed'],r['drive'],r['threshold'],r['exchange']) for r in rows}!=expected:
        raise ValueError('cohort grid mismatch')
    checks=[]
    initial_by_seed={}
    rng_by_seed={}
    observations={}
    for r in rows:
        name=f"seed-{r['seed']}-drive-{r['drive']}-threshold-{r['threshold']}-exchange-{int(r['exchange'])}"
        directory=root/name
        m=read(directory/'metadata.json')
        config=dict(seed=r['seed'],steps=300,width=16,height=16,occupancy=250,max_energy=64,
                    bond_cost=1,exchange=r['exchange'],max_site_records=77056,
                    drive_per_thousand=r['drive'],drive_amount=8,capacity=64,leak=1,initial_raw=1,threshold=r['threshold'],construction_cost=4)
        if any(m[k]!=v for k,v in config.items()) or m['git_commit']!=meta['git_commit'] or m['git_dirty'] is not False:
            raise ValueError('configuration/source mismatch')
        checked=audit(directory)
        if checked!=read(directory/'audit.json') or checked['summary']!=r['summary']:
            raise ValueError('audit/summary mismatch')
        initial=read(directory/'initial.json')
        final=read(directory/'final.json')
        final_rng=(final['drive_rng'],final['direction_rng'])
        if r['seed'] in initial_by_seed and (initial_by_seed[r['seed']]!=initial or rng_by_seed[r['seed']]!=final_rng):
            raise ValueError('paired initialization/random counts mismatch')
        initial_by_seed[r['seed']]=initial
        rng_by_seed[r['seed']]=final_rng
        with (directory/'steps.jsonl').open() as stream:
            trajectory=[json.loads(line) for line in stream]
            observation=windows(trajectory)
        observations[(r['seed'],r['drive'],r['threshold'],r['exchange'])]=observation[-1]
        first_zero=0 if not any(initial['units']) else next((r['tick'] for r in trajectory if not any(r['units'])),None)
        checks.append(dict(directory=name,windows=observation,first_zero_population_tick=first_zero,
                           final_population=checked['summary']['units'],final_raw=final['raw'],audit=checked))
    contrasts=[]
    for seed in range(92000,92005):
        for factor in ('formation','drive','exchange'):
            fixed_values=product((0,500),(False,True)) if factor=='formation' else product((16,65),(False,True)) if factor=='drive' else product((0,500),(16,65))
            for a,b in fixed_values:
                if factor=='formation':
                    low,high=(seed,a,65,b),(seed,a,16,b)
                elif factor=='drive':
                    low,high=(seed,0,a,b),(seed,500,a,b)
                else:
                    low,high=(seed,a,b,False),(seed,a,b,True)
                contrasts.append(dict(seed=seed,factor=factor,fixed=[a,b],
                    late_occupied_fraction_difference=str(Fraction(observations[high]['occupied_fraction'])-Fraction(observations[low]['occupied_fraction']))))
    means=[]
    for factor,fixed in sorted({(r['factor'],tuple(r['fixed'])) for r in contrasts}):
        values=[Fraction(r['late_occupied_fraction_difference']) for r in contrasts if r['factor']==factor and tuple(r['fixed'])==fixed]
        means.append(dict(factor=factor,fixed=list(fixed),sources=len(values),mean=str(sum(values,Fraction())/len(values))))
    return dict(scope='complete cohort, independent dynamics and registered windows; local growth and spatial occupation only',
                checks=checks,contrasts=contrasts,contrast_means=means,
                results_sha256=sha256((root/'results.json').read_bytes()).hexdigest(),
                script_sha256=sha256(Path(__file__).read_bytes()).hexdigest())


if __name__=='__main__':
    root=Path('data/v4-study-002')
    result=verify(root)
    with (root/'verification.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print('Verified40 runs and80 windows')
