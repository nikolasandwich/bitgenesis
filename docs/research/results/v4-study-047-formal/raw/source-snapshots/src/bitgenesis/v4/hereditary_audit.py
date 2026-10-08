"""Independent reconstruction of growing local-unit trajectories."""
from hashlib import sha256
import json
from pathlib import Path
from random import Random
from .audit import reconstruct
from .growing_audit import reconstruct_material


def audit(directory):
    root=Path(directory)
    def read(name):
        return json.loads((root/name).read_text(encoding='utf-8'))
    def require(ok,message):
        if not ok:
            raise ValueError(message)
    meta=read('metadata.json')
    require(meta['schema']=='v4-hereditary-run-1' and meta['rules']=='v4-hereditary-growing-1'
            and meta['status']=='complete','unsupported driven run')
    hashes={n:sha256((root/n).read_bytes()).hexdigest() for n in ('initial.json','steps.jsonl','final.json','summary.json')}
    require(hashes==meta['output_sha256'],'output hashes')
    rng=Random(meta['seed'])
    units=[]
    for _ in range(meta['width']*meta['height']):
        units.append(dict(material=rng.randrange(4),energy=rng.randrange(meta['max_energy']+1))
                     if rng.randrange(1000)<meta['occupancy'] else None)
    drive=Random(int.from_bytes(sha256(f"v4-driven-1:{meta['seed']}:drive".encode('ascii')).digest(),'big'))
    direction=Random(int.from_bytes(sha256(f"v4-growing-1:{meta['seed']}:directions".encode('ascii')).digest(),'big'))
    program_rng=Random(int.from_bytes(sha256(f"v4-heredity-1:{meta['seed']}:program".encode('ascii')).digest(),'big'))
    mutation_rng=Random(int.from_bytes(sha256(f"v4-heredity-1:{meta['seed']}:mutation".encode('ascii')).digest(),'big'))
    require(meta['program_mode'] in ('random','constant'),'program mode')
    for u in units:
        program=[program_rng.randrange(4) for _ in range(4)]
        if u is not None:
            u['program']=program if meta['program_mode']=='random' else [u['material']]*4
    raw=[meta['initial_raw']]*len(units)
    initial=read('initial.json')
    require(initial==dict(tick=0,units=units,raw=raw,program_rng=json.loads(json.dumps(program_rng.getstate())),mutation_rng=json.loads(json.dumps(mutation_rng.getstate())),direction_rng=json.loads(json.dumps(direction.getstate())),rng_state=json.loads(json.dumps(rng.getstate())),
                         drive_rng=json.loads(json.dumps(drive.getstate()))),'initial state/random mismatch')
    start=sum(u['energy'] for u in units if u is not None)
    energy=start
    mass=sum(raw)+sum(u is not None for u in units)
    formations=dissolutions=construction_spent=copy_spent=mutations=0
    spent=imported=rejected=leakage=tick=0
    edges=set()
    groups=[]
    with (root/'steps.jsonl').open() as stream:
        for tick,line in enumerate(stream,1):
            row=json.loads(line)
            inputs=[]
            supplied=[]
            for site,u in enumerate(units):
                proposal=meta['drive_amount'] if drive.randrange(1000)<meta['drive_per_thousand'] else 0
                new=0 if u is None else min(meta['capacity'],u['energy']+proposal)
                accepted=0 if u is None else new-u['energy']
                loss=min(meta['leak'],new)
                supplied.append(None if u is None else dict(material=u['material'],energy=new-loss))
                inputs.append(dict(site=site,proposed=proposal,accepted=accepted,rejected=proposal-accepted,leakage=loss))
            intermediate,edges,transfers,groups,cost=reconstruct(supplied,meta['width'],meta['height'],meta['bond_cost'],meta['exchange'])
            gain=sum(i['accepted'] for i in inputs)
            refuse=sum(i['rejected'] for i in inputs)
            leak=sum(i['leakage'] for i in inputs)
            driven=row['driven']
            require(driven['inputs']==inputs,'drive input/leak mismatch')
            normalized=[tuple(sorted(e)) for e in driven['interaction']['bonds']]
            require(len(normalized)==len(edges) and set(normalized)==edges,'driven bonds mismatch')
            require(sorted(driven['interaction']['transfers'],key=lambda r:(r['donor'],r['recipient']))==
                    sorted(transfers,key=lambda r:(r['donor'],r['recipient'])),'driven transfer mismatch')
            require(driven['interaction']['spent']==cost and driven['energy_before']==energy,'interaction cost/before mismatch')
            middle_energy=energy+gain-leak-cost
            require(driven['energy_after']==middle_energy and driven['imported']==gain
                    and driven['rejected_import']==refuse and driven['leakage']==leak
                    and driven['spent']==cost+leak,'driven ledger mismatch')
            tickets=[direction.randrange(4) for _ in units]
            require(row['directions']==tickets,'direction RNG mismatch')
            mutation_tickets=[[mutation_rng.randrange(1000),mutation_rng.randrange(4),mutation_rng.randrange(1,4)] for _ in units]
            require(row['mutation_tickets']==mutation_tickets,'mutation RNG tickets')
            original=units
            inherited_intermediate=[None if u is None else dict(**u,program=original[i]['program']) for i,u in enumerate(intermediate)]
            units,raw,material=reconstruct_material(intermediate,raw,meta['width'],meta['height'],
                tickets,meta['threshold'],meta['construction_cost']+meta['copy_cost'])
            programs={i:list(u['program']) for i,u in enumerate(original) if u is not None}
            births=0
            for p in material['proposals']:
                if p['reason']!='formed':
                    continue
                source,target=p['source'],p['target']
                parent=original[source]
                child=list(parent['program'])
                chance,entry,offset=mutation_tickets[source]
                changed=chance<meta['mutation_per_thousand']
                if changed:
                    child[entry]=(child[entry]+offset)%4
                expressed=parent['program'][tickets[source]]
                programs[target]=child
                units[target]['material']=expressed
                p.update(parent_material=parent['material'],material=expressed,parent_program=parent['program'],
                    child_program=child,mutation_ticket=mutation_tickets[source],mutated=changed,
                    construction_cost=meta['construction_cost'],copy_cost=meta['copy_cost'])
                births+=1
            units=[None if u is None else dict(**u,program=programs[i]) for i,u in enumerate(units)]
            material.update(construction_spent=births*meta['construction_cost'],copy_spent=births*meta['copy_cost'])
            require(row['material']==material,'material transition mismatch')
            require(row['interaction_units']==inherited_intermediate and row['interaction_components']==groups,
                    'intermediate observation mismatch')
            total_cost=cost+leak+material['spent']
            require(row['energy_before']==energy,'growing energy before mismatch')
            energy+=gain-total_cost
            require(row['tick']==tick and row['units']==units and row['raw']==raw
                    and row['energy']==row['energy_after']==energy and row['imported']==gain
                    and row['rejected_import']==refuse and row['spent']==total_cost
                    and row['material_before']==row['material_after']==mass,'growing state ledger mismatch')
            spent+=total_cost
            formations+=sum(p['reason']=='formed' for p in material['proposals'])
            dissolutions+=len(material['dissolved'])
            construction_spent+=material['construction_spent']
            copy_spent+=material['copy_spent']
            mutations+=sum(p.get('mutated',False) for p in material['proposals'])
            imported+=gain
            rejected+=refuse
            leakage+=leak
    require(tick==meta['steps'],'horizon mismatch')
    require(read('final.json')==dict(tick=tick,units=units,raw=raw,mutation_rng=json.loads(json.dumps(mutation_rng.getstate())),direction_rng=json.loads(json.dumps(direction.getstate())),drive_rng=json.loads(json.dumps(drive.getstate()))),'final state/RNG mismatch')
    summary=dict(steps=tick,units=sum(u is not None for u in units),initial_energy=start,final_energy=energy,
                 spent=spent,imported=imported,rejected_import=rejected,leakage=leakage,
                 construction_spent=construction_spent,copy_spent=copy_spent,mutations=mutations,formations=formations,dissolutions=dissolutions,
                 initial_material=mass,final_material=sum(raw)+sum(u is not None for u in units),final_raw=sum(raw))
    require(read('summary.json')==summary,'driven summary mismatch')
    return dict(scope='independent initialization/program/drive/direction/mutation RNG, physical dynamics and hereditary expression',
                summary=summary,output_sha256=hashes,audit_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                dependencies_sha256={name:sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('audit.py','growing_audit.py')})


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
