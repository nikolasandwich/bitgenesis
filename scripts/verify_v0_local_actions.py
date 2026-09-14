"""Reconcile recorded local actions with boundary maps; no stochastic path replay."""
from collections import defaultdict


def verify_actions(boundaries, streams, config):
    grouped={kind:defaultdict(list) for kind in ('local','feeding','terminal','energy')}
    allowed=set(range(boundaries[0]['tick']+1,boundaries[-1]['tick']+1))
    for kind in grouped:
        for row in streams[kind]:
            if type(row['tick']) is not int or row['tick'] not in allowed:raise ValueError('Action outside window')
            grouped[kind][row['tick']].append(row)
    width,height=config['width'],config['height'];size=width*height
    def neighbors(p):
        x,y=p%width,p//width
        return list(dict.fromkeys([y*width+(x+1)%width,y*width+(x-1)%width,((y+1)%height)*width+x,((y-1)%height)*width+x]))
    counts=dict(actions=0,current_site_food=0,free_neighbor_food=0,basal_deaths=0)
    for before,after in zip(boundaries,boundaries[1:]):
        tick=after['tick']
        if tick!=before['tick']+1:raise ValueError('Nonconsecutive boundaries')
        local,feeding,terminal,energy=(grouped[k][tick] for k in ('local','feeding','terminal','energy'))
        living={a['id']:dict(a) for a in before['living']};ending={a['id']:a for a in after['living']}
        feeds={a['id']:a for a in feeding};deaths={a['id']:a for a in terminal};ledgers={a['id']:a for a in energy}
        order=[r['id'] for r in local]
        if len(order)!=len(living) or set(order)!=set(living) or [r['id'] for r in energy]!=order or len(feeds)!=len(feeding) or len(deaths)!=len(terminal) or set(feeds)&set(deaths) or set(feeds)|set(deaths)!=set(living):raise ValueError('Action partition/order differs')
        if [i for i in order if i in feeds]!=[r['id'] for r in feeding] or [i for i in order if i in deaths]!=[r['id'] for r in terminal]:raise ValueError('Substream order differs')
        eaten=[0]*size
        for row in feeding:
            if type(row['position']) is not int or not 0<=row['position']<size or type(row['eaten']) is not int or row['eaten']<0:raise ValueError('Invalid intake')
            eaten[row['position']]+=row['eaten']
        food=[a+b for a,b in zip(after['food'],eaten)]
        growth=[a-b for a,b in zip(food,before['food'])]
        if any(g not in (0,min(config['regrowth_amount'],config['food_capacity']-old)) for g,old in zip(growth,before['food'])) or sum(growth)!=after['metrics']['supplied_energy']-before['metrics']['supplied_energy']:raise ValueError('Inferred regrowth differs')
        occupied={a['position']:a['id'] for a in living.values()}
        next_id=config['initial_population']+before['metrics']['births']
        paid=0
        for local_row in local:
            identity=local_row['id'];actor=living[identity];start=actor['energy'];position=actor['position']
            sites=list(dict.fromkeys([position,*neighbors(position)]))
            expected_local=dict(observation_schema=1,tick=tick,id=identity,founder_id=actor['founder_id'],position=position,energy_before_action=start,sites=[dict(position=p,food=food[p],occupant_id=occupied.get(p)) for p in sites])
            if local_row!=expected_local:raise ValueError('Local resource snapshot differs')
            counts['actions']+=1;counts['current_site_food']+=food[position]>0
            counts['free_neighbor_food']+=any(p not in occupied and food[p]>0 for p in neighbors(position))
            obs=feeds.get(identity,deaths.get(identity));attempted=obs['movement_attempted']
            if type(attempted) is not bool or obs['position_before_action']!=position or obs['founder_id']!=actor['founder_id']:raise ValueError('Action identity differs')
            basal=min(start,config['basal_cost']);movement=min(start-basal,config['movement_cost']) if attempted else 0
            available=start-basal-movement;birth=child_energy=intake=0;child_id=None
            if identity in deaths:
                phase='basal' if start==basal else 'movement'
                if available!=0 or obs['phase']!=phase or obs['position']!=position or obs['energy_before_action']!=start or (phase=='basal' and attempted) or (phase=='movement' and not attempted):raise ValueError('Terminal phase differs')
                counts['basal_deaths']+=phase=='basal';del occupied[position];del living[identity]
            else:
                if available<=0 or obs['energy_before_feeding']!=available or obs['genome']!=250:raise ValueError('Feeding energy differs')
                destination=obs['position'];moved=destination!=position
                if type(obs['moved']) is not bool or obs['moved']!=moved or (moved and (not attempted or destination not in neighbors(position) or destination in occupied)):raise ValueError('Movement differs')
                if moved:del occupied[position];occupied[destination]=identity;actor['position']=destination
                intake=min(config['feeding_rate'],food[destination])
                if obs['food_before']!=food[destination] or obs['eaten']!=intake or obs['food_after']!=food[destination]-intake:raise ValueError('Sequential food write differs')
                food[destination]-=intake;available+=intake
                empty=[p for p in neighbors(destination) if p not in occupied]
                eligible=available>=config['birth_threshold'];child_id=obs['child_id']
                if obs['birth_eligible']!=eligible or obs['empty_neighbors_before_birth']!=len(empty) or (child_id is not None)!=(eligible and bool(empty)):raise ValueError('Birth space differs')
                if child_id is not None:
                    if type(child_id) is not int or child_id!=next_id or child_id not in ending:raise ValueError('Child sequence differs')
                    next_id+=1;birth=config['birth_cost'];available-=birth;child_energy=available//2;available-=child_energy
                    child=ending[child_id]
                    if child['position'] not in empty or child['parent_id']!=identity or child['founder_id']!=actor['founder_id'] or child['generation']!=actor['generation']+1 or child['birth_tick']!=tick or child['energy']!=child_energy or child['genome']!=250 or child['offspring']!=0:raise ValueError('Child boundary differs')
                    living[child_id]=dict(child);occupied[child['position']]=child_id;actor['offspring']+=1
                actor['energy']=available
            expected_energy=dict(observation_schema=1,tick=tick,id=identity,energy_before_action=start,basal_paid=basal,movement_paid=movement,birth_paid=birth,eaten=intake,child_id=child_id,child_energy=child_energy,energy_after_action=available,died=identity in deaths)
            if ledgers[identity]!=expected_energy:raise ValueError('Action energy differs')
            paid+=basal+movement+birth
        if food!=after['food'] or living!=ending or sorted(occupied.items())!=[tuple(x) for x in after['occupied']] or next_id!=config['initial_population']+after['metrics']['births'] or paid!=after['metrics']['dissipated_energy']-before['metrics']['dissipated_energy']:raise ValueError('Ending spatial state differs')
    return counts


def main():
    import argparse
    import hashlib
    import json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/local-resource-replay-019'))
    parser.add_argument('--original',type=Path,default=Path('data/campaign-019'))
    parser.add_argument('--boundaries-verification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    verified=json.loads(args.boundaries_verification.read_text(encoding='utf-8'))
    if sha(args.input/'metadata.json')!=verified['metadata_sha256'] or sha(args.input/'results.json')!=verified['results_sha256']:raise ValueError('Boundary-verified replay changed')
    records=json.loads((args.input/'results.json').read_text(encoding='utf-8'));results=[];hashes={}
    for r in records:
        prefix=f"block-threshold-{r['birth_threshold']}-birth-cost-{r['birth_cost']}-seed-{r['seed']}"
        ip=args.original/(prefix+'-initial.json');bp=args.input/(prefix+'-boundaries.jsonl')
        for p in (ip,bp):
            hashes[p.name]=sha(p)
            if hashes[p.name]!=verified['input_sha256'][p.name]:raise ValueError('Boundary-verified input changed')
        config=json.loads(ip.read_text(encoding='utf-8'))['config']
        boundaries=[json.loads(l) for l in bp.read_text(encoding='utf-8').splitlines()];streams={}
        for kind in ('local','feeding','terminal','energy'):
            p=args.input/f'{prefix}-{kind}.jsonl';hashes[p.name]=sha(p)
            if hashes[p.name]!=r['output_sha256'][kind]:raise ValueError('Recorded stream changed')
            streams[kind]=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
            if len(streams[kind])!=r['counts'][kind]:raise ValueError('Stream count differs')
        counts=verify_actions(boundaries,streams,config)
        results.append(dict(**{k:r[k] for k in ('arm','birth_threshold','birth_cost','seed','endpoint','right_censored')},**counts))
    report=dict(results=results,input_sha256=hashes,action_ticks=800,actions=sum(r['actions'] for r in results),
        boundary_verification_sha256=sha(args.boundaries_verification),script_sha256=sha(Path(__file__)),
        scope='Sequential recorded-action consistency with boundary maps and inferred per-site growth. Uses recorded action order/movement and newborn ending positions; does not independently reproduce random choices or prove historical action paths. Descriptive endpoint-conditioned counts, not causal effects.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(worlds=len(results),action_ticks=800,actions=report['actions'])))


if __name__=='__main__':main()
