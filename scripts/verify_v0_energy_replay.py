"""Reconstruct individual energy from stored replay ledgers without executing V0."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/energy-replay-017'))
    parser.add_argument('--reference',type=Path,default=Path('data/campaign-017'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); root=Path(__file__).resolve().parents[1]
    meta=json.loads((args.input/'metadata.json').read_text(encoding='utf-8'))
    records=json.loads((args.input/'results.json').read_text(encoding='utf-8'))
    prior=json.loads((root/'docs/research/results/action-replay-017.json').read_text(encoding='utf-8'))
    verified=json.loads((root/'docs/research/results/campaign-017-verification.json').read_text(encoding='utf-8'))
    old={(r['arm'],r['birth_threshold'],r['seed']):r for r in prior['results']}
    grid={(a,t,s) for a in ('dispersed','block') for t in (40,160) for s in range(1400,1410)}
    if meta['status']!='complete' or meta['energy_schema']!=1 or len(records)!=40 or {(r['arm'],r['birth_threshold'],r['seed']) for r in records}!=grid:
        raise ValueError('Incomplete energy replay')
    results=[]; hashes={}
    for record in records:
        key={k:record[k] for k in ('arm','birth_threshold','seed')}
        previous=old[record['arm'],record['birth_threshold'],record['seed']]
        prefix=f"{record['arm']}-threshold-{record['birth_threshold']}-seed-{record['seed']}"
        streams={}
        for kind in ('feeding','terminal','energy'):
            path=args.input/f'{prefix}-{kind}.jsonl'
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if digest!=record[kind+'_sha256'] or (kind!='energy' and digest!=previous[kind+'_sha256']):
                raise ValueError('Stored observation hash differs')
            hashes[path.name]=digest
            grouped=defaultdict(list)
            for line in path.read_text(encoding='utf-8').splitlines():
                row=json.loads(line)
                if type(row['tick']) is not int or not 1<=row['tick']<=100:
                    raise ValueError('Invalid ledger tick')
                grouped[row['tick']].append(row)
            streams[kind]=grouped
        ip=args.reference/f'{prefix}-initial.json'; mp=args.reference/f'{prefix}.csv'
        for path in (ip,mp):
            if hashlib.sha256(path.read_bytes()).hexdigest()!=verified['input_sha256'][path.name]:
                raise ValueError('Original record differs')
        initial=json.loads(ip.read_text(encoding='utf-8')); config=initial['config']
        energies={r['id']:r['energy'] for r in initial['founders']}; next_id=len(energies)
        with mp.open(encoding='utf-8',newline='') as stream:
            metrics=list(csv.DictReader(stream))[:101]
        totals=dict(basal_paid=0,movement_paid=0,birth_paid=0,eaten=0,child_energy=0)
        count=0
        for tick in range(1,101):
            ledgers=streams['energy'][tick]
            feeds={r['id']:r for r in streams['feeding'][tick]}
            deaths={r['id']:r for r in streams['terminal'][tick]}
            if len(ledgers)!=len(energies) or {r['id'] for r in ledgers}!=set(energies) or set(feeds)&set(deaths) or set(feeds)|set(deaths)!=set(energies):
                raise ValueError('Energy actor partition differs')
            ending={}; children={}; costs=0
            for row in ledgers:
                identity=row['id']; start=energies[identity]
                for field in ('energy_before_action','energy_after_action',*totals):
                    if type(row[field]) is not int or row[field]<0:
                        raise ValueError('Invalid integer ledger field')
                if row['observation_schema']!=1 or type(row['died']) is not bool or row['energy_before_action']!=start:
                    raise ValueError('Starting energy or schema differs')
                feed=feeds.get(identity); death=deaths.get(identity)
                attempted=feed['movement_attempted'] if feed else death['movement_attempted']
                basal=min(start,config['basal_cost'])
                movement=min(start-basal,config['movement_cost']) if attempted else 0
                eaten=feed['eaten'] if feed else 0
                child_id=feed['child_id'] if feed else None
                birth=config['birth_cost'] if child_id is not None else 0
                transfer=(start-basal-movement+eaten-birth)//2 if child_id is not None else 0
                final=start-basal-movement+eaten-birth-transfer
                expected=dict(basal_paid=basal,movement_paid=movement,birth_paid=birth,eaten=eaten,child_energy=transfer)
                if any(row[k]!=v for k,v in expected.items()) or row['child_id']!=child_id or row['energy_after_action']!=final or row['died']!=(identity in deaths):
                    raise ValueError('Individual energy transition differs')
                if feed and feed['energy_before_feeding']!=start-basal-movement:
                    raise ValueError('Pre-feeding energy differs')
                if row['died']:
                    if final!=0:raise ValueError('Death has residual energy')
                else:
                    if final<=0:raise ValueError('Survivor has no energy')
                    ending[identity]=final
                if child_id is not None:
                    if child_id in children:raise ValueError('Duplicate child')
                    children[child_id]=transfer
                for k,v in expected.items():totals[k]+=v
                costs+=basal+movement+birth
            if sorted(children)!=list(range(next_id,next_id+len(children))):
                raise ValueError('Child sequence differs')
            next_id+=len(children); energies=ending|children
            now,before=metrics[tick],metrics[tick-1]
            if sum(energies.values())!=int(now['organism_energy']) or len(energies)!=int(now['population']) or costs!=int(now['dissipated_energy'])-int(before['dissipated_energy']):
                raise ValueError('Global energy differs')
            count+=len(ledgers)
        if count!=record['energy_records']:raise ValueError('Ledger count differs')
        results.append(dict(**key,energy_records=count,totals=totals))
    report=dict(source_commit=meta['git_commit'],results=results,input_sha256=hashes,
                reconstructed_ticks=4000,energy_records=sum(r['energy_records'] for r in results),
                scope='Stored energy reconstructed from initial states and verified feeding/birth/death records under pinned payment/split rules. No simulation rerun or causal claim.',
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('source_commit','reconstructed_ticks','energy_records')}))


if __name__=='__main__':main()
