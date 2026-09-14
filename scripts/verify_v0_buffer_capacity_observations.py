"""Verify campaign-021 early observations against metric-verified initial states."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
if __package__:
    from .verify_v0_movement_charge_observations import verify_early
    from .summarize_v0_buffer_capacity import verify_initial
else:
    from verify_v0_movement_charge_observations import verify_early
    from summarize_v0_buffer_capacity import verify_initial


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-021'))
    parser.add_argument('--metrics-verification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();verification=json.loads(args.metrics_verification.read_text(encoding='utf-8'))
    records=verification['runs'];grid={(a,t,c,b,s) for a in ('block',) for t in (40,160) for c in ("frequent-small","reference","rare-large") for b in (24,96) for s in range(1800,1810)}
    if len(records)!=120 or {(r['arm'],r['birth_threshold'],r['renewal'],r['food_capacity'],r['seed']) for r in records}!=grid:
        raise ValueError('Expected full metric-verified grid')
    metadata_path=args.input/'metadata.json'
    if hashlib.sha256(metadata_path.read_bytes()).hexdigest()!=verification['metadata_sha256']:
        raise ValueError('Metric-verified metadata changed')
    if verification.get('metric_rows_checked')!=1200120 or verification.get('initial_states_checked')!=120:
        raise ValueError('Incomplete metric verification')
    results=[];hashes={}
    for r in records:
        key={k:r[k] for k in ('arm','birth_threshold','renewal','food_capacity','seed')}
        prefix=f"{r['arm']}-threshold-{r['birth_threshold']}-renewal-{r['renewal']}-capacity-{r['food_capacity']}-seed-{r['seed']}"
        ip=args.input/f'{prefix}-initial.json';mp=args.input/f'{prefix}.csv'
        for p in (ip,mp):
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            if digest!=verification['input_sha256'][p.name]:raise ValueError('Metric-verified input changed')
            hashes[p.name]=digest
        initial=json.loads(ip.read_text(encoding='utf-8'))
        verify_initial(initial,r['arm'],r['birth_threshold'],r['renewal'],r['food_capacity'],r['seed'])
        with mp.open(encoding='utf-8',newline='') as stream:
            metrics=[{k:None if v=='' else float(v) if k=='mean_genome' else int(v) for k,v in row.items()} for row in csv.DictReader(stream)][:101]
        streams={}
        for kind in ('feeding','terminal','energy'):
            p=args.input/f'{prefix}-{kind}.jsonl';hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
            streams[kind]=[json.loads(line) for line in p.read_text(encoding='utf-8').splitlines()]
        results.append(dict(**key,**verify_early(initial,metrics,streams)))
    report=dict(results=results,input_sha256=hashes,verified_world_ticks=12000,
        scope='Recorded early actor partitions, energy, genealogy labels and legal displacement. Unrecorded blocked destinations, birth positions and full local food histories are not reconstructed. No independent stochastic replay or unique causal claim.',
        metrics_verification_sha256=hashlib.sha256(args.metrics_verification.read_bytes()).hexdigest(),
        initialization_helper_sha256=hashlib.sha256(Path(__file__).with_name('summarize_v0_buffer_capacity.py').read_bytes()).hexdigest(),
        geometry_helper_sha256=hashlib.sha256(Path(__file__).with_name('summarize_v0_food_geometry.py').read_bytes()).hexdigest(),
        early_helper_sha256=hashlib.sha256(Path(__file__).with_name('verify_v0_movement_charge_observations.py').read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        cohort_helper_sha256=hashlib.sha256(Path(__file__).with_name('analyze_v0_cohort_energy.py').read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(worlds=len(results),world_ticks=12000,energy_records=sum(r['counts']['energy'] for r in results))))


if __name__=='__main__':main()
