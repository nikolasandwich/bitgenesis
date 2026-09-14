"""Local templating and dissolution; no group identity or group copy operation."""
from collections import Counter
from .local import Unit

RULES_VERSION='v4-material-1'


def convert(units,raw,width,height,directions,threshold=16,construction_cost=4):
    """Dissolve exhausted units, then resolve simultaneous neighbor proposals.

    A new unit incorporates one raw token and inherits its template's material.
    All collisions are rejected. Newly formed units do not act in this call.
    Direction tickets are supplied externally; no random draws occur here.
    """
    if any(type(v) is not int for v in (width,height,threshold,construction_cost)) or min(width,height)<3:
        raise ValueError('invalid geometry or integer cost')
    if construction_cost<0 or threshold<construction_cost+2:
        raise ValueError('threshold must allow two positive energy shares')
    if len(units)!=width*height or len(raw)!=len(units) or len(directions)!=len(units):
        raise ValueError('one unit/raw/direction entry per site required')
    if any(u is not None and type(u) is not Unit for u in units):
        raise ValueError('invalid unit')
    if any(type(n) is not int or n<0 for n in raw) or any(type(d) is not int or not 0<=d<4 for d in directions):
        raise ValueError('invalid raw material or direction ticket')
    current=list(units)
    resources=list(raw)
    dissolved=[]
    for site,u in enumerate(current):
        if u is not None and u.energy==0:
            current[site]=None
            resources[site]+=1
            dissolved.append(site)
    proposals=[]
    for site,u in enumerate(current):
        if u is None:
            continue
        x,y=site%width,site//width
        targets=(y*width+(x+1)%width,y*width+(x-1)%width,
                 ((y+1)%height)*width+x,((y-1)%height)*width+x)
        target=targets[directions[site]]
        reason=('energy' if u.energy<threshold else 'occupied' if current[target] is not None
                else 'raw_material' if resources[target]<1 else 'candidate')
        proposals.append(dict(source=site,target=target,direction=directions[site],reason=reason))
    contenders=Counter(p['target'] for p in proposals if p['reason']=='candidate')
    spent=0
    for p in proposals:
        if p['reason']!='candidate':
            continue
        if contenders[p['target']]!=1:
            p['reason']='collision'
            continue
        site,target=p['source'],p['target']
        parent=current[site]
        remaining=parent.energy-construction_cost
        child_energy=remaining//2
        current[site]=Unit(parent.material,remaining-child_energy)
        current[target]=Unit(parent.material,child_energy)
        resources[target]-=1
        spent+=construction_cost
        p.update(reason='formed',material=parent.material,parent_energy=remaining-child_energy,
                 child_energy=child_energy,cost=construction_cost)
    initial_mass=sum(raw)+sum(u is not None for u in units)
    final_mass=sum(resources)+sum(u is not None for u in current)
    initial_energy=sum(u.energy for u in units if u is not None)
    final_energy=sum(u.energy for u in current if u is not None)
    if initial_mass!=final_mass or initial_energy-spent!=final_energy:
        raise AssertionError('local material or energy ledger mismatch')
    return current,resources,dict(dissolved=dissolved,proposals=proposals,spent=spent,
        material_before=initial_mass,material_after=final_mass,
        energy_before=initial_energy,energy_after=final_energy)
