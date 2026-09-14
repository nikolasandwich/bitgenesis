"""Summarize verified retrospective renewal-stock partitions without simulation."""
import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def summarize(report):
    runs=report['rows'];fields=('arm','birth_threshold','renewal','seed')
    regimes=('frequent-small','reference','rare-large')
    grid={('block',t,n,s) for t in (40,160) for n in regimes for s in range(1700,1710)}
    if len(runs)!=60 or {tuple(r[k] for k in fields) for r in runs}!=grid:
        raise ValueError('Incomplete verified cohort')
    rows=[]
    for run in runs:
        parts=run['partitions']
        if set(parts)!={'all','active','empty'} or parts['all']['ticks']!=100:
            raise ValueError('Incomplete partitions')
        for k in ('ticks','actual_added','uncapped','discarded','expected_added','expected_cap_loss'):
            if Fraction(parts['all'][k])!=Fraction(parts['active'][k])+Fraction(parts['empty'][k]):
                raise ValueError('Partitions do not reconcile')
        for name,part in parts.items():
            if any(type(part[k]) is not int or part[k]<0 for k in ('ticks','actual_added','uncapped','discarded')):
                raise ValueError('Invalid integer accounting')
            expected=Fraction(part['expected_added']);loss=Fraction(part['expected_cap_loss'])
            nominal=Fraction(1536,25)*part['ticks']
            if expected<0 or loss<0 or expected+loss!=nominal or part['uncapped']!=part['actual_added']+part['discarded']:
                raise ValueError('Resource identity differs')
            if not part['ticks'] and any(Fraction(v) for v in part.values()):raise ValueError('Nonzero empty partition')
            rows.append(dict(**{k:run[k] for k in fields},partition=name,**part,
                expected_added_value=float(expected),expected_cap_loss_value=float(loss),
                actual_minus_expected=str(Fraction(part['actual_added'])-expected),
                actual_minus_expected_value=float(Fraction(part['actual_added'])-expected),
                realized_discard_fraction=part['discarded']/part['uncapped'] if part['uncapped'] else None,
                expected_loss_fraction=float(loss/nominal) if nominal else None))
    groups=[]
    for t in (40,160):
        for n in regimes:
            for partition in ('all','active','empty'):
                selected=[r for r in rows if (r['birth_threshold'],r['renewal'],r['partition'])==(t,n,partition)]
                ranges={}
                for k in ('ticks','actual_added','uncapped','discarded','expected_added_value','expected_cap_loss_value','actual_minus_expected_value','realized_discard_fraction','expected_loss_fraction'):
                    available=[r[k] for r in selected if r[k] is not None]
                    ranges[k]=[min(available),max(available)] if available else None
                groups.append(dict(birth_threshold=t,renewal=n,partition=partition,worlds=10,
                    positive_window_worlds=sum(r['ticks']>0 for r in selected),ranges=ranges))
    return dict(rows=rows,groups=groups)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('docs/research/results/renewal-stocks-020-verification.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=json.loads(args.input.read_text(encoding='utf-8'))
    result=summarize(report)
    result.update(input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Retrospective first-100-tick descriptive ranges over all ten worlds per cell. Sampled discard fraction uses actual uncapped sampled arrivals; expected cap-loss fraction uses nominal expectation. Zero-length partitions have unavailable ratios, not measured zero rates. Residuals are descriptive, not significance tests or causal mediators.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    with (args.output/'worlds.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(result['rows'][0]));writer.writeheader();writer.writerows(result['rows'])
    print(json.dumps(dict(world_partition_rows=len(result['rows']),groups=len(result['groups']))))


if __name__=='__main__':main()
