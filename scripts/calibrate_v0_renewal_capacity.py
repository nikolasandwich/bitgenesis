"""Exact one-site renewal law for campaign 020, conditional on identical stock."""
import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path

REGIMES={"frequent-small":(60,1),"reference":(15,4),"rare-large":(5,12)}


def law(stock, probability, amount, capacity=24):
    if any(type(v) is not int for v in (stock,probability,amount,capacity)) or not (0<=stock<=capacity and capacity>0 and 0<=probability<=1000 and amount>0):
        raise ValueError('Invalid discrete renewal parameters')
    p=Fraction(probability,1000);added=min(amount,capacity-stock)
    mean=p*added
    return dict(mean=mean,variance=p*(1-p)*added*added,
        lost_nominal_mean=p*(amount-added),positive_probability=p if added else Fraction(0))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();rows=[]
    for stock in range(25):
        for name,(probability,amount) in REGIMES.items():
            values=law(stock,probability,amount)
            row=dict(stock=stock,remaining_capacity=24-stock,renewal=name,
                     probability_per_thousand=probability,packet=amount)
            for key,value in values.items():
                row[key+'_exact']=str(value);row[key]=float(value)
            rows.append(row)
        means=[law(stock,*parameters)['mean'] for parameters in REGIMES.values()]
        if not means[0]>=means[1]>=means[2]:raise ValueError('Conditional mean ordering failed')
    root=Path(__file__).resolve().parents[1]
    engine=root/'src/bitgenesis/v0/engine.py'
    digest=hashlib.sha256(engine.read_text(encoding='utf-8').encode()).hexdigest()
    if digest!='8f3ed33ad0ebe802c099e3e6f8ae61f9bcc526b98512f31f48ec40478fbfa7ff':
        raise ValueError('Review calibration against changed engine rules')
    result=dict(analysis='campaign-020-conditional-renewal-law-1',rows=rows,
        engine_normalized_sha256=digest,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Exact distribution over one randrange(1000) draw for each of 25 identical pre-renewal stocks and three treatments. No simulation, historical conditional-stock distribution, treatment survival effect or variance-only interpretation. Map expectations sum these one-site means; evolving worlds need not share maps.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    with (args.output/'stocks.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(dict(stock_treatment_cells=len(rows),simulated_worlds=0)))


if __name__=='__main__':main()
