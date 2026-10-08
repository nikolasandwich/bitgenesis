"""Independent drive RNG, input/leak boundary and local interaction replay."""
from hashlib import sha256
import json
from pathlib import Path
from random import Random
from .audit import reconstruct


def audit(directory):
    root=Path(directory)
    def read(name):
        return json.loads((root/name).read_text(encoding='utf-8'))
    def require(ok,message):
        if not ok:
            raise ValueError(message)
    meta=read('metadata.json')
    require(meta['schema']=='v4-driven-run-1' and meta['rules']=='v4-driven-1'
            and meta['status']=='complete','unsupported driven run')
    hashes={n:sha256((root/n).read_bytes()).hexdigest() for n in ('initial.json','steps.jsonl','final.json','summary.json')}
    require(hashes==meta['output_sha256'],'output hashes')
    rng=Random(meta['seed'])
    units=[]
    for _ in range(meta['width']*meta['height']):
        units.append(dict(material=rng.randrange(4),energy=rng.randrange(meta['max_energy']+1))
                     if rng.randrange(1000)<meta['occupancy'] else None)
    drive=Random(int.from_bytes(sha256(f"v4-driven-1:{meta['seed']}:drive".encode('ascii')).digest(),'big'))
    initial=read('initial.json')
    require(initial==dict(tick=0,units=units,rng_state=json.loads(json.dumps(rng.getstate())),
                         drive_rng=json.loads(json.dumps(drive.getstate()))),'initial state/random mismatch')
    start=sum(u['energy'] for u in units if u is not None)
    energy=start
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
            units,edges,transfers,groups,cost=reconstruct(supplied,meta['width'],meta['height'],meta['bond_cost'],meta['exchange'])
            gain=sum(i['accepted'] for i in inputs)
            refuse=sum(i['rejected'] for i in inputs)
            leak=sum(i['leakage'] for i in inputs)
            require(row['inputs']==inputs,'drive input/leak mismatch')
            normalized=[tuple(sorted(e)) for e in row['interaction']['bonds']]
            require(len(normalized)==len(edges) and set(normalized)==edges,'driven bonds mismatch')
            require(sorted(row['interaction']['transfers'],key=lambda r:(r['donor'],r['recipient']))==
                    sorted(transfers,key=lambda r:(r['donor'],r['recipient'])),'driven transfer mismatch')
            require(row['interaction']['spent']==cost and row['energy_before']==energy,'interaction cost/before mismatch')
            energy+=gain-leak-cost
            require(row['tick']==tick and row['units']==units and row['components']==groups
                    and row['energy']==row['energy_after']==energy and row['imported']==gain
                    and row['rejected_import']==refuse and row['leakage']==leak and row['spent']==cost+leak,'driven state ledger mismatch')
            spent+=cost+leak
            imported+=gain
            rejected+=refuse
            leakage+=leak
    require(tick==meta['steps'],'horizon mismatch')
    require(read('final.json')==dict(tick=tick,units=units,drive_rng=json.loads(json.dumps(drive.getstate()))),'final state/RNG mismatch')
    summary=dict(steps=tick,units=sum(u is not None for u in units),initial_energy=start,final_energy=energy,
                 spent=spent,imported=imported,rejected_import=rejected,leakage=leakage,
                 last_transition_bonds=len(edges) if tick else None,last_transition_components=len(groups) if tick else None)
    require(read('summary.json')==summary,'driven summary mismatch')
    return dict(scope='independent initialization/drive RNG, input/leak, local bonds/transport/components',
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
