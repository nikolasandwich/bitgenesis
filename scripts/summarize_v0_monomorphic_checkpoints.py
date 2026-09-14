"""Summarize all registered mutation-assay checkpoints after both verification gates."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-022'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    mp=root/'docs/research/results/campaign-022-verification.json'
    hp=root/'docs/research/results/campaign-022-histories.json'
    metrics=json.loads(mp.read_text(encoding='utf-8'));histories=json.loads(hp.read_text(encoding='utf-8'))
    if histories['metric_verification_sha256']!=hashlib.sha256(mp.read_bytes()).hexdigest():raise ValueError('Gate linkage differs')
    grid={(s,m) for s in range(1900,1920) for m in (0,100)}
    for rows in (metrics['runs'],histories['results']):
        if len(rows)!=40 or {(r['seed'],r['mutation_probability']) for r in rows}!=grid:raise ValueError('Incomplete gate')
    observations=[];hashes={}
    for run in metrics['runs']:
        relative=f"mutation-{run['mutation_probability']}-seed-{run['seed']}/result.json"
        p=args.input/relative;digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if digest!=histories['input_sha256'][relative] or digest!=metrics['input_sha256'][relative]:raise ValueError('Verified checkpoint data changed')
        hashes[relative]=digest;result=json.loads(p.read_text(encoding='utf-8'))
        if {k:v for k,v in result.items() if k!='observations'}!=run:raise ValueError('Terminal summary changed')
        for tick,obs in result['observations'].items():
            observations.append(dict(seed=run['seed'],mutation_probability=run['mutation_probability'],**obs))
    checkpoints=(0,100,500,1000,5000,10000)
    if len(observations)!=240 or {(r['seed'],r['mutation_probability'],r['tick']) for r in observations}!={(s,m,t) for s,m in grid for t in checkpoints}:raise ValueError('Checkpoint grid differs')
    groups=[]
    fields=('population','births','deaths','genome_variants','ever_genome_values','changed_births','founder_lineages','food_energy','organism_energy','supplied_energy','dissipated_energy')
    for mutation in (0,100):
        for tick in checkpoints:
            rows=[r for r in observations if r['mutation_probability']==mutation and r['tick']==tick]
            groups.append(dict(mutation_probability=mutation,tick=tick,worlds=20,alive=sum(r['population']>0 for r in rows),
                ranges={k:[min(r[k] for r in rows),max(r[k] for r in rows)] for k in fields},
                null_mean_worlds=sum(r['mean_genome'] is None for r in rows),
                null_generation_worlds=sum(r['max_generation'] is None for r in rows)))
    report=dict(scope='All 240 predeclared world/checkpoint observations, including extinct worlds. Ranges are descriptive across 20 seeds, not confidence intervals; null means/generations remain in individual rows.',observations=observations,groups=groups,input_sha256=hashes,metric_report_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),history_report_sha256=hashlib.sha256(hp.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    compact=[{k:v for k,v in r.items() if not k.endswith('_histogram')} for r in observations]
    with (args.output/'checkpoints.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(compact[0]));writer.writeheader();writer.writerows(compact)
    print(json.dumps(groups,indent=2))


if __name__=='__main__':main()
