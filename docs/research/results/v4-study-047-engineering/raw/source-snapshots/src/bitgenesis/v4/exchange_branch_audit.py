"""Dictionary physics and recursive ancestor-set audit, independent of observers."""
from hashlib import sha256
import json
from pathlib import Path
from .audit import reconstruct
from .growing_audit import reconstruct_material
from .structure_audit import reconstruct as partition
from .hereditary_audit import audit as source_audit


def continuity(series, parents):
    """Set intersections and recursive parent chains, without production follow."""
    initial = [set(g) for g in series[0]]
    founders = set().union(*initial) if initial else set()
    def ancestor(identity):
        if identity in founders:
            return identity
        parent = parents[identity]
        if parent is None or not 0 <= parent < identity:
            raise ValueError('ancestor chain')
        return ancestor(parent)
    roots = {i:ancestor(i) for i in range(len(parents))}
    results = []
    states = ('extinct','fragmented','mixed','closed_singleton','closed_multi')
    for index, origin in enumerate(initial):
        counts, outside_counts = dict.fromkeys(states,0),dict.fromkeys(states,0)
        first_break = first_replacement = None
        for tick in range(1,len(series)):
            groups = [set(g) for g in series[tick]]
            living = set().union(*groups) if groups else set()
            descendants = {i for i in living if roots[i] in origin}
            targets = [g for g in groups if g & descendants]
            outsiders = sum(len(g-descendants) for g in targets)
            state = 'extinct' if not descendants else 'fragmented' if len(targets)>1 else 'mixed' if outsiders else 'closed_singleton' if len(descendants)==1 else 'closed_multi'
            survivors = len(descendants & origin)
            replaced = bool(descendants) and survivors == 0
            counts[state] += 1
            outside_counts[state] += outsiders
            if state != 'closed_multi' and first_break is None:
                first_break = tick
            if replaced and first_replacement is None:
                first_replacement = tick
        continuous = len(origin)>=2 and first_break is None
        results.append(dict(component=index,anchor_members=sorted(origin),anchor_size=len(origin),
            anchor_world_units=len(founders),whole_world_anchor=len(origin)==len(founders),
            state_steps=counts,outsider_unit_steps=outside_counts,first_break_tick=first_break,
            first_complete_replacement_tick=first_replacement,
            endpoint=dict(state=state,descendants=len(descendants),original_survivors=survivors,
                new_descendants=len(descendants)-survivors,represented_anchor_members=len({roots[i] for i in descendants}),
                destination_components=len(targets),outsiders=outsiders),continuous_closed_multi=continuous,
            complete_replacement=replaced,endpoint_closed_after_break=state=='closed_multi' and first_break is not None,
            primary=continuous and replaced))
    return results


def physical_step(original, raw, config, tape, exchange):
    supplied, inputs = [], []
    for site,u in enumerate(original):
        proposed = tape['driven']['inputs'][site]['proposed']
        accepted = min(proposed,config['capacity']-u['energy']) if u else 0
        loss = min(config['leak'],u['energy']+accepted) if u else 0
        supplied.append(dict(material=u['material'],energy=u['energy']+accepted-loss) if u else None)
        inputs.append(dict(site=site,proposed=proposed,accepted=accepted,rejected=proposed-accepted,leakage=loss))
    width,height = config['width'],config['height']
    middle,edges,transfers,groups,cost = reconstruct(supplied,width,height,config['bond_cost'],exchange)
    # Restore the documented east/south serialization order after independent edge reconstruction.
    bonds=[]
    for a in range(len(original)):
        for b in ((a//width)*width+(a%width+1)%width,((a//width+1)%height)*width+a%width):
            if tuple(sorted((a,b))) in edges:
                bonds.append([a,b])
    transfer_map={(r['donor'],r['recipient']):r for r in transfers}
    ordered=[]
    for a,b in bonds:
        item=transfer_map.get((a,b),transfer_map.get((b,a)))
        if item is not None:
            ordered.append(item)
    inherited=[None if u is None else dict(**u,program=original[i]['program']) for i,u in enumerate(middle)]
    units,stock,material = reconstruct_material(middle,raw,width,height,tape['directions'],config['threshold'],config['construction_cost']+config['copy_cost'])
    programs={i:u['program'] for i,u in enumerate(original) if u}
    births=0
    for p in material['proposals']:
        if p['reason']!='formed':
            continue
        source,target=p['source'],p['target']
        parent=original[source]
        child=list(parent['program'])
        chance,entry,offset=tape['mutation_tickets'][source]
        mutated=chance<config['mutation_per_thousand']
        if mutated:
            child[entry]=(child[entry]+offset)%4
        expressed=parent['program'][tape['directions'][source]]
        programs[target]=child
        units[target]['material']=expressed
        p.update(parent_material=parent['material'],material=expressed,parent_program=parent['program'],child_program=child,
            mutation_ticket=tape['mutation_tickets'][source],mutated=mutated,construction_cost=config['construction_cost'],copy_cost=config['copy_cost'])
        births+=1
    units=[None if u is None else dict(**u,program=programs[i]) for i,u in enumerate(units)]
    material.update(construction_spent=births*config['construction_cost'],copy_spent=births*config['copy_cost'])
    before=sum(u['energy'] for u in original if u)
    gain=sum(i['accepted'] for i in inputs)
    rejected=sum(i['rejected'] for i in inputs)
    leak=sum(i['leakage'] for i in inputs)
    driven=dict(inputs=inputs,interaction=dict(bonds=bonds,transfers=ordered,spent=cost),energy_before=before,
        imported=gain,rejected_import=rejected,leakage=leak,spent=cost+leak,energy_after=before+gain-cost-leak)
    return dict(tick=tape['tick'],units=units,raw=stock,energy=material['energy_after'],directions=tape['directions'],
        mutation_tickets=tape['mutation_tickets'],driven=driven,material=material,interaction_units=inherited,
        interaction_components=groups,energy_before=before,energy_after=material['energy_after'],imported=gain,
        rejected_import=rejected,spent=cost+leak+material['spent'],material_before=material['material_before'],material_after=material['material_after'])


def audit(output,source):
    root,source=Path(output),Path(source)
    def read(path):
        return json.loads(path.read_text())
    def hashes(path):
        return {p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(path.iterdir()) if p.is_file()}
    def require(ok,message):
        if not ok:
            raise ValueError(message)
    original_source,original_output=hashes(source),hashes(root)
    meta=read(root/'metadata.json')
    require(meta['schema']=='v4-exchange-branch-1' and meta['status']=='complete','branch status/schema')
    require(type(meta['exchange']) is bool and type(meta['anchor']) is int and meta['anchor']>=0 and type(meta['horizon']) is int and meta['horizon']>0,'branch configuration')
    require(meta['source_sha256']==meta['source_sha256_after']==original_source,'source hashes')
    require(meta['source_audit']==source_audit(source),'upstream audit')
    expected_files=('initial.json','steps.jsonl','final.json','continuity.json','summary.json')
    require(meta['output_sha256']=={n:original_output[n] for n in expected_files},'output hashes')
    require(meta['code_sha256']=={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))},'code hashes')
    config=read(source/'metadata.json')
    require(config['exchange'] is True,'source exchange')
    history=[json.loads(line) for line in (source/'steps.jsonl').read_text().splitlines()]
    anchor,horizon=meta['anchor'],meta['horizon']
    require(anchor+horizon<=len(history),'source horizon')
    origin=history[anchor-1] if anchor else read(source/'initial.json')
    units,raw=origin['units'],origin['raw']
    ids=[]
    parents=[]
    deaths=[]
    for u in units:
        ids.append(len(parents) if u else None)
        if u:
            parents.append(None)
            deaths.append(None)
    observed=partition(units,ids,config['width'],config['height'],'final')
    require(read(root/'initial.json')==dict(tick=0,source_tick=anchor,units=units,raw=raw,site_ids=ids,observation=observed),'initial state/identities')
    series={0:observed['components']['material']}
    rows=[json.loads(line) for line in (root/'steps.jsonl').read_text().splitlines()]
    require(len(rows)==horizon,'branch horizon')
    for tick,(row,tape) in enumerate(zip(rows,history[anchor:anchor+horizon]),1):
        expected=physical_step(units,raw,config,tape,meta['exchange'])
        require(row['physical']==expected,'physical record')
        if meta['exchange']:
            require(expected==tape,'baseline physical record')
        old_ids=list(ids)
        for site in expected['material']['dissolved']:
            deaths[ids[site]]=tick
            ids[site]=None
        for p in expected['material']['proposals']:
            if p['reason']=='formed':
                require(old_ids[p['source']] is not None,'birth parent')
                ids[p['target']]=len(parents)
                parents.append(old_ids[p['source']])
                deaths.append(None)
        units,raw=expected['units'],expected['raw']
        observed=partition(units,ids,config['width'],config['height'],'final')
        require(row==dict(tick=tick,source_tick=anchor+tick,physical=expected,site_ids=ids,observation=observed),'identity/observation record')
        series[tick]=observed['components']['material']
    require(read(root/'final.json')==dict(tick=horizon,source_tick=anchor+horizon,units=units,raw=raw,site_ids=ids,parents=parents,death_ticks=deaths),'final identities/ancestry/deaths')
    records=continuity(series,parents)
    require(read(root/'continuity.json')==records,'continuity records')
    eligible=[r for r in records if r['anchor_size']>1 and not r['whole_world_anchor']]
    n=len(eligible)
    c=sum(r['continuous_closed_multi'] for r in eligible)
    r=sum(r['primary'] for r in eligible)
    summary=dict(eligible_components=n,continuous_closed_multi=c,continuous_fraction=c/n if n else None,
        continuous_replacement=r,continuous_replacement_fraction=r/n if n else None)
    require(read(root/'summary.json')==summary,'summary')
    require(hashes(source)==original_source and hashes(root)==original_output,'audit inputs changed')
    return dict(scope='independent physical/hereditary records, birth ancestry, final material partitions and continuity',
        ticks=horizon,components=len(records),summary=summary,input_sha256=original_source,
        output_sha256=meta['output_sha256'],auditor_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
