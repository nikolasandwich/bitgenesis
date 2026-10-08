"""Experimental removal boundary; exported units are not recycled in situ."""
from dataclasses import asdict
from .local import Unit

RULES_VERSION = 'v4-removal-1'


def remove(units, raw, sites):
    """Return copied state and an explicit material/energy export ledger."""
    selected = list(sites)
    if len(raw) != len(units) or any(u is not None and type(u) is not Unit for u in units):
        raise ValueError('invalid unit/raw arrays')
    if any(type(r) is not int or r < 0 for r in raw):
        raise ValueError('invalid raw material')
    if any(type(i) is not int or not 0 <= i < len(units) for i in selected):
        raise ValueError('invalid removal site')
    if len(set(selected)) != len(selected):
        raise ValueError('duplicate removal site')
    selected.sort()
    after = list(units)
    removed = []
    for i in selected:
        if after[i] is not None:
            removed.append(dict(site=i, **asdict(after[i])))
            after[i] = None
    exported_energy = sum(u['energy'] for u in removed)
    return after, list(raw), dict(
        rules=RULES_VERSION, sites=selected, removed=removed,
        exported_material=len(removed), exported_energy=exported_energy,
        material_before=sum(raw)+sum(u is not None for u in units),
        material_after=sum(raw)+sum(u is not None for u in after),
        energy_before=sum(u.energy for u in units if u is not None),
        energy_after=sum(u.energy for u in after if u is not None))
