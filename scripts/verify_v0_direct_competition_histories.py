"""Reconstruct direct-competition ancestry and life histories from physical events.

No runner imports. Per-tick group energy is bounded by the separate ledger gate;
complete individual energy is checked at recorded endpoints, not reconstructed
as a full movement/feeding history.
"""
from collections import Counter
from fractions import Fraction
if __package__:
    from .verify_v0_direct_competition_metrics import verify_records
else:
    from verify_v0_direct_competition_metrics import verify_records


def histogram(counter):
    return {str(k):v for k,v in sorted(counter.items()) if v}


def reconstruct(initial, rows, groups, events, lineage, result):
    mutation=result['mutation_probability'];seed=result['seed']
    verify_records(initial,rows,groups,result,len(rows)-1)
    mapping={int(k):v for k,v in initial['founder_groups'].items()}
    group_births=Counter();group_deaths=Counter()
    traits_by_group={g:result[g+'_trait'] for g in ('sampled','ancestor')}
    if mutation!=0:raise ValueError('Competition mutation must be disabled')
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
                    if tick!=0 or identity>=80 or event['genome']!=traits_by_group[mapping[identity]] or event['energy']!=24 or event['position']!=initial['founders'][identity]['position']:
                        raise ValueError('Founder event differs')
                    founder,generation=identity,0
                else:
                    if tick==0 or parent not in alive or born[parent]['tick']>=tick:
                        raise ValueError('Parent unavailable or not earlier')
                    delta=event['genome']-born[parent]['genome']
                    if abs(delta)>100 or (mutation==0 and delta):raise ValueError('Inheritance differs')
                    changed+=int(delta!=0);offspring[parent]+=1
                    founder,generation=born[parent]['founder_id'],born[parent]['generation']+1
                    group_births[mapping[founder]]+=1
                born[identity]=dict(event,founder_id=founder,generation=generation)
                alive.add(identity);ever[event['genome']]+=1
            elif event['event']=='death':
                if identity not in alive or born[identity]['tick']>=tick or event['energy']!=0:
                    raise ValueError('Invalid death')
                alive.remove(identity);deaths[identity]=event
                group_deaths[mapping[born[identity]['founder_id']]]+=1
            else:raise ValueError('Unknown compact event')
        if cursor<len(events) and events[cursor]['tick']<tick:raise ValueError('Events out of order')
        traits=Counter(born[i]['genome'] for i in alive)
        expected=dict(population=len(alive),births=len(born)-80,deaths=len(deaths),
            mean_genome=sum(k*v for k,v in traits.items())/len(alive) if alive else None,
            genome_variants=len(traits),founder_lineages=len({born[i]['founder_id'] for i in alive}),
            max_generation=max((born[i]['generation'] for i in alive),default=None),
            ever_genome_values=len(ever),changed_births=changed)
        if any(row[k]!=v for k,v in expected.items()):raise ValueError('Event-reconstructed metrics differ')
        for group in ('sampled','ancestor'):
            members=[born[i] for i in alive if mapping[born[i]['founder_id']]==group]
            expected_group=dict(population=len(members),births=group_births[group],deaths=group_deaths[group],
                founder_lineages=len({o['founder_id'] for o in members}),
                max_generation=max((o['generation'] for o in members),default=None),
                mean_genome=sum(o['genome'] for o in members)/len(members) if members else None)
            if any(groups[tick][group+'_'+k]!=v for k,v in expected_group.items()):
                raise ValueError('Event-reconstructed group metrics differ')
            if str(tick) in result['observations']:
                if result['observations'][str(tick)]['groups'][group]['living_genome_histogram']!=histogram(Counter(o['genome'] for o in members)):
                    raise ValueError('Event-reconstructed group histogram differs')
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
    for group in ('sampled','ancestor'):
        energy=sum(o['energy'] for o in living if mapping[o['founder_id']]==group)
        if energy!=groups[-1][group+'_organism_energy']:
            raise ValueError('Terminal lineage group energy differs')
    return dict(seed=seed,mutation_probability=mutation,metric_rows=len(rows),events=len(events),
        individuals=len(born),deaths=len(deaths),changed_births=changed,terminal_population=len(alive))



def source_contrasts(runs, sources):
    expected={(s,r,w) for s in sources for r in range(5) for w in (0,1)}
    if len(runs)!=len(expected) or {(r['source_seed'],r['replicate'],r['swap']) for r in runs}!=expected:
        raise ValueError('Incomplete source/replicate/swap grid')
    index={(r['source_seed'],r['replicate'],r['swap']):r for r in runs}
    observations=[];pairs=[];summaries=[]
    for source in sorted(sources):
        values=[]
        for replicate in range(5):
            contrasts=[]
            for swap in (0,1):
                run=index[source,replicate,swap]
                a,b=(run['groups'][g]['population'] for g in ('sampled','ancestor'))
                if any(type(n) is not int or n<0 for n in (a,b)) or a+b>1024:
                    raise ValueError('Invalid terminal populations')
                effect=Fraction(a-b,40);contrasts.append(effect)
                status='both_present' if a and b else 'sampled_only' if a else 'ancestor_only' if b else 'both_extinct'
                observations.append(dict(source_seed=source,replicate=replicate,swap=swap,
                    sampled_population=a,ancestor_population=b,status=status,contrast=str(effect),
                    sampled_fraction=str(Fraction(a,a+b)) if a+b else None))
            mean=sum(contrasts,Fraction())/2;values.append(mean)
            pairs.append(dict(source_seed=source,replicate=replicate,contrast=str(mean)))
        summaries.append(dict(source_seed=source,contrast=str(sum(values,Fraction())/5)))
    effects=[Fraction(r['contrast']) for r in summaries]
    mean=sum(effects,Fraction())/len(effects) if effects else None
    return dict(runs=observations,pairs=pairs,sources=summaries,
        mean_source_contrast=str(mean) if mean is not None else None,
        positive_sources=sum(v>0 for v in effects),zero_sources=sum(v==0 for v in effects),negative_sources=sum(v<0 for v in effects))
