"""Independent reconstruction of serialized experimental boundary changes."""
from copy import deepcopy


def reconstruct(before, capacity, remove_founder, additions):
    after=deepcopy(before)
    living=[o for o in after['lineage'] if o['death_tick'] is None]
    energy=sum(after['food'])+sum(after['substrate_b'])+sum(o['energy'] for o in living)
    removed=[]
    for o in living:
        if remove_founder is not None and o['founder']==remove_founder:
            removed.append(dict(id=o['id'],founder=o['founder'],x=o['x'],y=o['y'],exported_energy=o['energy']))
            o['energy']=0
            o['death_tick']=before['tick']
    deposits=[]
    for site,proposed in additions:
        old=after['substrate_b'][site]
        new=min(capacity,old+proposed)
        after['substrate_b'][site]=new
        deposits.append(dict(site=site,before=old,proposed=proposed,accepted=new-old,
                             rejected=old+proposed-new,after=new))
    exported=sum(o['exported_energy'] for o in removed)
    imported=sum(d['accepted'] for d in deposits)
    record=dict(event='experimental_boundary',rules='v3-boundary-1',tick=before['tick'],
                remove_founder=remove_founder,removed=removed,b_deposits=deposits,
                energy_before=energy,exported_energy=exported,imported_energy=imported,
                rejected_import=sum(d['rejected'] for d in deposits),energy_after=energy-exported+imported)
    return after,record
