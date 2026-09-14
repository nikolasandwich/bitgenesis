"""Direct-expression control with explicit construction accounting."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DirectConstruction:
    weights: tuple[int, ...]
    cost: int
    valid: bool
    reason: str


def construct_direct(weights, energy_budget, padding_cost=0):
    if type(weights) is not tuple or len(weights)!=35 or any(type(w) is not int or not -100<=w<=100 for w in weights):
        raise ValueError('35 immutable bounded weights required')
    if type(energy_budget) is not int or energy_budget<0 or type(padding_cost) is not int or padding_cost<0:
        raise ValueError('nonnegative integer budgets/costs required')
    # Reading 35 coefficients costs one unit each, then expressing nonzeros.
    if energy_budget<35:
        return DirectConstruction((0,)*35,0,False,'read_budget')
    active=sum(w!=0 for w in weights)
    if energy_budget<35+active:
        return DirectConstruction((0,)*35,35,False,'expression_budget')
    cost=35+active
    if energy_budget<cost+padding_cost:
        return DirectConstruction((0,)*35,cost,False,'padding_budget')
    cost+=padding_cost
    if not active:
        return DirectConstruction((0,)*35,cost,False,'empty_structure')
    return DirectConstruction(weights,cost,True,'constructed')
