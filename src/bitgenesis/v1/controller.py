"""Integer linear controllers, with explicit interventions and tie sampling.

Input order: current/east/west/south/north food, energy, bias.
Output order: rest/east/west/south/north. World accounting is separate.
"""

from dataclasses import dataclass
from itertools import permutations
from random import Random

ACTIONS = ("rest", "east", "west", "south", "north")
DIRECTION_PERMUTATIONS = tuple(permutations(range(4)))
CONTROLLER_VERSION = "v1-linear-1"


def integer(value: int, low: int, high: int, name: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")


def inputs(food: tuple[int, ...], capacity: int, energy: int,
           energy_scale: int = 160) -> tuple[int, ...]:
    """Read an already charged live organism; zero-capacity food must be zero."""
    if type(capacity) is not int or capacity < 0:
        raise ValueError("capacity must be a nonnegative integer")
    if type(energy) is not int or energy <= 0:
        raise ValueError("energy must be a positive integer")
    if type(energy_scale) is not int or energy_scale <= 0:
        raise ValueError("energy scale must be a positive integer")
    if len(food) != 5:
        raise ValueError("five food readings required")
    for value in food:
        integer(value, 0, capacity, "food")
    scaled = tuple(1000 * value // capacity if capacity else 0 for value in food)
    return scaled + (min(1000, 1000 * energy // energy_scale), 1000)


def intervene(values: tuple[int, ...], mode: str, permutation: int) -> tuple[int, ...]:
    """Permutation is supplied externally, including for intact/blind decisions.

    All 24 permutations retain multiplicity, including identity. Blind removes
    all five food readings; shuffled retains current-site food and the multiset.
    """
    validate_inputs(values)
    integer(permutation, 0, 23, "permutation")
    if mode == "intact":
        return values
    if mode == "blind":
        return (0,) * 5 + values[5:]
    if mode == "shuffled":
        return (values[0],) + tuple(values[1 + i] for i in DIRECTION_PERMUTATIONS[permutation]) + values[5:]
    raise ValueError("unknown sensory intervention")


def validate_inputs(values: tuple[int, ...]) -> None:
    if len(values) != 7:
        raise ValueError("seven inputs required")
    for value in values:
        integer(value, 0, 1000, "input")
    if values[-1] != 1000:
        raise ValueError("bias must equal 1000")


@dataclass(frozen=True)
class Genome:
    weights: tuple[int, ...]

    def __post_init__(self) -> None:
        if type(self.weights) is not tuple or len(self.weights) != 35:
            raise ValueError("weights must be an immutable tuple of length 35")
        for value in self.weights:
            integer(value, -100, 100, "weight")

    @classmethod
    def random(cls, rng: Random) -> "Genome":
        return cls(tuple(rng.randrange(-100, 101) for _ in range(35)))

    def offspring(self, rng: Random, mutation_per_thousand: int = 100) -> "Genome":
        """One probability draw per birth; extra draws only when selected.

        A selected mutation can be silent (zero perturbation or clipping).
        Selection is not a guarantee that the inherited genome changes.
        """
        integer(mutation_per_thousand, 0, 1000, "mutation probability")
        if rng.randrange(1000) >= mutation_per_thousand:
            return self
        coordinate = rng.randrange(35)
        delta = rng.randrange(-10, 11)
        weights = list(self.weights)
        weights[coordinate] = max(-100, min(100, weights[coordinate] + delta))
        return Genome(tuple(weights))

    def scores(self, values: tuple[int, ...]) -> tuple[int, ...]:
        validate_inputs(values)
        return tuple(sum(self.weights[7 * action + i] * values[i] for i in range(7))
                     for action in range(5))

    def maxima(self, values: tuple[int, ...]) -> tuple[int, ...]:
        scores = self.scores(values)
        return tuple(i for i, score in enumerate(scores) if score == max(scores))

    def action(self, values: tuple[int, ...], tie_ticket: int) -> int:
        """A uniform integer ticket in [0,59] gives exact uniform ties of 1..5.

        The caller draws one ticket even for a unique maximum. No occupancy
        masking or environmental action preference is introduced here.
        """
        integer(tie_ticket, 0, 59, "tie ticket")
        maxima = self.maxima(values)
        return maxima[tie_ticket % len(maxima)]
