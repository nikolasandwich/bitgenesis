"""Post hoc campaign-020 supply partition; no simulation or causal mediation."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def partition(rows, extinction):
    horizon=len(rows)-1
    if horizon<1 or [r['tick'] for r in rows]!=list(range(horizon+1)):
        raise ValueError('Incomplete tick grid')
    observed=next((r['tick'] for r in rows if r['population']==0),None)
    if observed!=extinction or extinction==0:
        raise ValueError('Extinction mismatch')
    end=horizon if extinction is None else extinction
    first,boundary,last=rows[0],rows[end],rows[-1]
    for previous,current in zip(rows,rows[1:]):
        supply=current['supplied_energy']-previous['supplied_energy']
        uptake=supply+previous['food_energy']-current['food_energy']
        if supply<0 or not 0<=uptake<=8*previous['population']:
            raise ValueError('Invalid resource transition')
        if previous['population']==0 and (current['population'] or uptake or
                current['organism_energy'] or current['dissipated_energy']!=previous['dissipated_energy']):
            raise ValueError('Empty-world resources consumed or population returned')
    active=boundary['supplied_energy']-first['supplied_energy']
    post=last['supplied_energy']-boundary['supplied_energy']
    uptake=active+first['food_energy']-boundary['food_energy']
    total=last['supplied_energy']-first['supplied_energy']
    if active+post!=total:
        raise ValueError('Supply partition failed')
    return dict(extinction_tick=extinction,right_censored=extinction is None,
        active_start_ticks=end,empty_start_ticks=horizon-end,
        added_during_active_start_ticks=active,added_after_extinction=post,
        total_added=total,cumulative_uptake=uptake,
        food_at_window_end=boundary['food_energy'],final_food=last['food_energy'],
        post_extinction_fraction=post/total if total else None)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-020'))
    parser.add_argument('--verification',type=Path,default=Path('docs/research/results/campaign-020-verification.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=json.loads(args.verification.read_text(encoding='utf-8'))
    runs=report['runs']; fields=('arm','birth_threshold','renewal','seed')
    grid={('block',t,n,s) for t in (40,160) for n in ('frequent-small','reference','rare-large') for s in range(1700,1710)}
    if len(runs)!=60 or {tuple(r[k] for k in fields) for r in runs}!=grid:
        raise ValueError('Incomplete cohort')
    results=[];hashes={}
    for run in runs:
        prefix=f"block-threshold-{run['birth_threshold']}-renewal-{run['renewal']}-seed-{run['seed']}"
        p=args.input/(prefix+'.csv');digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if digest!=report['input_sha256'][p.name]:raise ValueError('Verified metrics changed')
        hashes[p.name]=digest
        with p.open(encoding='utf-8',newline='') as f:
            rows=[{k:int(r[k]) for k in ('tick','population','food_energy','supplied_energy','organism_energy','dissipated_energy')} for r in csv.DictReader(f)]
        if len(rows)!=10001:raise ValueError('Truncated horizon')
        result=partition(rows,run['extinction_tick'])
        if result['total_added']!=run['resources_added_by_10000'] or result['cumulative_uptake']!=run['cumulative_uptake_by_10000']:
            raise ValueError('Registered checkpoint differs')
        results.append(dict(**{k:run[k] for k in fields},**result))
    output=dict(analysis='campaign-020-supply-windows-posthoc-1',rows=results,
        input_sha256=hashes,metric_report_sha256=hashlib.sha256(args.verification.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='All sixty worlds, retrospective partition. Active-start ticks include the extinction tick: regrowth precedes lethal basal payments. Supply is global and need not be locally accessible. Unequal window lengths and outcome conditioning prevent causal or per-rate treatment inference. Survivors have zero observed post-extinction ticks, not predicted immortality. No new simulations.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(worlds=len(results),extinct=sum(r['extinction_tick'] is not None for r in results))))


if __name__=='__main__':main()
