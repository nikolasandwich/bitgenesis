"""Text initialization summary. A spatial/lineage view is future V0 work."""

from bitgenesis.metrics import observe
from bitgenesis.simulation import RULES_VERSION, Simulation


def render_summary(simulation: Simulation) -> str:
    snapshot = observe(simulation)
    config = simulation.config
    return (
        f"BitGenesis V0 scaffold ({RULES_VERSION})\n"
        f"World: {config.width} x {config.height} | seed: {config.seed}\n"
        f"Tick: {snapshot.tick} | population: {snapshot.population}\n"
        f"Organism energy: {snapshot.organism_energy:g} | "
        f"resource energy: {snapshot.resource_energy:g}\n"
        "Initialization only; evolutionary dynamics are not implemented yet."
    )
