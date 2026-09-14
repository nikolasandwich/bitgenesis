"""Summarize preregistered early processes from campaign-021 verified reports."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    mp=root/'docs/research/results/campaign-021-verification.json'
    op=root/'docs/research/results/campaign-021-observations.json'
    metrics=json.loads(mp.read_text(encoding='utf-8'));observations=json.loads(op.read_text(encoding='utf-8'))
    if observations['metrics_verification_sha256']!=hashlib.sha256(mp.read_bytes()).hexdigest():
        raise ValueError('Observation and metric reports have different sources')
    fields=('arm','birth_threshold','renewal','food_capacity','seed')
    index={tuple(r[k] for k in fields):r for r in metrics['runs']}
    records=observations['results'];grid={(a,t,c,b,s) for a in ('block',) for t in (40,160) for c in ("frequent-small","reference","rare-large") for b in (24,96) for s in range(1800,1810)}
    if len(records)!=120 or {tuple(r[k] for k in fields) for r in records}!=grid or len(metrics['runs'])!=120 or set(index)!=grid:
        raise ValueError('Incomplete process grid')
    rows=[]
    for record in records:
        key={k:record[k] for k in fields};m=index[tuple(key.values())]
        counts=record['counts'];f,d=(record['cohorts'][name] for name in ('founders','descendants'))
        attempts=counts['attempted_moves']
        if attempts!=sum(counts[k] for k in ('successful_moves','occupied_target_blocks','movement_payment_deaths')):
            raise ValueError('Movement outcomes do not partition attempts')
        if f['eaten']+d['eaten']!=m['food_eaten_by_100'] or f['ending_energy']+d['ending_energy']!=m['organism_energy_at_100'] or f['birth_paid']+d['birth_paid']!=0:
            raise ValueError('Cohort processes disagree with metrics')
        if (f['movement_paid']+d['movement_paid'] or counts['movement_payment_deaths']):
            raise ValueError('Zero-charge movement consumed energy or killed actors')
        rows.append(dict(**key,attempted_moves=attempts,blocked_moves=counts['occupied_target_blocks'],
            blocked_fraction=counts['occupied_target_blocks']/attempts if attempts else None,
            movement_payment_deaths=counts['movement_payment_deaths'],basal_deaths=counts['basal_deaths'],
            basal_paid=f['basal_paid']+d['basal_paid'],movement_paid=f['movement_paid']+d['movement_paid'],
            birth_paid=f['birth_paid']+d['birth_paid'],food_eaten=m['food_eaten_by_100'],births=m['births_at_100'],
            founder_to_descendant_energy=f['child_energy'],founder_ending_energy=f['ending_energy'],
            descendant_ending_energy=d['ending_energy'],population_at_100=m['population_at_100'],
            alive_at_10000=m['population']>0))
    groups=[]
    values=[k for k in rows[0] if k not in (*fields,'alive_at_10000')]
    from itertools import product
    for arm,threshold,renewal,capacity in product(('block',),(40,160),('frequent-small','reference','rare-large'),(24,96)):
        subset=[r for r in rows if (r['arm'],r['birth_threshold'],r['renewal'],r['food_capacity'])==(arm,threshold,renewal,capacity)]
        ranges={}
        for k in values:
            available=[r[k] for r in subset if r[k] is not None]
            ranges[k]=[min(available),max(available)] if available else None
        groups.append(dict(arm=arm,birth_threshold=threshold,renewal=renewal,food_capacity=capacity,ranges=ranges))
    report=dict(scope='Predeclared ticks 1–100 process summaries; ranges across ten worlds per treatment, not confidence intervals. No selection by survival and no independent-action inference.',
        rows=rows,groups=groups,metric_report_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),
        observation_report_sha256=hashlib.sha256(op.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    with (args.output/'worlds.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(groups,indent=2))


if __name__=='__main__':main()
