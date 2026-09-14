"""Persist isolated continuations with explicit boundary records."""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import platform

from .interventions import boundary, INTERVENTION_VERSION
from .runner import encoded, save, state
from .world import RULES_VERSION


def run_branch(output, origin, steps, *, remove_founder=None, deposits=None,
               max_actor_records=1000000):
    """Copy an in-memory common state; deposits map absolute boundary tick to pairs.

    Prefix records and scientific target selection remain the caller's job.
    This new format is deliberately distinct from ordinary v3-run-1 output.
    """
    if type(steps) is not int or not 1 <= steps <= 100000:
        raise ValueError('branch steps must be in1..100000')
    if type(max_actor_records) is not int or max_actor_records < origin.config.width*origin.config.height*steps:
        raise ValueError('branch recording budget exceeded')
    schedule={} if deposits is None else {tick:list(items) for tick,items in deposits.items()}
    if any(type(tick) is not int or not origin.tick <= tick < origin.tick+steps for tick in schedule):
        raise ValueError('deposit boundary outside branch horizon')
    # Validate every request on disposable state before creating any output.
    validation=deepcopy(origin)
    boundary(validation,remove_founder=remove_founder)
    for items in schedule.values():
        boundary(validation,b_additions=items)
    world=deepcopy(origin)
    world.events.clear()  # Prefix events belong to the caller's common history.
    root=Path(output)
    root.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).parent
    sources={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(source.glob('*.py'))}
    for name in ('v1/controller.py','v2/development.py'):
        sources['../'+name]=sha256((source.parent/name).read_bytes()).hexdigest()
    metadata=dict(schema='v3-branch-1',status='running',rules=RULES_VERSION,
                  intervention_rules=INTERVENTION_VERSION,python=platform.python_version(),
                  config=asdict(world.config),seed=world.seed,start_tick=world.tick,
                  steps=steps,completed_steps=0,remove_founder=remove_founder,
                  deposits={str(t):items for t,items in schedule.items()},
                  max_actor_records=max_actor_records,source_sha256=sources)
    save(root/'metadata.json',metadata)
    try:
        save(root/'initial.json',state(world))
        counts=dict(actor_records=0,exported_energy=0,imported_energy=0,rejected_import=0)
        with (root/'steps.jsonl').open('w',encoding='utf-8') as records, \
             (root/'events.jsonl').open('w',encoding='utf-8') as events:
            for index in range(steps):
                intervention=boundary(world,remove_founder=remove_founder if index==0 else None,
                                      b_additions=schedule.get(world.tick,()))
                row=world.step()
                records.write(encoded(dict(boundary=intervention,step=row)))
                for event in world.events:
                    events.write(encoded(event))
                world.events.clear()
                counts['actor_records']+=len(row['actors'])
                for key in ('exported_energy','imported_energy','rejected_import'):
                    counts[key]+=intervention[key]
                metadata['completed_steps']=index+1
        save(root/'final.json',state(world))
        summary=dict(**counts,population=len(world.organisms),total_energy=world.total_energy(),
                     branch_births=sum(o.birth_tick>origin.tick for o in world.lineage.values()))
        save(root/'summary.json',summary)
        metadata.update(status='complete',output_sha256={name:sha256((root/name).read_bytes()).hexdigest()
            for name in ('initial.json','steps.jsonl','events.jsonl','final.json','summary.json')})
        save(root/'metadata.json',metadata)
        return summary
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        save(root/'metadata.json',metadata)
        raise


def donor_schedule(reference, founder):
    """Reference tick t releases become treatment imports before t+1.

    Terminal-tick releases cannot affect this horizon and are excluded. This
    merely prepares a schedule; reference validation belongs to the assay gate.
    """
    root=Path(reference)
    meta=json.loads((root/'metadata.json').read_text())
    if meta['schema']!='v3-branch-1' or meta['status']!='complete' or meta['remove_founder'] is not None or meta['deposits']:
        raise ValueError('an intact reference branch is required')
    final=json.loads((root/'final.json').read_text())
    ids={o['id'] for o in final['lineage'] if o['founder']==founder}
    if founder not in ids:
        raise ValueError('unknown reference founder')
    schedule={}
    with (root/'steps.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)['step']
            if row['tick']>=meta['start_tick']+meta['steps']:
                continue
            additions=[(actor['feeding']['site'],actor['feeding']['released_b'])
                       for actor in row['actors'] if actor['id'] in ids
                       and actor['feeding'] is not None and actor['feeding']['released_b']>0]
            if additions:
                schedule[row['tick']]=additions
    return schedule
