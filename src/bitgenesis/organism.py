"""Explicit V0 organism state; no built-in food-seeking behavior."""

from dataclasses import dataclass

from bitgenesis.genome import Genome


@dataclass
class Organism:
    organism_id: int
    genome: Genome
    x: int
    y: int
    energy: float
