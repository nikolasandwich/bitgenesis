"""Independent origin, material-retaining damage and continued growing dynamics verification."""
from hashlib import sha256
import json
from pathlib import Path
from random import Random
from .audit import reconstruct
from .growing_audit import audit as origin_audit, reconstruct_material


def tuples(value):
    return tuple(map(tuples,value)) if isinstance(value,list) else value


def audit(directory, origin):
    root, source = Path(directory), Path(origin)
    def read(name):
        return json.loads((root/name).read_text(encoding='utf-8'))
    def require(ok,message):
        if not ok:
            raise ValueError(message)
    header=read('metadata.json')
    require(header['schema']=='v4-damage-branch-1' and header['rules']=='v4-growing-1'
            and header['status']=='complete','unsupported branch')
    names=('origin-audit.json','before.json','boundary.json','initial.json','steps.jsonl','final.json','summary.json')
    hashes={n:sha256((root/n).read_bytes()).hexdigest() for n in names}
    require(hashes==header['output_sha256'],'branch output hashes')
    checked=origin_audit(source)
    require(checked==read('origin-audit.json'),'origin audit mismatch')
    require(header['origin_metadata_sha256']==sha256((source/'metadata.json').read_bytes()).hexdigest()
            and header['origin_output_sha256']==checked['output_sha256'],'origin binding mismatch')
    source_meta=json.loads((source/'metadata.json').read_text(encoding='utf-8'))
    before=json.loads((source/'final.json').read_text(encoding='utf-8'))
    require(read('before.json')==before and header['start_tick']==before['tick'],'branch before mismatch')
    meta=header['config']
    keys=('width','height','drive_per_thousand','drive_amount','capacity','leak','bond_cost','exchange','threshold','construction_cost')
    require(set(meta)==set(keys),'branch config fields')
    require(all(meta[k]==source_meta[k] for k in keys if k!='threshold'),'branch config drift')
    require(type(meta['threshold']) is int and meta['threshold']>=meta['construction_cost']+2,'branch threshold')
    require(type(header['steps']) is int and 0<=header['steps']<=100000,'branch horizon')
    require(type(header['max_site_records']) is int and header['max_site_records']>=meta['width']*meta['height']*(header['steps']+1),'branch budget')
    sites=header['sites']
    require(isinstance(sites,list) and all(type(i) is int and 0<=i<len(before['units']) for i in sites),'removal sites')
    require(sites==sorted(set(sites)),'removal site order/duplicates')
    selected=set(sites)
    removed=[dict(site=i,**u) for i,u in enumerate(before['units']) if i in selected and u is not None]
    units=[None if i in selected else u for i,u in enumerate(before['units'])]
    raw=list(before['raw'])
    for unit in removed:
        raw[unit['site']]+=1
    boundary=dict(rules='v4-damage-1',sites=sites,removed=removed,
        exported_material=0,recycled_material=len(removed),exported_energy=sum(u['energy'] for u in removed),
        material_before=sum(before['raw'])+sum(u is not None for u in before['units']),
        material_after=sum(raw)+sum(u is not None for u in units),
        energy_before=sum(u['energy'] for u in before['units'] if u is not None),
        energy_after=sum(u['energy'] for u in units if u is not None))
    require(read('boundary.json')==boundary,'boundary material-retaining damage mismatch')
    require(read('initial.json')==dict(tick=before['tick'],units=units,raw=raw,
        drive_rng=before['drive_rng'],direction_rng=before['direction_rng']),'branch initial mismatch')
    drive,direction=Random(),Random()
    drive.setstate(tuples(before['drive_rng']))
    direction.setstate(tuples(before['direction_rng']))
    start=sum(u['energy'] for u in units if u is not None)
    energy=start
    mass=sum(raw)+sum(u is not None for u in units)
    formations=dissolutions=construction_spent=spent=imported=rejected=leakage=0
    tick=before['tick']
    with (root/'steps.jsonl').open() as stream:
        for tick,line in enumerate(stream,before['tick']+1):
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
    require(tick==before['tick']+header['steps'],'branch horizon mismatch')
    require(read('final.json')==dict(tick=tick,units=units,raw=raw,
        drive_rng=json.loads(json.dumps(drive.getstate())),direction_rng=json.loads(json.dumps(direction.getstate()))),'branch final mismatch')
    summary=dict(steps=header['steps'],initial_energy=start,final_energy=energy,
        initial_material=mass,final_material=sum(raw)+sum(u is not None for u in units),
        imported=imported,spent=spent,formations=formations,dissolutions=dissolutions,
        units=sum(u is not None for u in units),exported_energy=boundary['exported_energy'],exported_material=boundary['exported_material'],recycled_material=boundary['recycled_material'])
    require(read('summary.json')==summary,'branch summary mismatch')
    return dict(scope='independent origin reconstruction, material-retaining damage, continued RNG and growing dynamics',
        summary=summary,output_sha256=hashes,origin_output_sha256=checked['output_sha256'],
        audit_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        dependencies_sha256={name:sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                             for name in ('audit.py','growing_audit.py')})
