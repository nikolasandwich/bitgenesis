"""Independently verify campaign-020 stock replay records using only stdlib."""
import argparse
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

REGIMES={"frequent-small":(60,1),"reference":(15,4),"rare-large":(5,12)}
FIELDS=('arm','birth_threshold','renewal','seed')
GRID={('block',t,n,s) for t in (40,160) for n in REGIMES for s in range(1700,1710)}


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def tuples(value):return tuple(tuples(x) for x in value) if isinstance(value,list) else value


def verify_record(row,before,after,renewal):
    if row['schema']!=1 or row['tick']!=after['tick'] or after['tick']!=before['tick']+1:
        raise ValueError('Invalid record tick/schema')
    if row['before_metrics']!=before or row['after_metrics']!=after:
        raise ValueError('Historical metrics differ')
    food=row['food']
    if len(food)!=1024 or any(type(x) is not int or not 0<=x<=24 for x in food):
        raise ValueError('Invalid food vector')
    counts=Counter(food);hist=[counts[x] for x in range(25)]
    if row['histogram']!=hist or sum(food)!=before['food_energy']:
        raise ValueError('Food histogram or energy mismatch')
    if (type(row['active_start']) is not bool or row['active_start']!=(before['population']>0)
            or row['prior_population']!=before['population']):
        raise ValueError('Population partition mismatch')
    expected={name:Fraction(probability*sum(min(amount,24-x) for x in food),1000)
              for name,(probability,amount) in REGIMES.items()}
    if row['expected_added']!={k:str(v) for k,v in expected.items()} or row['expected_cap_loss']!=str(Fraction(6144,100)-expected[renewal]):
        raise ValueError('Conditional expectation mismatch')
    rng=random.Random();rng.setstate(tuples(row['rng_state']))
    probability,amount=REGIMES[renewal]
    arrivals=[x for x in food if rng.randrange(1000)<probability]
    admitted=sum(min(amount,24-x) for x in arrivals)
    uncapped=len(arrivals)*amount
    values=dict(successful_arrivals=len(arrivals),uncapped_arrival_energy=uncapped,
        admitted_energy=admitted,discarded_energy=uncapped-admitted,
        actual_supplied_increment=after['supplied_energy']-before['supplied_energy'])
    if values['actual_supplied_increment']!=admitted or any(type(row[k]) is not int or row[k]!=v for k,v in values.items()):
        raise ValueError('Sampled arrival accounting mismatch')
    return values


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/renewal-stocks-020'))
    parser.add_argument('--original',type=Path,default=Path('data/campaign-020'))
    parser.add_argument('--verification',type=Path,default=Path('docs/research/results/campaign-020-verification.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    metadata=json.loads((args.input/'metadata.json').read_text(encoding='utf-8'))
    verification=json.loads(args.verification.read_text(encoding='utf-8'))
    expected=dict(protocol='observation-020-renewal-stocks-1',status='complete',completed_runs=60,
        window=[1,100],planned_worlds=60,planned_replay_ticks=6000,git_dirty=False,
        engine_sha256='8f3ed33ad0ebe802c099e3e6f8ae61f9bcc526b98512f31f48ec40478fbfa7ff',
        protocol_sha256=digest(root/'experiments/v0/observation-020-renewal-stocks.md'),
        original_verification_sha256=digest(args.verification),original_metadata_sha256=digest(args.original/'metadata.json'))
    if any(metadata.get(k)!=v for k,v in expected.items()):raise ValueError('Incomplete or changed replay metadata')
    if verification['metadata_sha256']!=metadata['original_metadata_sha256']:raise ValueError('Original metadata differs')
    results=json.loads((args.input/'results.json').read_text(encoding='utf-8'))
    for records in (results,verification['runs']):
        if len(records)!=60 or {tuple(r[k] for k in FIELDS) for r in records}!=GRID:raise ValueError('Incomplete identity grid')
    checked=[];hashes={}
    for result in results:
        key={k:result[k] for k in FIELDS};prefix=f"block-threshold-{key['birth_threshold']}-renewal-{key['renewal']}-seed-{key['seed']}"
        if any(result[k]!=v for k,v in dict(replay_ticks=100,metric_rows_matched=101,observations=100,output_file=prefix+'-stocks.jsonl').items()):raise ValueError('Run coverage differs')
        ip=args.original/(prefix+'-initial.json');mp=args.original/(prefix+'.csv')
        for p in (ip,mp):
            value=digest(p)
            if value!=verification['input_sha256'][p.name] or value!=metadata['original_input_sha256'][p.name]:raise ValueError('Original inputs changed')
            hashes[p.name]=value
        initial=json.loads(ip.read_text(encoding='utf-8'))
        with mp.open(encoding='utf-8',newline='') as f:
            metrics=[{k:None if v=='' else float(v) if k=='mean_genome' else int(v) for k,v in r.items()} for r in csv.DictReader(f)][:101]
        p=args.input/result['output_file'];hashes[p.name]=digest(p)
        if hashes[p.name]!=result['output_sha256']:raise ValueError('Replay output changed')
        rows=[json.loads(line) for line in p.read_text(encoding='utf-8').splitlines()]
        if len(rows)!=100:raise ValueError('Incomplete observation window')
        if rows[0]['food']!=initial['food'] or hashlib.sha256(json.dumps(rows[0]['rng_state']).encode()).hexdigest()!=initial['rng_sha256']:
            raise ValueError('Initial map or RNG differs')
        partitions={name:dict(ticks=0,actual_added=0,uncapped=0,discarded=0,expected_added=Fraction(0),expected_cap_loss=Fraction(0)) for name in ('all','active','empty')}
        for tick,row in enumerate(rows,1):
            verify_record(row,metrics[tick-1],metrics[tick],key['renewal'])
            for name in ('all','active' if row['active_start'] else 'empty'):
                part=partitions[name];part['ticks']+=1
                for a,b in (('actual_added','admitted_energy'),('uncapped','uncapped_arrival_energy'),('discarded','discarded_energy')):part[a]+=row[b]
                part['expected_added']+=Fraction(row['expected_added'][key['renewal']]);part['expected_cap_loss']+=Fraction(row['expected_cap_loss'])
        for part in partitions.values():
            for k in ('expected_added','expected_cap_loss'):part[k]=str(part[k])
        checked.append(dict(**key,partitions=partitions))
    report=dict(worlds=60,records_checked=6000,renewal_draws_checked=6144000,metric_rows_checked=6060,rows=checked,
        input_sha256=hashes,metadata_sha256=digest(args.input/'metadata.json'),results_sha256=digest(args.input/'results.json'),
        original_verification_sha256=digest(args.verification),script_sha256=digest(Path(__file__)),
        scope='Independent reconstruction of recorded stock histograms, conditional expectations and renewal draws; stored metric boundaries match original prefixes. Does not reconstruct intervening actor paths or certify historical RNG states after initialization. Conditional means do not simulate alternative worlds; partitions are descriptive.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('worlds','records_checked','renewal_draws_checked','metric_rows_checked')}))


if __name__=='__main__':main()
