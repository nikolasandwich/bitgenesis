"""Local integer field development into a sparse 5x7 controller structure.

This deliberately preserves V1's interface for matched direct-encoding controls.
"""
from dataclasses import dataclass
from random import Random

GENE_BOUNDS = ((0,34),(-100,100),(0,34),(-100,100),(0,34),(-100,100),
               (0,4),(0,10),(0,100),(1,16))


@dataclass(frozen=True)
class DevelopmentGenome:
    # Three (site, signed amplitude) sources, diffusion, decay, threshold, rounds.
    genes: tuple[int, ...]

    def __post_init__(self):
        if type(self.genes) is not tuple or len(self.genes) != 10 or any(type(g) is not int for g in self.genes):
            raise ValueError('ten immutable integer genes required')
        for index in (0,2,4):
            if not 0 <= self.genes[index] < 35 or not -100 <= self.genes[index+1] <= 100:
                raise ValueError('invalid developmental source')
        for index,low,high in ((6,0,4),(7,0,10),(8,0,100),(9,1,16)):
            if not low <= self.genes[index] <= high:
                raise ValueError('invalid developmental parameter')

    @classmethod
    def random(cls, rng: Random):
        return cls(tuple(rng.randint(low,high) for low,high in GENE_BOUNDS))

    def offspring(self, rng: Random, mutation_per_thousand: int = 100):
        if type(mutation_per_thousand) is not int or not 0 <= mutation_per_thousand <= 1000:
            raise ValueError('invalid mutation probability')
        if rng.randrange(1000) >= mutation_per_thousand:
            return self
        index=rng.randrange(10)
        # Site/round/diffusion/decay mutate locally; amplitudes/threshold have
        # ten-unit steps. Clipping and zero perturbations can be silent.
        radius=10 if index in (1,3,5,8) else 1
        delta=rng.randint(-radius,radius)
        low,high=GENE_BOUNDS[index]
        genes=list(self.genes)
        genes[index]=max(low,min(high,genes[index]+delta))
        return DevelopmentGenome(tuple(genes))


@dataclass(frozen=True)
class DevelopedController:
    weights: tuple[int, ...]
    active_sites: tuple[int, ...]
    rounds_completed: int
    updates: int
    cost: int
    valid: bool
    reason: str
    history: tuple[tuple[int, ...], ...]


def develop(genome: DevelopmentGenome, energy_budget: int) -> DevelopedController:
    """One energy unit per cell update, and one per expressed coefficient.

    Stop before an unaffordable complete round; no partially updated structure
    is viable. Closed rectangular boundaries have missing neighbors equal self.
    Each update uses only prior-round self/neighbors (synchronous), signed
    truncation toward zero and decay toward zero. Sources are initial conditions,
    not repeatedly injected resources.
    """
    if type(energy_budget) is not int or energy_budget < 0:
        raise ValueError('nonnegative integer development budget required')
    genes = genome.genes
    field = [0]*35
    for index in (0,2,4):
        site, amplitude = genes[index:index+2]
        field[site] = max(-100,min(100,field[site]+amplitude))
    history = [tuple(field)]
    diffusion, decay, threshold, rounds = genes[6:]
    cost = 0
    for completed in range(rounds):
        if cost + 35 > energy_budget:
            return DevelopedController((0,)*35,(),completed,completed*35,cost,False,'round_budget',tuple(history))
        following=[]
        for site,value in enumerate(field):
            row,column=divmod(site,7)
            neighbors=[field[site-7] if row else value,
                       field[site+7] if row<4 else value,
                       field[site-1] if column else value,
                       field[site+1] if column<6 else value]
            numerator=(16-4*diffusion)*value+diffusion*sum(neighbors)
            mixed=(abs(numerator)//16)*(1 if numerator>=0 else -1)
            following.append(max(0,mixed-decay) if mixed>=0 else min(0,mixed+decay))
        field=following
        history.append(tuple(field))
        cost+=35
    active=tuple(i for i,value in enumerate(field) if value!=0 and abs(value)>=threshold)
    if cost+len(active)>energy_budget:
        return DevelopedController((0,)*35,(),rounds,rounds*35,cost,False,'expression_budget',tuple(history))
    cost+=len(active)
    if not active:
        return DevelopedController((0,)*35,(),rounds,rounds*35,cost,False,'empty_structure',tuple(history))
    weights=tuple(value if i in active else 0 for i,value in enumerate(field))
    return DevelopedController(weights,active,rounds,rounds*35,cost,True,'developed',tuple(history))
