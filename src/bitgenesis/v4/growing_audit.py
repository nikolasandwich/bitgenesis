"""Independent reconstruction of growing local-unit trajectories."""
from hashlib import sha256
import json
from pathlib import Path
from random import Random
from .audit import reconstruct


def reconstruct_material(units, raw, width, height, directions, threshold, cost):
    """Dictionary-only reconstruction, resolving target buckets before changes."""
    state = [None if u is None or u['energy'] == 0 else dict(u) for u in units]
    dissolved = [i for i, u in enumerate(units) if u is not None and u['energy'] == 0]
    stock = list(raw)
    for i in dissolved:
        stock[i] += 1
    proposals = []
    buckets = {}
    offsets = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for source, u in enumerate(state):
        if u is None:
            continue
        dx, dy = offsets[directions[source]]
        target = ((source // width + dy) % height) * width + (source % width + dx) % width
        if u['energy'] < threshold:
            reason = 'energy'
        elif state[target] is not None:
            reason = 'occupied'
        elif not stock[target]:
            reason = 'raw_material'
        else:
            reason = 'candidate'
        proposal = dict(source=source, target=target, direction=directions[source], reason=reason)
        proposals.append(proposal)
        if reason == 'candidate':
            buckets.setdefault(target, []).append(proposal)
    spent = 0
    for target, choices in buckets.items():
        if len(choices) > 1:
            for p in choices:
                p['reason'] = 'collision'
            continue
        p = choices[0]
        template = units[p['source']]
        child = (template['energy'] - cost) // 2
        parent = template['energy'] - cost - child
        state[p['source']] = dict(material=template['material'], energy=parent)
        state[target] = dict(material=template['material'], energy=child)
        stock[target] -= 1
        spent += cost
        p.update(reason='formed', material=template['material'], parent_energy=parent,
                 child_energy=child, cost=cost)
    return state, stock, dict(dissolved=dissolved, proposals=proposals, spent=spent,
        material_before=sum(raw)+sum(u is not None for u in units),
        material_after=sum(stock)+sum(u is not None for u in state),
        energy_before=sum(u['energy'] for u in units if u is not None),
        energy_after=sum(u['energy'] for u in state if u is not None))


def audit(directory):
    root=Path(directory)
    def read(name):
        return json.loads((root/name).read_text(encoding='utf-8'))
    def require(ok,message):
        if not ok:
            raise ValueError(message)
    meta=read('metadata.json')
    require(meta['schema']=='v4-growing-run-1' and meta['rules']=='v4-growing-1'
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
    raw=[meta['initial_raw']]*len(units)
    initial=read('initial.json')
    require(initial==dict(tick=0,units=units,raw=raw,direction_rng=json.loads(json.dumps(direction.getstate())),rng_state=json.loads(json.dumps(rng.getstate())),
                         drive_rng=json.loads(json.dumps(drive.getstate()))),'initial state/random mismatch')
    start=sum(u['energy'] for u in units if u is not None)
    energy=start
    mass=sum(raw)+sum(u is not None for u in units)
    formations=dissolutions=construction_spent=0
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
            units,raw,material=reconstruct_material(intermediate,raw,meta['width'],meta['height'],
                                                    tickets,meta['threshold'],meta['construction_cost'])
            require(row['material']==material,'material transition mismatch')
            require(row['interaction_units']==intermediate and row['interaction_components']==groups,
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
            construction_spent+=material['spent']
            imported+=gain
            rejected+=refuse
            leakage+=leak
    require(tick==meta['steps'],'horizon mismatch')
    require(read('final.json')==dict(tick=tick,units=units,raw=raw,direction_rng=json.loads(json.dumps(direction.getstate())),drive_rng=json.loads(json.dumps(drive.getstate()))),'final state/RNG mismatch')
    summary=dict(steps=tick,units=sum(u is not None for u in units),initial_energy=start,final_energy=energy,
                 spent=spent,imported=imported,rejected_import=rejected,leakage=leakage,
                 construction_spent=construction_spent,formations=formations,dissolutions=dissolutions,
                 initial_material=mass,final_material=sum(raw)+sum(u is not None for u in units),final_raw=sum(raw))
    require(read('summary.json')==summary,'driven summary mismatch')
    return dict(scope='independent initialization/drive/direction RNG, input/leak, local interaction and material conversion',
                summary=summary,output_sha256=hashes,audit_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                local_audit_sha256=sha256(Path(__file__).with_name('audit.py').read_bytes()).hexdigest())


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
