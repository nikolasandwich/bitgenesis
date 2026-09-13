"""Read-only observations; never award fitness or modify the simulation."""

from dataclasses import dataclass

from bitgenesis.simulation import Simulation


@dataclass(frozen=True)
class Snapshot:
    tick: int
    population: int
    organism_energy: float
    resource_energy: float


def observe(simulation: Simulation) -> Snapshot:
    world = simulation.world
    return Snapshot(
        tick=simulation.tick,
        population=len(world.organisms),
        organism_energy=sum(o.energy for o in world.organisms),
        resource_energy=sum(world.resources.energy_by_position.values()),
    )
