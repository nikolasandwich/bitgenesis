"""Lifecycle-based demographic observation of already selected cohesive cohorts."""


def measure(lives, anchor_ids, members, phase, anchor, horizon):
    if phase not in ('interaction','final') or type(horizon) is not int or horizon<1:
        raise ValueError('valid phase and positive horizon required')
    start = anchor-(phase=='interaction')
    end = start+horizon
    if type(anchor) is not int or start<0:
        raise ValueError('invalid anchor')
    for i,r in enumerate(lives):
        if r['id']!=i or type(r['birth_tick']) is not int or r['birth_tick']<0:
            raise ValueError('ordered birth identities required')
        d=r['death_tick']
        if d is not None and (type(d) is not int or d<=r['birth_tick']):
            raise ValueError('invalid lifespan')
        p=r['parent']
        if p is not None and (type(p) is not int or not 0<=p<i or
                lives[p]['birth_tick']>=r['birth_tick'] or
                (lives[p]['death_tick'] is not None and lives[p]['death_tick']<=r['birth_tick'])):
            raise ValueError('invalid parent lifecycle')
    def alive(r,t):
        return r['birth_tick']<=t and (r['death_tick'] is None or t<r['death_tick'])
    anchors=set(anchor_ids)
    originals=set(members)
    if len(anchors)!=len(anchor_ids) or anchors!={r['id'] for r in lives if alive(r,start)}:
        raise ValueError('complete anchor population required')
    if not originals or len(originals)!=len(members) or not originals<=anchors:
        raise ValueError('anchor component members required')
    roots=[]
    for r in lives:
        roots.append(r['id'] if r['id'] in anchors else None if r['parent'] is None else roots[r['parent']])
    for r,root in zip(lives,roots):
        if root is None and (alive(r,end) or start<r['birth_tick']<=end):
            raise ValueError('missing anchor ancestry')
    cohort=[r for r,root in zip(lives,roots) if root in originals]
    births=[r['id'] for r in cohort if start<r['birth_tick']<=end]
    deaths=[r['id'] for r in cohort if r['death_tick'] is not None and start<r['death_tick']<=end]
    survivors=[r['id'] for r in cohort if alive(r,end)]
    original_curve=[sum(alive(lives[i],t) for i in originals) for t in range(start,end+1)]
    original_deaths=len(originals & set(deaths))
    if len(survivors)!=len(originals)+len(births)-len(deaths) or original_curve[-1]!=len(originals)-original_deaths:
        raise ValueError('population conservation failure')
    if not survivors:
        raise ValueError('selected cohesive cohort cannot be extinct')
    return dict(event_start=start+1,event_end=end,birth_ids=births,death_ids=deaths,
        births=len(births),deaths=len(deaths),original_deaths=original_deaths,
        descendant_deaths=len(deaths)-original_deaths,
        original_survivors_by_snapshot=original_curve,endpoint_population=len(survivors),
        endpoint_original_survivors=original_curve[-1],
        represented_anchor_members=len({roots[i] for i in survivors}),
        category='with_deaths' if deaths else 'births_only' if births else 'stasis')


def observe(lives,observed,panels,horizon=100):
    snapshots={r['tick']:r for r in observed['observations']}
    output=[]
    for panel in panels:
        if panel['horizon']!=horizon:
            continue
        phase,anchor=panel['phase'],panel['anchor']
        anchor_ids=[i for i in snapshots[anchor][phase+'_site_ids'] if i is not None]
        selected=[r for r in panel['records'] if r['anchor_size']>=2 and r['continuous_closed_multi']]
        records=[]
        for row in selected:
            result=measure(lives,anchor_ids,row['anchor_members'],phase,anchor,horizon)
            if (result['endpoint_population'],result['endpoint_original_survivors'],result['represented_anchor_members'])!=(
                    row['endpoint']['descendants'],row['endpoint']['original_survivors'],row['endpoint']['represented_anchor_members']):
                raise ValueError('study010 endpoint binding')
            records.append(dict(component=row['component'],anchor_members=row['anchor_members'],
                anchor_size=row['anchor_size'],anchor_world_units=row['anchor_world_units'],
                whole_world_anchor=row['whole_world_anchor'],**result))
        output.append(dict(**{k:panel[k] for k in ('phase','boundary','anchor','horizon')},
            initial_multi_components=sum(r['anchor_size']>=2 for r in panel['records']),
            eligible_components=len(selected),records=records))
    return output
