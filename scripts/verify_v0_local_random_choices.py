"""Check recorded local windows against independently consumed boundary RNG draws."""
from collections import defaultdict
import json
import random
if __package__:
    from .verify_v0_local_actions import verify_actions
else:
    from verify_v0_local_actions import verify_actions


def verify_random_choices(boundaries, streams, config):
    result=verify_actions(boundaries,streams,config)
    if config['mutation_probability']!=0:raise ValueError('This check requires fixed genomes')
    grouped={k:defaultdict(list) for k in ('local','feeding','terminal')}
    for k in grouped:
        for r in streams[k]:grouped[k][r['tick']].append(r)
    w,h=config['width'],config['height']
    def neighbors(p):
        x,y=p%w,p//w
        return list(dict.fromkeys([y*w+(x+1)%w,y*w+(x-1)%w,((y+1)%h)*w+x,((y-1)%h)*w+x]))
    for before,after in zip(boundaries,boundaries[1:]):
        rng=random.Random();state=before['rng_state'];rng.setstate((state[0],tuple(state[1]),state[2]))
        food=list(before['food'])
        for p,value in enumerate(food):
            if rng.randrange(1000)<config['regrowth_probability']:
                food[p]+=min(config['regrowth_amount'],config['food_capacity']-value)
        actors={a['id']:a for a in before['living']};occupied={a['position']:a['id'] for a in before['living']}
        ending={a['id']:a for a in after['living']};order=list(actors);rng.shuffle(order)
        local=grouped['local'][after['tick']]
        if order!=[r['id'] for r in local]:raise ValueError('Random action order differs')
        feeds={r['id']:r for r in grouped['feeding'][after['tick']]}
        deaths={r['id']:r for r in grouped['terminal'][after['tick']]}
        for row in local:
            identity=row['id'];actor=actors[identity];position=actor['position']
            if any(s['food']!=food[s['position']] for s in row['sites']):raise ValueError('Random regrowth/local food differs')
            energy=actor['energy']-min(actor['energy'],config['basal_cost'])
            if energy==0:
                del occupied[position];continue
            attempted=rng.randrange(1000)<actor['genome'];obs=feeds.get(identity,deaths.get(identity))
            if attempted!=obs['movement_attempted']:raise ValueError('Random movement decision differs')
            if attempted:
                energy-=min(energy,config['movement_cost'])
                if energy==0:
                    del occupied[position];continue
                destination=rng.choice(neighbors(position))
                if destination not in occupied:
                    del occupied[position];occupied[destination]=identity;position=destination
            feed=feeds[identity]
            if position!=feed['position']:raise ValueError('Random movement destination differs')
            intake=min(config['feeding_rate'],food[position]);food[position]-=intake;energy+=intake
            if energy>=config['birth_threshold']:
                empty=[p for p in neighbors(position) if p not in occupied]
                if empty:
                    destination=rng.choice(empty);child=feed['child_id']
                    if child is None or ending[child]['position']!=destination:raise ValueError('Random birth destination differs')
                    # The fixed-genome control still consumes the mutation decision.
                    rng.randrange(1000)
                    occupied[destination]=child
        if food!=after['food'] or json.loads(json.dumps(rng.getstate()))!=after['rng_state']:
            raise ValueError('Random ending state differs')
    return dict(**result,random_ticks_checked=len(boundaries)-1)


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
        counts=verify_random_choices(boundaries,streams,config)
        results.append(dict(**{k:r[k] for k in ('arm','birth_threshold','birth_cost','seed','endpoint','right_censored')},**counts))
    report=dict(results=results,input_sha256=hashes,action_ticks=800,actions=sum(r['actions'] for r in results),
        boundary_verification_sha256=sha(args.boundaries_verification),script_sha256=sha(Path(__file__)),
        action_helper_sha256=sha(Path(__file__).with_name('verify_v0_local_actions.py')),
        scope='Boundary-conditioned random draw reconstruction for regrowth, action order, movement, birth and mutation decisions, plus prior sequential accounting. This checks consistency of recorded replay states, not independent historical actor paths or causal effects.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(worlds=len(results),action_ticks=800,actions=report['actions'])))


if __name__=='__main__':main()
