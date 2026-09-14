"""Material-retaining experimental damage, with energy exported explicitly."""
from .perturbation import remove

RULES_VERSION = 'v4-damage-1'


def damage(units, raw, sites):
    after, stock, record = remove(units, raw, sites)
    for unit in record['removed']:
        stock[unit['site']] += 1
    record.update(rules=RULES_VERSION, recycled_material=len(record['removed']),
                  exported_material=0, material_after=record['material_before'])
    return after, stock, record
