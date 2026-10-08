"""Independent raw-event counts for selected sampled-cohesion cohorts."""
import json
from pathlib import Path


def event_ledger(directory,observed):
    root=Path(directory)
    units=json.loads((root/'initial.json').read_text(encoding='utf-8'))['units']
    parents=[];alive=[];births=[];deaths=[]
    for u in units:
        alive.append(None if u is None else len(parents))
        if u is not None:
            parents.append(None)
    states={0:set(i for i in alive if i is not None)}
    count=0
    with (root/'steps.jsonl').open(encoding='utf-8') as stream:
        for tick,line in enumerate(stream,1):
            row=json.loads(line);snapshot=observed['observations'][tick-1]
            if row['tick']!=tick or snapshot['tick']!=tick or snapshot['interaction_site_ids']!=alive:
                raise ValueError('event audit interaction identity mismatch')
            old=set(states[tick-1])
            for site in row['material']['dissolved']:
                if alive[site] is None:
                    raise ValueError('event audit invalid death')
                deaths.append((tick,alive[site]));alive[site]=None
            for p in row['material']['proposals']:
                if p['reason']=='formed':
                    parent=alive[p['source']]
                    if parent is None or parent not in old or alive[p['target']] is not None:
                        raise ValueError('event audit invalid birth')
                    identity=len(parents);parents.append(parent)
                    alive[p['target']]=identity;births.append((tick,identity))
            if snapshot['final_site_ids']!=alive:
                raise ValueError('event audit final identity mismatch')
            states[tick]=set(i for i in alive if i is not None)
            count=tick
    if count!=len(observed['observations']):
        raise ValueError('event horizon mismatch')
    return states,parents,births,deaths


def check(directory,observed,old_panels,panels,horizon=100):
    states,parents,births,deaths=event_ledger(directory,observed)
    key=lambda p:(p['phase'],p['boundary'],p['anchor'],p['horizon'])
    expected={key(p):p for p in old_panels if p['horizon']==horizon}
    if len(panels)!=len(expected) or {key(p) for p in panels}!=set(expected):
        raise ValueError('demographic panel coverage')
    total=0
    for panel in panels:
        original=expected[key(panel)]
        chosen=[r for r in original['records'] if r['anchor_size']>=2 and r['continuous_closed_multi']]
        if panel['initial_multi_components']!=sum(r['anchor_size']>=2 for r in original['records']) or panel['eligible_components']!=len(chosen):
            raise ValueError('conditional denominator mismatch')
        if len(panel['records'])!=len(chosen):
            raise ValueError('selected cohort coverage')
        t0=panel['anchor'] if panel['phase']=='final' else panel['anchor']-1
        t1=t0+horizon;anchor_ids=states[t0]
        root_cache={i:i for i in anchor_ids}
        def root(identity):
            if identity not in root_cache:
                ancestor=identity
                while ancestor is not None and ancestor not in anchor_ids:
                    ancestor=parents[ancestor]
                if ancestor is None:
                    raise ValueError('event lacks anchor ancestry')
                root_cache[identity]=ancestor
            return root_cache[identity]
        for old,saved in zip(chosen,panel['records']):
            members=set(old['anchor_members'])
            new_ids=sorted(i for t,i in births if t0<t<=t1 and root(i) in members)
            lost_ids=sorted(i for t,i in deaths if t0<t<=t1 and root(i) in members)
            remaining={i for i in states[t1] if root(i) in members}
            originals_lost=len(members & set(lost_ids))
            if len(remaining)!=len(members)+len(new_ids)-len(lost_ids):
                raise ValueError('independent demographic conservation')
            curve=[len(members & states[t]) for t in range(t0,t1+1)]
            expected_record=dict(component=old['component'],anchor_members=old['anchor_members'],
                anchor_size=len(members),anchor_world_units=len(anchor_ids),whole_world_anchor=members==anchor_ids,
                event_start=t0+1,event_end=t1,birth_ids=new_ids,death_ids=lost_ids,
                births=len(new_ids),deaths=len(lost_ids),original_deaths=originals_lost,
                descendant_deaths=len(lost_ids)-originals_lost,original_survivors_by_snapshot=curve,
                endpoint_population=len(remaining),endpoint_original_survivors=curve[-1],
                represented_anchor_members=len({root(i) for i in remaining}),
                category='stasis' if not new_ids and not lost_ids else 'births_only' if not lost_ids else 'with_deaths')
            if saved!=expected_record:
                raise ValueError('independent demographic record mismatch')
            if (len(remaining),curve[-1],expected_record['represented_anchor_members'])!=(
                    old['endpoint']['descendants'],old['endpoint']['original_survivors'],old['endpoint']['represented_anchor_members']):
                raise ValueError('independent study010 endpoint binding')
            total+=1
    return dict(panels=len(panels),cohort_windows=total,
        scope='raw-event identity reconstruction, backward anchor ancestry, birth/death and population conservation')
