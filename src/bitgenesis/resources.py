"""Sparse resource state. Feeding and replenishment rules are future V0 work."""

from dataclasses import dataclass, field


@dataclass
class Resources:
    energy_by_position: dict[tuple[int, int], float] = field(default_factory=dict)
