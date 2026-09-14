"""V2 construction/life-history ledger audit, independent of world execution."""
from collections import Counter,defaultdict
from hashlib import sha256
import json
from pathlib import Path

from .construction_audit import audit_run,require
from .spatial_audit import reconstruct
from bitgenesis.v1.decision_audit import check_decision


def audit(directory):
    root=Path(directory)
    construction=audit_run(root)
    def read(name):
        return json.loads((root/name).read_text(encoding='utf-8'))
    meta,initial,final,summary=(read(n) for n in ('metadata.json','initial.json','final.json','summary.json'))
    hashes={name:sha256((root/name).read_bytes()).hexdigest() for name in ('initial.json','final.json','steps.jsonl','events.jsonl','summary.json')}
    require(hashes==meta['output_sha256'],'output hashes')
    c=meta['config']
    attempts=final['attempts']
    require(initial['tick']==0 and final['tick']==meta['steps']==meta['completed_steps'],'horizon')
    require(initial['attempts']==attempts[:c['founders']] and len(initial['attempts'])==c['founders'],'initial attempts')
    if 'founder_genomes' in meta:
        require(meta['founder_genomes']==[a['genome'] for a in initial['attempts']],'assigned founder genomes')
    require(initial['food']==[c['initial_food']]*(c['width']*c['height']),'initial food')
    initial_cost=sum(a['construction_cost']+a['failure_loss'] for a in initial['attempts'])
    require(initial_cost==initial['initialization_spent']==final['initialization_spent'],'initial expense')
    events=defaultdict(list)
    previous=0
    with (root/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            e=json.loads(line)
            require(type(e['tick']) is int and previous<=e['tick']<=meta['steps'],'event tick order')
            previous=e['tick']
            events[e['tick']].append(e)
    alive,born,dead={}, {}, {}
    offspring=Counter()
    next_attempt=0

    def process_attempt(iterator,parent,tick,allocation):
        nonlocal next_attempt
        e=next(iterator,None)
        require(e is not None and e['event']=='development','missing development event')
        require(next_attempt<len(attempts),'extra attempt')
        a=attempts[next_attempt]
        require(e=={'event':'development',**a} and a['id']==next_attempt,'attempt record mismatch')
        require(a['parent']==parent and a['tick']==tick and a['allocation']==allocation,'attempt identity/allocation')
        if parent is None:
            require(tick==0,'late founder')
        else:
            require(parent in born and born[parent]['birth_tick']<tick,'invalid developmental parent')
            old=born[parent]['genome']
            field='genes' if meta['encoding']=='developmental' else 'weights'
            changes=[(i,abs(x-y)) for i,(x,y) in enumerate(zip(old[field],a['genome'][field])) if x!=y]
            require(len(changes)<=1,'multiple mutation coordinates')
            require(not changes or c['mutation_per_thousand']>0,'mutation disabled')
            for i,delta in changes:
                radius=10 if field=='weights' or i in (1,3,5,8) else 1
                require(delta<=radius,'mutation step bound')
        next_attempt+=1
        if a['valid']:
            birth=next(iterator,None)
            require(birth is not None and birth['event']=='birth','missing viable birth')
            identifier=a['id']
            expected={'id':identifier,'parent':parent,'founder':identifier if parent is None else born[parent]['founder'],
                      'generation':0 if parent is None else born[parent]['generation']+1,
                      'birth_tick':tick,'x':a['x'],'y':a['y'],'energy':a['living_energy'],
                      'genome':a['genome'],'controller':{'weights':a['construction']['weights']},
                      'mode':meta['mode'] if parent is None else born[parent]['mode'],
                      'death_tick':None,'offspring':0}
            require(birth=={'event':'birth','tick':tick,**expected},'constructed birth state')
            born[identifier]=expected
            alive[identifier]=expected['energy']
            if parent is not None:
                offspring[parent]+=1
        return a

    initial_events=iter(events.pop(0,[]))
    for _ in range(c['founders']):
        process_attempt(initial_events,None,0,c['initial_energy'])
    require(next(initial_events,None) is None,'extra initial event')
    require(initial['lineage']==list(born.values()),'initial lineage')
    total=sum(initial['food'])+c['founders']*c['initial_energy']-initial_cost
    require(total==sum(initial['food'])+sum(alive.values()),'initial energy')
    actor_count=0
    ticks=0
    with (root/'steps.jsonl').open(encoding='utf-8') as stream:
        for ticks,line in enumerate(stream,1):
            row=json.loads(line)
            require(row['tick']==ticks and row['energy_before']==total,'tick continuity')
            actors=row['actors']
            require(len(actors)==len(alive) and {r['id'] for r in actors}==set(alive),'actor set or newborn timing')
            tick_events=iter(events.pop(ticks,[]))
            spent=0
            for r in actors:
                identifier=r['id']
                require(r['tick']==ticks and r['energy_before']==alive[identifier],'actor energy continuity')
                check_decision(r,born[identifier]['controller']['weights'],born[identifier]['mode'])
                energy=alive[identifier]
                phase_death=None
                for phase,cost in (('basal',c['basal_cost']),('decision',c['decision_cost']),('movement',c['movement_cost'] if r['action'] else 0)):
                    paid=min(energy,cost) if phase_death is None else 0
                    require(type(r[phase]) is int and r[phase]==paid,'phase charge')
                    energy-=paid
                    if energy==0 and phase_death is None:
                        phase_death=phase
                for field in ('intake','birth_cost','development_cost','failure_loss','child_energy','energy_after'):
                    require(type(r[field]) is int and r[field]>=0,'energy field bounds')
                if phase_death:
                    require(all(r[k]==0 for k in ('intake','birth_cost','development_cost','failure_loss','child_energy','energy_after')) and 'development_attempt' not in r,'post-death action')
                    require(next(tick_events,None)=={'event':'death','tick':ticks,'id':identifier,'phase':phase_death},'death record')
                    del alive[identifier]
                    dead[identifier]=ticks
                else:
                    require(r['intake']<=c['feeding_limit'],'intake bound')
                    energy+=r['intake']
                    if 'development_attempt' in r:
                        require(energy>=c['birth_threshold'] and r['birth_cost']==c['birth_cost'],'birth eligibility')
                        energy-=r['birth_cost']
                        allocation=energy//2
                        require(r['development_attempt']==next_attempt,'attempt actor identity')
                        a=process_attempt(tick_events,identifier,ticks,allocation)
                        require((r['development_cost'],r['failure_loss'],r['child_energy'])==(a['construction_cost'],a['failure_loss'],a['living_energy']),'attempt transfer ledger')
                        energy-=allocation
                    else:
                        require(all(r[k]==0 for k in ('birth_cost','development_cost','failure_loss','child_energy')),'unrecorded development charges')
                    require(energy==r['energy_after'],'actor final energy')
                    alive[identifier]=energy
                spent+=sum(r[k] for k in ('basal','decision','movement','birth_cost','development_cost','failure_loss'))
            require(next(tick_events,None) is None,'extra tick event')
            require(type(row['resource_added']) is int and 0<=row['resource_added']<=c['width']*c['height']*c['renewal_amount'],'resource bound')
            total+=row['resource_added']-spent
            require(row['spent']==spent and row['energy_after']==total and row['population']==len(alive),'global ledger')
            actor_count+=len(actors)
    require(ticks==meta['steps'] and not events and next_attempt==len(attempts),'incomplete history')
    require([o['id'] for o in final['lineage']]==list(born),'final lineage IDs')
    occupied=set()
    for o in final['lineage']:
        identifier=o['id']
        for field in ('parent','founder','generation','birth_tick','genome','controller','mode'):
            require(o[field]==born[identifier][field],'final inherited state')
        require(o['offspring']==offspring[identifier] and o['death_tick']==dead.get(identifier) and o['energy']==alive.get(identifier,0),'final life history')
        require(type(o['x']) is int and type(o['y']) is int and 0<=o['x']<c['width'] and 0<=o['y']<c['height'],'position bounds')
        if identifier in alive:
            position=(o['x'],o['y'])
            require(position not in occupied,'overlap')
            occupied.add(position)
    require(len(final['food'])==c['width']*c['height'] and all(type(f) is int and 0<=f<=c['capacity'] for f in final['food']),'food bounds')
    require(total==sum(final['food'])+sum(alive.values()),'final total energy')
    expected={'steps':ticks,'population':len(alive),'individuals':len(born),'actor_records':actor_count,
              'births':sum(o['parent'] is not None for o in born.values()),'founder_attempts':c['founders'],
              'successful_founders':sum(o['parent'] is None for o in born.values()),'attempts':len(attempts),
              'failed_attempts':sum(not a['valid'] for a in attempts),'construction_cost':construction['construction_cost'],
              'failure_loss':construction['failure_loss'],'deaths':len(dead),'total_energy':total}
    require(summary==expected,'summary mismatch')
    spatial=reconstruct(root)
    return {'scope':'construction, ancestry, decisions, energy and spatial reconstruction; five RNG streams from recorded initial states; initialization/mutation RNG not replayed',
            **spatial,
            'summary':expected,'construction_audit':construction,'input_sha256':hashes,
            'audit_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'decision_audit_sha256':sha256(Path(__file__).parents[1].joinpath('v1/decision_audit.py').read_bytes()).hexdigest()}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=audit(args.directory)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result['summary'],indent=2))
