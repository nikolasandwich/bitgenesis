"""V0 inherited information. Copying/mutation semantics remain to be designed."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Genome:
    genes: tuple[int, ...] = ()
