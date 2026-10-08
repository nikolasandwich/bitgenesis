"""Externally driven local units, preserving the closed interaction kernel."""
from .local import Unit,interact

RULES_VERSION='v4-driven-1'


def step(units,width,height,proposals,capacity=64,leak=1,bond_cost=1,exchange=True):
    """Boundary input -> per-unit leakage -> existing local interaction.

    Proposals include empty sites. Unaccepted input stays outside the system.
    Existing energy above capacity is rejected as an invalid state, not erased.
    """
    if any(type(v) is not int or v<0 for v in (capacity,leak)):
        raise ValueError('nonnegative capacity and leak required')
    if len(proposals)!=len(units) or any(type(p) is not int or p<0 for p in proposals):
        raise ValueError('one nonnegative input proposal per site required')
    if any(u is not None and (type(u) is not Unit or u.energy>capacity) for u in units):
        raise ValueError('invalid unit or energy above capacity')
    supplied=[]
    inputs=[]
    for site,(u,proposal) in enumerate(zip(units,proposals)):
        accepted=0 if u is None else min(proposal,capacity-u.energy)
        dissipated=0 if u is None else min(leak,u.energy+accepted)
        supplied.append(None if u is None else Unit(u.material,u.energy+accepted-dissipated))
        inputs.append(dict(site=site,proposed=proposal,accepted=accepted,rejected=proposal-accepted,
                           leakage=dissipated))
    result,interaction=interact(supplied,width,height,bond_cost,exchange)
    # At most four incoming edges each transfer <=(capacity-energy)/8,
    # so the existing transport rule preserves this capacity without clipping.
    if any(u is not None and u.energy>capacity for u in result):
        raise AssertionError('transport exceeded capacity')
    before=sum(u.energy for u in units if u is not None)
    imported=sum(i['accepted'] for i in inputs)
    leakage=sum(i['leakage'] for i in inputs)
    spent=leakage+interaction['spent']
    after=sum(u.energy for u in result if u is not None)
    if after!=before+imported-spent:
        raise AssertionError('driven local energy mismatch')
    return result,dict(inputs=inputs,interaction=interaction,
                        energy_before=before,imported=imported,
                        rejected_import=sum(i['rejected'] for i in inputs),leakage=leakage,
                        spent=spent,energy_after=after)
