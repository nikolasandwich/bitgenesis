"""Independent fixed-unit reconstruction using four-neighbor sets and union-find."""
from hashlib import sha256
import json
from pathlib import Path
from random import Random


def reconstruct(units,width,height,cost,exchange):
    neighbors={}
    for i,u in enumerate(units):
        if u is None:
            continue
        x,y=i%width,i//width
        adjacent={y*width+(x-1)%width,y*width+(x+1)%width,
                  ((y-1)%height)*width+x,((y+1)%height)*width+x}
        neighbors[i]={j for j in adjacent if units[j] is not None and units[j]['material']==u['material']}
    edges={(min(i,j),max(i,j)) for i,adjacent in neighbors.items() for j in adjacent
           if units[i]['energy']>=cost*len(adjacent) and units[j]['energy']>=cost*len(neighbors[j])}
    energy={i:u['energy']-cost*sum(i in edge for edge in edges) for i,u in enumerate(units) if u is not None}
    after=dict(energy)
    transfers=[]
    for a,b in sorted(edges):
        donor,recipient=(a,b) if energy[a]>=energy[b] else (b,a)
        amount=(energy[donor]-energy[recipient])//8 if exchange else 0
        if amount:
            transfers.append(dict(donor=donor,recipient=recipient,amount=amount))
            after[donor]-=amount
            after[recipient]+=amount
    parents={i:i for i in neighbors}
    def find(i):
        while parents[i]!=i:
            i=parents[i]
        return i
    for a,b in edges:
        parents[find(b)]=find(a)
    groups={}
    for i in parents:
        groups.setdefault(find(i),[]).append(i)
    components=sorted((sorted(g) for g in groups.values()),key=lambda g:g[0])
    result=[None if u is None else dict(material=u['material'],energy=after[i]) for i,u in enumerate(units)]
    return result,edges,transfers,components,2*cost*len(edges)


def audit(directory):
    root=Path(directory)
    def read(name):
        return json.loads((root/name).read_text(encoding='utf-8'))
    def require(ok,message):
        if not ok:
            raise ValueError(message)
    meta=read('metadata.json')
    require(meta['schema']=='v4-run-1' and meta['rules']=='v4-local-1' and meta['status']=='complete','unsupported run')
    hashes={name:sha256((root/name).read_bytes()).hexdigest() for name in ('initial.json','steps.jsonl','final.json','summary.json')}
    require(meta['output_sha256']==hashes,'output hash mismatch')
    rng=Random(meta['seed'])
    units=[]
    for _ in range(meta['width']*meta['height']):
        if rng.randrange(1000)<meta['occupancy']:
            units.append(dict(material=rng.randrange(4),energy=rng.randrange(meta['max_energy']+1)))
        else:
            units.append(None)
    initial=read('initial.json')
    require(initial['tick']==0 and initial['units']==units,'initialization mismatch')
    require(json.loads(json.dumps(rng.getstate()))==initial['rng_state'],'initial RNG mismatch')
    initial_energy=sum(u['energy'] for u in units if u is not None)
    spent=tick=0
    edges=set()
    groups=[]
    first_zero=None
    with (root/'steps.jsonl').open() as stream:
        for tick,line in enumerate(stream,1):
            row=json.loads(line)
            units,edges,transfers,groups,cost=reconstruct(units,meta['width'],meta['height'],meta['bond_cost'],meta['exchange'])
            normalized=[tuple(sorted(edge)) for edge in row['bonds']]
            require(len(normalized)==len(edges) and set(normalized)==edges,'bond mismatch')
            require(sorted(row['transfers'],key=lambda r:(r['donor'],r['recipient']))==
                    sorted(transfers,key=lambda r:(r['donor'],r['recipient'])),'transfer mismatch')
            spent+=cost
            require(row['tick']==tick and row['units']==units and row['components']==groups
                    and row['spent']==cost and row['energy']==initial_energy-spent,'state/component ledger mismatch')
            if not edges and first_zero is None:
                first_zero=tick
    require(tick==meta['steps'],'horizon mismatch')
    require(read('final.json')==dict(tick=tick,units=units),'final state mismatch')
    summary=dict(steps=tick,units=sum(u is not None for u in units),initial_energy=initial_energy,
                 final_energy=initial_energy-spent,spent=spent,last_transition_bonds=len(edges) if tick else None,
                 last_transition_components=len(groups) if tick else None)
    require(read('summary.json')==summary,'summary mismatch')
    return dict(scope='independent initialization, bonds, costs, transport and components',
                summary=summary,first_zero_bond_transition=first_zero,output_sha256=hashes,
                audit_sha256=sha256(Path(__file__).read_bytes()).hexdigest())


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
    print(json.dumps(result,indent=2))
