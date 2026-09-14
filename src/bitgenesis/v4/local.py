"""Synchronous local bonds and conservative transport without group identities."""
from dataclasses import dataclass

RULES_VERSION='v4-local-1'


@dataclass(frozen=True)
class Unit:
    material: int
    energy: int

    def __post_init__(self):
        if type(self.material) is not int or not 0<=self.material<=3:
            raise ValueError('material must be in0..3')
        if type(self.energy) is not int or self.energy<0:
            raise ValueError('nonnegative integer energy required')


def interact(units,width,height,bond_cost=1,exchange=True):
    """Matching neighboring materials propose bonds using only local state.

    Each endpoint reserves the cost of all its matching neighbors before any
    proposal is accepted. Both endpoints must afford their local reservation.
    Only realized bonds are charged. Post-charge diffusion is simultaneous.
    """
    if any(type(v) is not int for v in (width,height,bond_cost)) or min(width,height)<3 or bond_cost<0:
        raise ValueError('invalid geometry or cost')
    if len(units)!=width*height or any(u is not None and type(u) is not Unit for u in units):
        raise ValueError('one unit or empty value per site required')
    if type(exchange) is not bool:
        raise ValueError('exchange switch must be boolean')
    candidates=[]
    degrees=[0]*len(units)
    for site,unit in enumerate(units):
        if unit is None:
            continue
        x,y=site%width,site//width
        for neighbor in (y*width+(x+1)%width,((y+1)%height)*width+x):
            other=units[neighbor]
            if other is not None and other.material==unit.material:
                candidates.append((site,neighbor))
                degrees[site]+=1
                degrees[neighbor]+=1
    bonds=[(a,b) for a,b in candidates if units[a].energy>=degrees[a]*bond_cost
           and units[b].energy>=degrees[b]*bond_cost]
    energy=[u.energy if u is not None else 0 for u in units]
    for a,b in bonds:
        energy[a]-=bond_cost
        energy[b]-=bond_cost
    delta=[0]*len(units)
    transfers=[]
    if exchange:
        for a,b in bonds:
            donor,recipient=(a,b) if energy[a]>=energy[b] else (b,a)
            amount=(energy[donor]-energy[recipient])//8
            delta[donor]-=amount
            delta[recipient]+=amount
            if amount:
                transfers.append(dict(donor=donor,recipient=recipient,amount=amount))
    result=[None if u is None else Unit(u.material,energy[i]+delta[i]) for i,u in enumerate(units)]
    spent=2*bond_cost*len(bonds)
    if sum(u.energy for u in units if u is not None)-spent!=sum(u.energy for u in result if u is not None):
        raise AssertionError('local energy ledger mismatch')
    return result,dict(bonds=[list(edge) for edge in bonds],transfers=transfers,spent=spent)


def components(units,bonds):
    """Observe connected sets from supplied bonds; labels never drive dynamics."""
    remaining={i for i,u in enumerate(units) if u is not None}
    adjacent={i:set() for i in remaining}
    for a,b in bonds:
        if a not in remaining or b not in remaining or a==b:
            raise ValueError('invalid observed bond')
        adjacent[a].add(b)
        adjacent[b].add(a)
    groups=[]
    while remaining:
        reached={min(remaining)}
        pending=list(reached)
        while pending:
            site=pending.pop()
            for neighbor in adjacent[site]-reached:
                reached.add(neighbor)
                pending.append(neighbor)
        remaining-=reached
        groups.append(sorted(reached))
    return groups
