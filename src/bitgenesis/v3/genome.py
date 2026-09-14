"""Inherited development and resource-processing allocation."""
from dataclasses import dataclass
from random import Random

from bitgenesis.v2.development import DevelopmentGenome, GENE_BOUNDS


@dataclass(frozen=True)
class EcologyGenome:
    development: DevelopmentGenome
    allocation_a: int

    def __post_init__(self):
        if type(self.development) is not DevelopmentGenome:
            raise ValueError('development genome required')
        if type(self.allocation_a) is not int or not 0 <= self.allocation_a <= 16:
            raise ValueError('allocation must be an integer in0..16')

    @classmethod
    def random(cls, rng: Random):
        return cls(DevelopmentGenome.random(rng), rng.randrange(17))

    def offspring(self, rng: Random, mutation_per_thousand=100):
        if type(mutation_per_thousand) is not int or not 0 <= mutation_per_thousand <= 1000:
            raise ValueError('invalid mutation probability')
        if rng.randrange(1000) >= mutation_per_thousand:
            return self
        index = rng.randrange(11)
        radius = 10 if index in (1, 3, 5, 8) else 1
        delta = rng.randint(-radius, radius)
        if index == 10:
            return EcologyGenome(self.development, max(0, min(16, self.allocation_a + delta)))
        genes = list(self.development.genes)
        low, high = GENE_BOUNDS[index]
        genes[index] = max(low, min(high, genes[index] + delta))
        return EcologyGenome(DevelopmentGenome(tuple(genes)), self.allocation_a)
