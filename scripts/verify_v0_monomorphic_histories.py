"""Reconstruct campaign-022 histories independently from birth/death records."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
if __package__:
    from .verify_v0_monomorphic_metrics import initial_gate, metric_gate, read_metrics
else:
    from verify_v0_monomorphic_metrics import initial_gate, metric_gate, read_metrics


def histogram(counter):
    return {str(k):v for k,v in sorted(counter.items()) if v}


def reconstruct(initial, rows, events, lineage, result):
    mutation=result['mutation_probability'];seed=result['seed']
    initial_gate(initial,seed,mutation);metric_gate(rows,mutation,len(rows)-1)
    born={};alive=set();deaths={};offspring=Counter();ever=Counter();changed=0;cursor=0
    for tick,row in enumerate(rows):
        while cursor<len(events) and events[cursor]['tick']==tick:
            event=events[cursor];cursor+=1;identity=event['id']
            if type(identity) is not int or type(event['tick']) is not int or type(event['position']) is not int or not 0<=event['position']<1024:
                raise ValueError('Invalid event identity or location')
            if event['event']=='birth':
                if identity!=len(born) or event['birth_tick']!=tick or type(event['genome']) is not int or not 0<=event['genome']<=1000 or type(event['energy']) is not int or event['energy']<1:
                    raise ValueError('Invalid birth identity, trait or energy')
                parent=event['parent_id']
                if parent is None:
                    if tick!=0 or identity>=80 or event['genome']!=250 or event['energy']!=24 or event['position']!=initial['founders'][identity]['position']:
                        raise ValueError('Founder event differs')
                    founder,generation=identity,0
                else:
                    if tick==0 or parent not in alive or born[parent]['tick']>=tick:
                        raise ValueError('Parent unavailable or not earlier')
                    delta=event['genome']-born[parent]['genome']
                    if abs(delta)>100 or (mutation==0 and delta):raise ValueError('Inheritance differs')
                    changed+=int(delta!=0);offspring[parent]+=1
                    founder,generation=born[parent]['founder_id'],born[parent]['generation']+1
                born[identity]=dict(event,founder_id=founder,generation=generation)
                alive.add(identity);ever[event['genome']]+=1
            elif event['event']=='death':
                if identity not in alive or born[identity]['tick']>=tick or event['energy']!=0:
                    raise ValueError('Invalid death')
                alive.remove(identity);deaths[identity]=event
            else:raise ValueError('Unknown compact event')
        if cursor<len(events) and events[cursor]['tick']<tick:raise ValueError('Events out of order')
        traits=Counter(born[i]['genome'] for i in alive)
        expected=dict(population=len(alive),births=len(born)-80,deaths=len(deaths),
            mean_genome=sum(k*v for k,v in traits.items())/len(alive) if alive else None,
            genome_variants=len(traits),founder_lineages=len({born[i]['founder_id'] for i in alive}),
            max_generation=max((born[i]['generation'] for i in alive),default=None),
            ever_genome_values=len(ever),changed_births=changed)
        if any(row[k]!=v for k,v in expected.items()):raise ValueError('Event-reconstructed metrics differ')
        if str(tick) in result['observations']:
            obs=result['observations'][str(tick)]
            if obs['living_genome_histogram']!=histogram(traits) or obs['ever_born_genome_histogram']!=histogram(ever):
                raise ValueError('Checkpoint histogram differs')
    if cursor!=len(events):raise ValueError('Events beyond horizon or out of order')
    if len(lineage)!=len(born) or {o['id'] for o in lineage}!=set(born):raise ValueError('Lineage identity set differs')
    for o in lineage:
        b=born[o['id']];d=deaths.get(o['id'])
        expected=dict(parent_id=b['parent_id'],founder_id=b['founder_id'],generation=b['generation'],
            birth_tick=b['tick'],genome=b['genome'],offspring=offspring[o['id']],death_tick=d['tick'] if d else None)
        if any(o[k]!=v for k,v in expected.items()):raise ValueError('Lineage history differs')
        if d and (o['energy']!=0 or o['position']!=d['position']):raise ValueError('Dead lineage endpoint differs')
        if not d and (type(o['energy']) is not int or o['energy']<1 or type(o['position']) is not int or not 0<=o['position']<1024):raise ValueError('Invalid living lineage endpoint')
    living=[o for o in lineage if o['id'] in alive]
    if len({o['position'] for o in living})!=len(living) or sum(o['energy'] for o in living)!=rows[-1]['organism_energy']:
        raise ValueError('Living positions or energy differ')
    return dict(seed=seed,mutation_probability=mutation,metric_rows=len(rows),events=len(events),
        individuals=len(born),deaths=len(deaths),changed_births=changed,terminal_population=len(alive))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-022'))
    parser.add_argument('--metrics-verification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();gate=json.loads(args.metrics_verification.read_text(encoding='utf-8'))
    if gate['metric_rows_checked']!=400040 or gate['initial_states_checked']!=40 or gate['paired_initial_groups']!=20 or len(gate['runs'])!=40:
        raise ValueError('Incomplete metric gate')
    grid={(s,m) for s in range(1900,1920) for m in (0,100)}
    if {(r['seed'],r['mutation_probability']) for r in gate['runs']}!=grid:raise ValueError('Metric identity grid differs')
    if hashlib.sha256((args.input/'metadata.json').read_bytes()).hexdigest()!=gate['metadata_sha256']:raise ValueError('Metadata changed')
    verified=[];hashes={}
    for r in gate['runs']:
        folder=args.input/f"mutation-{r['mutation_probability']}-seed-{r['seed']}"
        for name in ('initial.json','metrics.csv','result.json','events.jsonl','lineage.json'):
            p=folder/name;key=p.relative_to(args.input).as_posix();digest=hashlib.sha256(p.read_bytes()).hexdigest();hashes[key]=digest
            if name in ('initial.json','metrics.csv','result.json') and digest!=gate['input_sha256'][key]:raise ValueError('Verified input changed')
        load=lambda name:json.loads((folder/name).read_text(encoding='utf-8'))
        result=load('result.json')
        if {k:v for k,v in result.items() if k!='observations'}!=r:raise ValueError('World summary changed')
        events=[json.loads(s) for s in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        verified.append(reconstruct(load('initial.json'),read_metrics(folder/'metrics.csv'),events,load('lineage.json'),result))
    pairs=[]
    for seed in range(1900,1920):
        worlds={r['mutation_probability']:r for r in gate['runs'] if r['seed']==seed}
        a,b=worlds[0]['population']>0,worlds[100]['population']>0
        status='both_alive' if a and b else 'mutation_only' if b else 'no_mutation_only' if a else 'both_extinct'
        pairs.append(dict(seed=seed,status=status,no_mutation_population=worlds[0]['population'],mutation_population=worlds[100]['population']))
    counts={k:sum(p['status']==k for p in pairs) for k in ('both_alive','mutation_only','no_mutation_only','both_extinct')}
    report=dict(scope='Complete birth/death, lineage and trait reconstruction with independent aggregate gate. No full movement paths, mutation-attempt reconstruction or causal adaptation claim.',results=verified,pairs=pairs,counts=counts,signed_discordance=counts['mutation_only']-counts['no_mutation_only'],input_sha256=hashes,metric_verification_sha256=hashlib.sha256(args.metrics_verification.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),metric_helper_sha256=hashlib.sha256(Path(__file__).with_name('verify_v0_monomorphic_metrics.py').read_bytes()).hexdigest())
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(counts=counts,signed_discordance=report['signed_discordance'],individuals=sum(v['individuals'] for v in verified),metric_rows=sum(v['metric_rows'] for v in verified)),indent=2))


if __name__=='__main__':main()
