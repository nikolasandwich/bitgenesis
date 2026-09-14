"""Inherited directional construction programs, expressed before mutation."""
from dataclasses import dataclass
from .local import Unit
from .material import convert as material_convert

RULES_VERSION = 'v4-heredity-1'


@dataclass(frozen=True)
class HeritableUnit:
    material: int
    energy: int
    program: tuple[int, int, int, int]

    def __post_init__(self):
        Unit(self.material, self.energy)
        if type(self.program) is not tuple or len(self.program) != 4 or any(
            type(x) is not int or not 0 <= x < 4 for x in self.program
        ):
            raise ValueError('program must contain four immutable labels in0..3')


def convert(units, raw, width, height, directions, mutation_tickets,
            threshold=16, construction_cost=4, copy_cost=1, mutation_per_thousand=10):
    """One mutation ticket (chance, entry, offset1..3) per site, including empty.

    Child material is expressed from the original parent program. Mutation alters
    the inherited child program only and can affect its future offspring.
    """
    if any(u is not None and type(u) is not HeritableUnit for u in units):
        raise ValueError('invalid heritable unit')
    if type(copy_cost) is not int or copy_cost < 0 or type(construction_cost) is not int or construction_cost < 0:
        raise ValueError('nonnegative integer construction/copy costs required')
    if type(mutation_per_thousand) is not int or not 0 <= mutation_per_thousand <= 1000:
        raise ValueError('invalid mutation probability')
    if len(mutation_tickets) != len(units):
        raise ValueError('one mutation ticket per site required')
    for ticket in mutation_tickets:
        if type(ticket) is not tuple or len(ticket) != 3 or any(type(x) is not int for x in ticket):
            raise ValueError('invalid mutation ticket')
        if not (0 <= ticket[0] < 1000 and 0 <= ticket[1] < 4 and 1 <= ticket[2] <= 3):
            raise ValueError('mutation ticket out of range')
    physical = [None if u is None else Unit(u.material,u.energy) for u in units]
    after, stock, record = material_convert(physical,raw,width,height,directions,
                                            threshold,construction_cost+copy_cost)
    programs = {i:u.program for i,u in enumerate(units) if u is not None}
    count = 0
    for proposal in record['proposals']:
        if proposal['reason'] != 'formed':
            continue
        source,target = proposal['source'],proposal['target']
        parent = units[source]
        expressed = parent.program[proposal['direction']]
        chance,entry,offset = mutation_tickets[source]
        inherited = list(parent.program)
        mutated = chance < mutation_per_thousand
        if mutated:
            inherited[entry] = (inherited[entry]+offset)%4
        programs[target] = tuple(inherited)
        after[target] = Unit(expressed,after[target].energy)
        proposal.update(parent_material=parent.material,material=expressed,
                        parent_program=list(parent.program),child_program=inherited,
                        mutation_ticket=list(mutation_tickets[source]),mutated=mutated,
                        construction_cost=construction_cost,copy_cost=copy_cost)
        count += 1
    result = [None if u is None else HeritableUnit(u.material,u.energy,programs[i])
              for i,u in enumerate(after)]
    record.update(construction_spent=count*construction_cost,copy_spent=count*copy_cost)
    return result, stock, record
