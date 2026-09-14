"""Independent boundary checks plus same-engine continuation replay from an origin."""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from .boundary_audit import reconstruct
from .interventions import boundary
from .runner import encoded,state


def verify(directory,origin):
    root=Path(directory)
    def read(name):
        return json.loads((root/name).read_text(encoding='utf-8'))
    def require(ok,message):
        if not ok:
            raise ValueError(message)
    meta=read('metadata.json')
    require(meta['schema']=='v3-branch-1' and meta['status']=='complete'
            and meta['rules']=='v3-world-1' and meta['intervention_rules']=='v3-boundary-1','unsupported branch')
    require(meta['config']==asdict(origin.config) and meta['seed']==origin.seed
            and meta['start_tick']==origin.tick,'origin configuration mismatch')
    require(encoded(read('initial.json'))==encoded(state(origin)),'common origin mismatch')
    require(type(meta['steps']) is int and 1<=meta['steps']<=100000,'invalid horizon')
    require(meta['completed_steps']==meta['steps'],'incomplete branch')
    hashes={n:sha256((root/n).read_bytes()).hexdigest() for n in
            ('initial.json','steps.jsonl','events.jsonl','final.json','summary.json')}
    require(meta['output_sha256']==hashes,'branch hash mismatch')
    schedule={int(t):items for t,items in meta['deposits'].items()}
    require(all(origin.tick<=t<origin.tick+meta['steps'] for t in schedule),'schedule horizon')
    world=deepcopy(origin)
    world.events.clear()
    counts=dict(actor_records=0,exported_energy=0,imported_energy=0,rejected_import=0)
    with (root/'steps.jsonl').open(encoding='utf-8') as rows, (root/'events.jsonl').open(encoding='utf-8') as events:
        for index in range(meta['steps']):
            line=next(rows,None)
            require(line is not None,'missing branch step')
            saved=json.loads(line)
            target=meta['remove_founder'] if index==0 else None
            additions=schedule.get(world.tick,())
            # Validate requested operation on a copy before the independent routine.
            validation=deepcopy(world)
            boundary(validation,remove_founder=target,b_additions=additions)
            expected_state,expected_record=reconstruct(state(world),world.config.capacity,target,additions)
            require(saved['boundary']==expected_record,'independent boundary record mismatch')
            actual=boundary(world,remove_founder=target,b_additions=additions)
            require(actual==expected_record and encoded(state(world))==encoded(expected_state),'boundary state mismatch')
            step=world.step()
            require(encoded(saved['step'])==encoded(step),'continuation replay mismatch')
            for event in world.events:
                line=next(events,None)
                require(line is not None and encoded(json.loads(line))==encoded(event),'branch event mismatch')
            world.events.clear()
            counts['actor_records']+=len(step['actors'])
            for key in ('exported_energy','imported_energy','rejected_import'):
                counts[key]+=expected_record[key]
        require(next(rows,None) is None and next(events,None) is None,'extra branch records')
    require(encoded(state(world))==encoded(read('final.json')),'branch final state mismatch')
    summary=dict(**counts,population=len(world.organisms),total_energy=world.total_energy(),
                 branch_births=sum(o.birth_tick>origin.tick for o in world.lineage.values()))
    require(read('summary.json')==summary,'branch summary mismatch')
    return dict(scope='independent boundary reconstruction plus same-engine world replay; '
                'origin provenance and independent intervened world history not certified',
                summary=summary,output_sha256=hashes,
                verifier_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                boundary_audit_sha256=sha256(Path(__file__).with_name('boundary_audit.py').read_bytes()).hexdigest())
