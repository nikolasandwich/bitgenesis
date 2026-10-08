"""Driven interaction followed by local material conversion, without group IDs."""
from dataclasses import asdict

from .driven import step as driven_step
from .local import components
from .material import convert

RULES_VERSION = 'v4-growing-1'


def step(units, raw, width, height, proposals, directions, capacity=64,
         leak=1, bond_cost=1, exchange=True, threshold=16, construction_cost=4):
    """Input -> leakage -> interaction -> dissolution -> local formation.

    Interaction components refer to the intermediate population, before any
    material conversions. New units first receive input on the following step.
    """
    intermediate, driven = driven_step(
        units, width, height, proposals, capacity, leak, bond_cost, exchange)
    result, resources, material = convert(
        intermediate, raw, width, height, directions, threshold, construction_cost)
    spent = driven['spent'] + material['spent']
    if material['energy_after'] != driven['energy_before'] + driven['imported'] - spent:
        raise AssertionError('composed energy ledger mismatch')
    if any(u is not None and u.energy > capacity for u in result):
        raise AssertionError('formation exceeded capacity')
    return result, resources, dict(
        driven=driven, material=material,
        interaction_units=[None if u is None else asdict(u) for u in intermediate],
        interaction_components=components(intermediate, driven['interaction']['bonds']),
        energy_before=driven['energy_before'], energy_after=material['energy_after'],
        imported=driven['imported'], rejected_import=driven['rejected_import'],
        spent=spent, material_before=material['material_before'],
        material_after=material['material_after'])
