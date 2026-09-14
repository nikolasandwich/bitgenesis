"""Reconstruct campaign-018 early actor lifecycles, energy and recorded movement."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
if __package__:
    from .analyze_v0_cohort_energy import budgets
else:
    from analyze_v0_cohort_energy import budgets


def verify_early(initial, metrics, streams):
    config=initial['config']; horizon=len(metrics)-1
    grouped={kind:defaultdict(list) for kind in ('feeding','terminal','energy')}
    for kind,rows in streams.items():
        for row in rows:
            if type(row['tick']) is not int or not 1<=row['tick']<=horizon:
                raise ValueError('Invalid early observation tick')
            grouped[kind][row['tick']].append(row)
    living={o['id']:dict(energy=o['energy'],founder=o['founder_id']) for o in initial['founders']}
    next_id=len(living); total_deaths=0
    counts=dict(feeding=0,terminal=0,energy=0,attempted_moves=0,successful_moves=0,
                occupied_target_blocks=0,movement_payment_deaths=0,basal_deaths=0)
    ordered=[]
    for tick in range(1,horizon+1):
        f,d,e=(grouped[k][tick] for k in ('feeding','terminal','energy'))
        feeds={r['id']:r for r in f};deaths={r['id']:r for r in d};ledgers={r['id']:r for r in e}
        if len(feeds)!=len(f) or len(deaths)!=len(d) or len(ledgers)!=len(e) or set(feeds)&set(deaths) or set(feeds)|set(deaths)!=set(living) or set(ledgers)!=set(living):
            raise ValueError('Early actors do not partition living IDs')
        ending={};children={};paid=uptake=0
        for identity,actor in living.items():
            row=ledgers[identity];feed=feeds.get(identity);terminal=deaths.get(identity)
            start=actor['energy']; basal=min(start,config['basal_cost'])
            observation=feed if feed is not None else terminal
            if observation['founder_id']!=actor['founder'] or type(observation['movement_attempted']) is not bool:
                raise ValueError('Founder identity or movement flag differs')
            attempted=observation['movement_attempted'];movement=min(start-basal,config['movement_cost']) if attempted else 0
            pos,previous=observation['position'],observation['position_before_action']
            if any(type(p) is not int or not 0<=p<config['width']*config['height'] for p in (pos,previous)):
                raise ValueError('Invalid observed position')
            if feed is not None:
                if feed['observation_schema']!=3 or feed['genome']!=250 or type(feed['moved']) is not bool or type(feed['birth_eligible']) is not bool:
                    raise ValueError('Invalid feeding schema')
                x,y=previous%config['width'],previous//config['width']
                neighbors={y*config['width']+(x+1)%config['width'],y*config['width']+(x-1)%config['width'],
                           ((y+1)%config['height'])*config['width']+x,((y-1)%config['height'])*config['width']+x}
                if feed['moved']!=(pos!=previous) or (feed['moved'] and (not attempted or pos not in neighbors)):
                    raise ValueError('Recorded movement displacement differs')
                eaten=feed['eaten'];before_food=feed['food_before']
                if any(type(feed[k]) is not int for k in ('eaten','food_before','food_after','empty_neighbors_before_birth')) or not 0<=before_food<=config['food_capacity'] or eaten!=min(config['feeding_rate'],before_food) or feed['food_after']!=before_food-eaten:
                    raise ValueError('Recorded intake differs')
                if start-basal-movement<=0 or feed['energy_before_feeding']!=start-basal-movement:
                    raise ValueError('Feeding reached without positive energy')
                eligible=start-basal-movement+eaten>=config['birth_threshold']
                space=feed['empty_neighbors_before_birth'];child_id=feed['child_id']
                if not 0<=space<=4 or feed['birth_eligible']!=eligible or (child_id is not None)!=(eligible and space>0):
                    raise ValueError('Birth eligibility or available-space outcome differs')
                counts['successful_moves']+=feed['moved']
                counts['occupied_target_blocks']+=attempted and not feed['moved']
            else:
                if terminal['observation_schema']!=1 or terminal['energy_before_action']!=start or pos!=previous:
                    raise ValueError('Invalid terminal observation')
                phase='basal' if start-basal==0 else 'movement'
                if terminal['phase']!=phase or (phase=='basal' and attempted) or (phase=='movement' and not attempted) or start-basal-movement!=0:
                    raise ValueError('Terminal payment phase differs')
                counts['basal_deaths' if phase=='basal' else 'movement_payment_deaths']+=1
                eaten=0;child_id=None
            counts['attempted_moves']+=attempted
            birth=config['birth_cost'] if child_id is not None else 0
            child_energy=(start-basal-movement+eaten-birth)//2 if child_id is not None else 0
            final=start-basal-movement+eaten-birth-child_energy
            expected=dict(observation_schema=1,tick=tick,id=identity,energy_before_action=start,
                          basal_paid=basal,movement_paid=movement,birth_paid=birth,eaten=eaten,
                          child_id=child_id,child_energy=child_energy,energy_after_action=final,died=terminal is not None)
            if row!=expected or type(row['died']) is not bool or any(type(row[k]) is not int for k in expected if k not in ('child_id','died')):
                raise ValueError('Individual energy ledger differs')
            if child_id is not None:
                if type(child_id) is not int or child_id in children:raise ValueError('Invalid child ID')
                children[child_id]=dict(energy=child_energy,founder=actor['founder'])
            if terminal is None:ending[identity]=dict(energy=final,founder=actor['founder'])
            paid+=basal+movement+birth;uptake+=eaten
        if sorted(children)!=list(range(next_id,next_id+len(children))):raise ValueError('Child sequence differs')
        next_id+=len(children);total_deaths+=len(d);living=ending|children
        now,before=metrics[tick],metrics[tick-1]
        if len(living)!=now['population'] or next_id-len(initial['founders'])!=now['births'] or total_deaths!=now['deaths'] or sum(o['energy'] for o in living.values())!=now['organism_energy'] or paid!=now['dissipated_energy']-before['dissipated_energy'] or uptake!=now['supplied_energy']-before['supplied_energy']+before['food_energy']-now['food_energy']:
            raise ValueError('Early global accounting differs')
        for kind,rows in (('feeding',f),('terminal',d),('energy',e)):counts[kind]+=len(rows)
        ordered.extend(e)
    if counts['attempted_moves']!=sum(counts[k] for k in ('successful_moves','occupied_target_blocks','movement_payment_deaths')):
        raise ValueError('Movement outcomes do not partition attempts')
    if config['movement_cost']==0 and (counts['movement_payment_deaths'] or any(r['movement_paid'] for r in ordered)):
        raise ValueError('Zero-charge movement dissipated energy or killed an actor')
    return dict(counts=counts,cohorts=budgets(ordered,{o['id']:o['energy'] for o in initial['founders']}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-018'))
    parser.add_argument('--metrics-verification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();verification=json.loads(args.metrics_verification.read_text(encoding='utf-8'))
    records=verification['runs'];grid={(a,t,c,s) for a in ('dispersed','block') for t in (40,160) for c in (0,1) for s in range(1500,1510)}
    if len(records)!=80 or {(r['arm'],r['birth_threshold'],r['movement_cost'],r['seed']) for r in records}!=grid:
        raise ValueError('Expected full metric-verified grid')
    results=[];hashes={}
    for r in records:
        key={k:r[k] for k in ('arm','birth_threshold','movement_cost','seed')}
        prefix=f"{r['arm']}-threshold-{r['birth_threshold']}-move-cost-{r['movement_cost']}-seed-{r['seed']}"
        ip=args.input/f'{prefix}-initial.json';mp=args.input/f'{prefix}.csv'
        for p in (ip,mp):
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            if digest!=verification['input_sha256'][p.name]:raise ValueError('Metric-verified input changed')
            hashes[p.name]=digest
        initial=json.loads(ip.read_text(encoding='utf-8'))
        with mp.open(encoding='utf-8',newline='') as stream:
            metrics=[{k:None if v=='' else float(v) if k=='mean_genome' else int(v) for k,v in row.items()} for row in csv.DictReader(stream)][:101]
        streams={}
        for kind in ('feeding','terminal','energy'):
            p=args.input/f'{prefix}-{kind}.jsonl';hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
            streams[kind]=[json.loads(line) for line in p.read_text(encoding='utf-8').splitlines()]
        results.append(dict(**key,**verify_early(initial,metrics,streams)))
    report=dict(results=results,input_sha256=hashes,verified_actor_ticks=8000,
        scope='Recorded early actor partitions, energy, genealogy labels and legal displacement. Unrecorded blocked destinations, birth positions and full local food histories are not reconstructed. No independent stochastic replay or unique causal claim.',
        metrics_verification_sha256=hashlib.sha256(args.metrics_verification.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        cohort_helper_sha256=hashlib.sha256(Path(__file__).with_name('analyze_v0_cohort_energy.py').read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(worlds=len(results),actor_ticks=8000,energy_records=sum(r['counts']['energy'] for r in results))))


if __name__=='__main__':main()
