"""Finite V0 space; boundary behavior for movement is not yet implemented."""

from dataclasses import dataclass, field

from bitgenesis.organism import Organism
from bitgenesis.resources import Resources


@dataclass
class World:
    width: int
    height: int
    organisms: list[Organism] = field(default_factory=list)
    resources: Resources = field(default_factory=Resources)

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("World dimensions must be positive")
