"""Verify campaign-019 early observations against metric-verified initial states."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
if __package__:
    from .verify_v0_movement_charge_observations import verify_early
else:
    from verify_v0_movement_charge_observations import verify_early


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-019'))
    parser.add_argument('--metrics-verification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();verification=json.loads(args.metrics_verification.read_text(encoding='utf-8'))
    records=verification['runs'];grid={(a,t,c,s) for a in ('block',) for t in (40,160) for c in (0,4) for s in range(1600,1610)}
    if len(records)!=40 or {(r['arm'],r['birth_threshold'],r['birth_cost'],r['seed']) for r in records}!=grid:
        raise ValueError('Expected full metric-verified grid')
    results=[];hashes={}
    for r in records:
        key={k:r[k] for k in ('arm','birth_threshold','birth_cost','seed')}
        prefix=f"{r['arm']}-threshold-{r['birth_threshold']}-birth-cost-{r['birth_cost']}-seed-{r['seed']}"
        ip=args.input/f'{prefix}-initial.json';mp=args.input/f'{prefix}.csv'
        for p in (ip,mp):
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            if digest!=verification['input_sha256'][p.name]:raise ValueError('Metric-verified input changed')
            hashes[p.name]=digest
        initial=json.loads(ip.read_text(encoding='utf-8'))
        if initial['config']['movement_cost'] != 0 or initial['config']['birth_cost'] != r['birth_cost']:
            raise ValueError('Joint-zero-charge configuration differs')
        with mp.open(encoding='utf-8',newline='') as stream:
            metrics=[{k:None if v=='' else float(v) if k=='mean_genome' else int(v) for k,v in row.items()} for row in csv.DictReader(stream)][:101]
        streams={}
        for kind in ('feeding','terminal','energy'):
            p=args.input/f'{prefix}-{kind}.jsonl';hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
            streams[kind]=[json.loads(line) for line in p.read_text(encoding='utf-8').splitlines()]
        results.append(dict(**key,**verify_early(initial,metrics,streams)))
    report=dict(results=results,input_sha256=hashes,verified_actor_ticks=4000,
        scope='Recorded early actor partitions, energy, genealogy labels and legal displacement. Unrecorded blocked destinations, birth positions and full local food histories are not reconstructed. No independent stochastic replay or unique causal claim.',
        metrics_verification_sha256=hashlib.sha256(args.metrics_verification.read_bytes()).hexdigest(),
        early_helper_sha256=hashlib.sha256(Path(__file__).with_name('verify_v0_movement_charge_observations.py').read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        cohort_helper_sha256=hashlib.sha256(Path(__file__).with_name('analyze_v0_cohort_energy.py').read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(worlds=len(results),actor_ticks=4000,energy_records=sum(r['counts']['energy'] for r in results))))


if __name__=='__main__':main()
