"""Driven interaction followed by inherited directional construction, without group IDs."""
from dataclasses import asdict

from .driven import step as driven_step
from .local import Unit, components
from .heredity import HeritableUnit, convert

RULES_VERSION = 'v4-hereditary-growing-1'


def step(units, raw, width, height, proposals, directions, mutation_tickets, capacity=64,
         leak=1, bond_cost=1, exchange=True, threshold=16, construction_cost=4, copy_cost=1, mutation_per_thousand=10):
    """Input -> leakage -> interaction -> dissolution -> local formation.

    Interaction components refer to the intermediate population, before any
    material conversions. New units first receive input on the following step.
    """
    if any(u is not None and type(u) is not HeritableUnit for u in units):
        raise ValueError('invalid heritable unit')
    physical = [None if u is None else Unit(u.material,u.energy) for u in units]
    intermediate, driven = driven_step(
        physical, width, height, proposals, capacity, leak, bond_cost, exchange)
    inherited = [None if u is None else HeritableUnit(u.material,u.energy,units[i].program)
                 for i,u in enumerate(intermediate)]
    result, resources, material = convert(
        inherited, raw, width, height, directions, mutation_tickets, threshold, construction_cost,
        copy_cost, mutation_per_thousand)
    spent = driven['spent'] + material['spent']
    if material['energy_after'] != driven['energy_before'] + driven['imported'] - spent:
        raise AssertionError('composed energy ledger mismatch')
    if any(u is not None and u.energy > capacity for u in result):
        raise AssertionError('formation exceeded capacity')
    return result, resources, dict(
        driven=driven, material=material,
        interaction_units=[None if u is None else asdict(u) for u in inherited],
        interaction_components=components(intermediate, driven['interaction']['bonds']),
        energy_before=driven['energy_before'], energy_after=material['energy_after'],
        imported=driven['imported'], rejected_import=driven['rejected_import'],
        spent=spent, material_before=material['material_before'],
        material_after=material['material_after'])
