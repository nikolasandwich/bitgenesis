"""Separate cohort energy flows from internal descendant-to-descendant transfers."""
import argparse
import hashlib
import json
from pathlib import Path


FIELDS=('eaten','basal_paid','movement_paid','birth_paid','child_energy')


def budgets(rows, initial):
    founders=set(initial)
    stock=dict(initial)
    groups={name:{k:0 for k in FIELDS} for name in ('founders','descendants')}
    for row in rows:
        identity=row['id']; name='founders' if identity in founders else 'descendants'
        if identity not in stock or stock[identity]!=row['energy_before_action']:
            raise ValueError('Individual starting energy differs')
        stock[identity]=row['energy_after_action']
        for field in FIELDS:groups[name][field]+=row[field]
        if row['child_id'] is not None:
            if row['child_id'] in stock:raise ValueError('Duplicate newborn')
            stock[row['child_id']]=row['child_energy']
    for name,g in groups.items():
        g['initial_energy']=sum(initial.values()) if name=='founders' else 0
        g['received_from_founders']=0 if name=='founders' else groups['founders']['child_energy']
        g['ending_energy']=sum(value for i,value in stock.items() if (i in founders)==(name=='founders'))
        g['total_paid']=sum(g[k] for k in ('basal_paid','movement_paid','birth_paid'))
        outgoing=g['child_energy'] if name=='founders' else 0
        if g['initial_energy']+g['received_from_founders']+g['eaten']!=g['ending_energy']+g['total_paid']+outgoing:
            raise ValueError('Cohort energy does not balance')
    return groups


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/energy-replay-017'))
    parser.add_argument('--reference',type=Path,default=Path('data/campaign-017'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); root=Path(__file__).resolve().parents[1]
    vp=root/'docs/research/results/energy-replay-017.json'
    verified=json.loads(vp.read_text(encoding='utf-8'))
    originals=json.loads((root/'docs/research/results/campaign-017-verification.json').read_text(encoding='utf-8'))
    intake=json.loads((root/'docs/research/results/individual-intake-017.json').read_text(encoding='utf-8'))
    old={(r['arm'],r['birth_threshold'],r['seed']):r for r in intake['results']}
    records=verified['results']
    grid={(a,t,s) for a in ('dispersed','block') for t in (40,160) for s in range(1400,1410)}
    if len(records)!=40 or {(r['arm'],r['birth_threshold'],r['seed']) for r in records}!=grid:
        raise ValueError('Incomplete energy grid')
    results=[]; hashes={}
    for record in records:
        key={k:record[k] for k in ('arm','birth_threshold','seed')}
        prefix=f"{record['arm']}-threshold-{record['birth_threshold']}-seed-{record['seed']}"
        path=args.input/f'{prefix}-energy.jsonl'; ip=args.reference/f'{prefix}-initial.json'
        for p,digest in ((path,verified['input_sha256'][path.name]),(ip,originals['input_sha256'][ip.name])):
            if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('Input hash differs')
            hashes[p.name]=digest
        initial=json.loads(ip.read_text(encoding='utf-8'))
        rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        groups=budgets(rows,{o['id']:o['energy'] for o in initial['founders']})
        for field in FIELDS:
            if sum(g[field] for g in groups.values())!=record['totals'][field]:
                raise ValueError('Whole-world flow differs')
        prior=old[record['arm'],record['birth_threshold'],record['seed']]
        for name,g in groups.items():
            if g['eaten']!=prior[name]['food_eaten']:raise ValueError('Prior cohort intake differs')
        results.append(dict(**key,**groups))
    grouped=[]
    for arm in ('dispersed','block'):
        for threshold in (40,160):
            subset=[r for r in results if r['arm']==arm and r['birth_threshold']==threshold]
            grouped.append(dict(arm=arm,birth_threshold=threshold,ranges={name:{
                k:[min(r[name][k] for r in subset),max(r[name][k] for r in subset)]
                for k in (*FIELDS,'total_paid','ending_energy','received_from_founders')}
                for name in ('founders','descendants')}))
    report=dict(scope='Retrospective ticks 1–100. Birth energy is a transfer, not supply; descendant-to-descendant transfers cancel in the descendant cohort balance. No causal counterfactual.',
                results=results,groups=grouped,input_sha256=hashes,
                verification_sha256=hashlib.sha256(vp.read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(grouped,indent=2))


if __name__=='__main__':main()
