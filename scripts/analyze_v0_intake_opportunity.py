"""Post hoc one-action policy-distribution intake, not deterministic RNG replay."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def opportunity(local, feeding_rate=8):
    """Pinned campaign-019: basal 1, move cost 0, trait 250, four unique neighbors."""
    sites=local['sites']
    if len(sites)!=5 or len({s['position'] for s in sites})!=5 or local['energy_before_action']<1:
        raise ValueError('Expected five distinct sites and positive actor energy')
    if any(type(s['food']) is not int or not 0<=s['food']<=24 for s in sites):raise ValueError('Invalid food')
    if local['energy_before_action']==1:return dict(expected_intake=Fraction(0),positive_intake_probability=Fraction(0))
    here=min(feeding_rate,sites[0]['food'])
    destinations=[here if s['occupant_id'] is not None else min(feeding_rate,s['food']) for s in sites[1:]]
    return dict(expected_intake=Fraction(3,4)*here+sum((Fraction(1,16)*x for x in destinations),Fraction()),
        positive_intake_probability=Fraction(3,4)*bool(here)+sum((Fraction(1,16)*bool(x) for x in destinations),Fraction()))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/local-resource-replay-019'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    vp=root/'docs/research/results/local-actions-019.json';verified=json.loads(vp.read_text(encoding='utf-8'))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    results=[];hashes={}
    for r in verified['results']:
        prefix=f"block-threshold-{r['birth_threshold']}-birth-cost-{r['birth_cost']}-seed-{r['seed']}"
        streams={}
        for kind in ('local','energy'):
            p=args.input/f'{prefix}-{kind}.jsonl';hashes[p.name]=sha(p)
            if hashes[p.name]!=verified['input_sha256'][p.name]:raise ValueError('Verified input changed')
            streams[kind]=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
        expected=Fraction();positive=Fraction();eligible_neighbor=0;eligible_empty_here=0
        for local in streams['local']:
            value=opportunity(local);expected+=value['expected_intake'];positive+=value['positive_intake_probability']
            if local['energy_before_action']>1 and any(s['occupant_id'] is None and s['food']>0 for s in local['sites'][1:]):
                eligible_neighbor+=1;eligible_empty_here+=local['sites'][0]['food']==0
        encode=lambda f:dict(numerator=f.numerator,denominator=f.denominator,value=float(f))
        results.append(dict(**{k:r[k] for k in ('arm','birth_threshold','birth_cost','seed','endpoint','right_censored')},actions=len(streams['local']),
            summed_policy_expected_intake=encode(expected),summed_policy_positive_intake_probability=encode(positive),
            actual_intake=sum(e['eaten'] for e in streams['energy']),actual_positive_intake_actions=sum(e['eaten']>0 for e in streams['energy']),
            basal_survivable_with_free_neighbor_food=eligible_neighbor,basal_survivable_empty_here_with_free_neighbor_food=eligible_empty_here))
    report=dict(results=results,input_sha256=hashes,source_verification_sha256=sha(vp),script_sha256=sha(Path(__file__)),
        scope='Post hoc policy-distribution expectation under fresh uniform movement draws conditional on each recorded pre-action local state. This is not the deterministic outcome conditional on saved PRNG state, an alternative trajectory, or an unbiased survival-effect estimate. Endpoint selection invalidates naive residual significance claims.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(worlds=len(results),actions=sum(r['actions'] for r in results))))


if __name__=='__main__':main()
