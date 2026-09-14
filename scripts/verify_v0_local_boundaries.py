"""Independent structural/accounting audit of campaign-019 replay boundary maps."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random


def verify_boundary(row, metric, config):
    if type(row['tick']) is not int or row['tick']!=metric['tick'] or row['metrics']!=metric:
        raise ValueError('Boundary metric differs from original')
    food=row['food'];living=row['living'];occupied=row['occupied'];size=config['width']*config['height']
    if len(food)!=size or any(type(x) is not int or not 0<=x<=config['food_capacity'] for x in food) or sum(food)!=metric['food_energy']:
        raise ValueError('Boundary food differs')
    ids=set();positions=set()
    for actor in living:
        for field in ('id','founder_id','generation','birth_tick','genome','position','energy','offspring'):
            if type(actor[field]) is not int:raise ValueError('Invalid individual integer')
        if (actor['id'] in ids or actor['position'] in positions or not 0<=actor['id']<config['initial_population']+metric['births'] or
            not 0<=actor['position']<size or actor['energy']<=0 or actor['genome']!=250 or actor['death_tick'] is not None or
            not 0<=actor['birth_tick']<=row['tick'] or actor['offspring']<0 or not 0<=actor['founder_id']<config['initial_population']):
            raise ValueError('Invalid living individual')
        if actor['id']<config['initial_population']:
            if (actor['parent_id'],actor['founder_id'],actor['generation'],actor['birth_tick'])!=(None,actor['id'],0,0):
                raise ValueError('Invalid founder labels')
        elif type(actor['parent_id']) is not int or not 0<=actor['parent_id']<actor['id'] or actor['generation']<=0 or actor['birth_tick']<=0:
            raise ValueError('Invalid descendant labels')
        ids.add(actor['id']);positions.add(actor['position'])
    if occupied!=[[a['position'],a['id']] for a in sorted(living,key=lambda a:a['position'])]:
        raise ValueError('Boundary occupancy differs')
    if (len(living)!=metric['population'] or sum(a['energy'] for a in living)!=metric['organism_energy'] or
        len({a['founder_id'] for a in living})!=metric['founder_lineages'] or
        max((a['generation'] for a in living),default=None)!=metric['max_generation']):
        raise ValueError('Boundary population accounting differs')
    if metric['food_energy']+metric['organism_energy']+metric['dissipated_energy']!=metric['supplied_energy']:
        raise ValueError('Boundary energy balance differs')
    state=row['rng_state']
    if not isinstance(state,list) or len(state)!=3 or not isinstance(state[1],list):raise ValueError('Invalid RNG state shape')
    random.Random().setstate((state[0],tuple(state[1]),state[2]))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/local-resource-replay-019'))
    parser.add_argument('--original',type=Path,default=Path('data/campaign-019'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    vp=root/'docs/research/results/campaign-019-verification.json'
    verification=json.loads(vp.read_text(encoding='utf-8'));meta=json.loads((args.input/'metadata.json').read_text(encoding='utf-8'))
    records=json.loads((args.input/'results.json').read_text(encoding='utf-8'))
    fields=('arm','birth_threshold','birth_cost','seed');original={tuple(r[k] for k in fields):r for r in verification['runs']}
    grid={('block',t,c,s) for t in (40,160) for c in (0,4) for s in range(1600,1610)}
    if meta['status']!='complete' or meta['completed_runs']!=40 or len(records)!=40 or {tuple(r[k] for k in fields) for r in records}!=grid or set(original)!=grid:
        raise ValueError('Expected complete registered replay')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if meta['git_dirty'] is not False or meta['verification_sha256']!=sha(vp) or meta['protocol_sha256']!=sha(root/'experiments/v0/observation-019-local-resources.md'):
        raise ValueError('Replay provenance differs')
    results=[];hashes={}
    for record in records:
        source=original[tuple(record[k] for k in fields)]
        endpoint=source['extinction_tick'] if source['extinction_tick'] is not None else 10000
        if record['endpoint']!=endpoint or record['right_censored']!=source['right_censored'] or record['matched_metric_rows']!=endpoint+1 or record['replayed_ticks']!=endpoint:
            raise ValueError('Replay endpoint differs')
        prefix=f"block-threshold-{record['birth_threshold']}-birth-cost-{record['birth_cost']}-seed-{record['seed']}"
        ip=args.original/(prefix+'-initial.json');mp=args.original/(prefix+'.csv');bp=args.input/(prefix+'-boundaries.jsonl')
        for p in (ip,mp):
            if sha(p)!=verification['input_sha256'][p.name] or sha(p)!=meta['input_sha256'][p.name]:raise ValueError('Original source changed')
            hashes[p.name]=sha(p)
        if sha(bp)!=record['output_sha256']['boundaries']:raise ValueError('Boundary output changed')
        hashes[bp.name]=sha(bp)
        initial=json.loads(ip.read_text(encoding='utf-8'))
        with mp.open(encoding='utf-8',newline='') as stream:
            metrics=[{k:None if v=='' else float(v) if k=='mean_genome' else int(v) for k,v in r.items()} for r in csv.DictReader(stream)]
        rows=[json.loads(line) for line in bp.read_text(encoding='utf-8').splitlines()]
        if len(rows)!=21 or record['counts']['boundaries']!=21 or [r['tick'] for r in rows]!=list(range(endpoint-20,endpoint+1)):
            raise ValueError('Boundary window differs')
        for row in rows:verify_boundary(row,metrics[row['tick']],initial['config'])
        results.append(dict(**{k:record[k] for k in fields},endpoint=endpoint,boundaries_checked=21))
    result=dict(results=results,boundaries_checked=840,input_sha256=hashes,
        metadata_sha256=sha(args.input/'metadata.json'),results_sha256=sha(args.input/'results.json'),script_sha256=sha(Path(__file__)),
        scope='Boundary structure and accounting against original metric rows; RNG state shape validated, not trajectory equality. No per-action spatial reconstruction or historical actor-path proof.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(worlds=40,boundaries_checked=840)))


if __name__=='__main__':main()
