"""Describe all registered campaign-019 terminal windows from verified observations."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/local-resource-replay-019'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    ap=root/'docs/research/results/local-actions-019.json';bp=root/'docs/research/results/local-boundaries-019.json'
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    actions=json.loads(ap.read_text(encoding='utf-8'));bounds=json.loads(bp.read_text(encoding='utf-8'))
    if actions['boundary_verification_sha256']!=sha(bp):raise ValueError('Verification reports differ')
    fields=('arm','birth_threshold','birth_cost','seed')
    grid={('block',t,c,s) for t in (40,160) for c in (0,4) for s in range(1600,1610)}
    if len(actions['results'])!=40 or {tuple(r[k] for k in fields) for r in actions['results']}!=grid:raise ValueError('Incomplete grid')
    results=[];hashes={}
    for r in actions['results']:
        prefix=f"block-threshold-{r['birth_threshold']}-birth-cost-{r['birth_cost']}-seed-{r['seed']}"
        streams={}
        for kind in ('local','boundaries'):
            p=args.input/f'{prefix}-{kind}.jsonl';hashes[p.name]=sha(p)
            if hashes[p.name]!=actions['input_sha256'][p.name]:raise ValueError('Verified input changed')
            streams[kind]=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
        local=streams['local'];end=streams['boundaries'][-1]
        current=sum(row['sites'][0]['food']>0 for row in local)
        nearby=sum(any(s['occupant_id'] is None and s['food']>0 for s in row['sites'][1:]) for row in local)
        if len(local)!=r['actions'] or current!=r['current_site_food'] or nearby!=r['free_neighbor_food']:raise ValueError('Action totals differ')
        final_rows=[row for row in local if row['tick']==r['endpoint']]
        extinction_local=None if r['right_censored'] else final_rows
        results.append(dict(**r,current_site_food_fraction=current/len(local) if local else None,
            free_neighbor_food_fraction=nearby/len(local) if local else None,
            final_population=end['metrics']['population'],final_organism_energy=end['metrics']['organism_energy'],
            final_food_energy=end['metrics']['food_energy'],extinction_action_locations=extinction_local))
    groups=[]
    for threshold in (40,160):
        for cost in (0,4):
            for censored in (False,True):
                selected=[r for r in results if (r['birth_threshold'],r['birth_cost'],r['right_censored'])==(threshold,cost,censored)]
                ranges={}
                for field in ('actions','basal_deaths','current_site_food_fraction','free_neighbor_food_fraction','final_population','final_organism_energy','final_food_energy'):
                    values=[r[field] for r in selected if r[field] is not None]
                    ranges[field]=[min(values),max(values)] if values else None
                groups.append(dict(birth_threshold=threshold,birth_cost=cost,right_censored=censored,worlds=len(selected),ranges=ranges))
    report=dict(results=results,groups=groups,input_sha256=hashes,
        action_verification_sha256=sha(ap),boundary_verification_sha256=sha(bp),script_sha256=sha(Path(__file__)),
        scope='Descriptive final-twenty-action-tick windows, aligned to extinction or fixed horizon. Percentages are per-world action fractions, not independent action replicates; ranges are not confidence intervals. Outcome-conditioned groups have different ages. Extinction locations are null for survivors. No causal or permanent-survival claim.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(groups,indent=2))


if __name__=='__main__':main()
