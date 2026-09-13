"""Future lifecycle logging record; no births or deaths are generated yet."""

from dataclasses import dataclass

from bitgenesis.genome import Genome


@dataclass
class LineageRecord:
    organism_id: int
    parent_id: int | None
    genome: Genome
    birth_tick: int
    death_tick: int | None = None
    offspring_count: int = 0
