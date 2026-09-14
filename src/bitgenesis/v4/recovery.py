"""Observer-only occupancy and material-pattern comparison, not ancestry."""
from fractions import Fraction
from .local import Unit


def observe(reference, current, sites):
    selected = list(sites)
    if len(reference) != len(current):
        raise ValueError('state size mismatch')
    if any(u is not None and type(u) is not Unit for state in (reference, current) for u in state):
        raise ValueError('invalid unit')
    if any(type(i) is not int or not 0 <= i < len(reference) for i in selected):
        raise ValueError('invalid observation site')
    if len(set(selected)) != len(selected):
        raise ValueError('duplicate observation site')
    original = [i for i in selected if reference[i] is not None]
    occupied = sum(current[i] is not None for i in selected)
    refilled = sum(current[i] is not None for i in original)
    matched = sum(current[i] is not None and current[i].material == reference[i].material for i in original)
    return dict(sites=len(selected), reference_occupied=len(original), occupied=occupied,
                refilled_reference_sites=refilled, matching_material_sites=matched,
                occupied_fraction=str(Fraction(occupied, len(selected))) if selected else None,
                refill_fraction=str(Fraction(refilled, len(original))) if original else None,
                material_match_fraction=str(Fraction(matched, len(original))) if original else None)
