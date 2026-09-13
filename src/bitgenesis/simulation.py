"""V0 initialization only. No time loop or evolutionary dynamics yet."""

from dataclasses import dataclass

from bitgenesis.world import World

RULES_VERSION = "v0-scaffold-1"


@dataclass(frozen=True)
class SimulationConfig:
    seed: int = 42
    width: int = 16
    height: int = 12

    def __post_init__(self) -> None:
        for name in ("seed", "width", "height"):
            if type(getattr(self, name)) is not int:
                raise ValueError(f"{name} must be an integer")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("World dimensions must be positive")


@dataclass
class Simulation:
    config: SimulationConfig
    world: World
    tick: int = 0


def initialize(config: SimulationConfig) -> Simulation:
    return Simulation(config=config, world=World(config.width, config.height))
