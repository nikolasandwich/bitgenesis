"""Integer-energy, asynchronous toroidal world with explicit organisms.

The genome encodes movement probability only. There is no food sensor, learning,
fitness ranking, or policy optimizer. All randomness comes from one local RNG.
"""

from dataclasses import asdict, dataclass, field
import random


@dataclass(frozen=True)
class Config:
    seed: int = 42
    width: int = 32
    height: int = 32
    initial_population: int = 80
    initial_energy: int = 24
    initial_food: int = 8
    food_capacity: int = 24
    regrowth_probability: int = 40  # Per thousand, per site, per tick.
    regrowth_amount: int = 4
    feeding_rate: int = 8
    basal_cost: int = 1
    movement_cost: int = 1
    birth_threshold: int = 40
    birth_cost: int = 4
    mutation_probability: int = 100  # Per thousand, per birth.
    mutation_step: int = 100

    def __post_init__(self):
        for name, value in asdict(self).items():
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer")
            if name != "seed" and value < 0:
                raise ValueError(f"{name} must be nonnegative")
        if self.width < 2 or self.height < 2:
            raise ValueError("width and height must be at least 2")
        if self.initial_population > self.width * self.height:
            raise ValueError("initial_population exceeds available cells")
        if self.initial_energy < 1 or self.basal_cost < 1:
            raise ValueError("initial_energy and basal_cost must be positive")
        if self.initial_food > self.food_capacity:
            raise ValueError("initial_food exceeds food_capacity")
        if self.birth_threshold < self.birth_cost + 2:
            raise ValueError("birth_threshold must leave at least one energy per descendant")
        if self.regrowth_probability > 1000 or self.mutation_probability > 1000:
            raise ValueError("probabilities must be in [0, 1000]")


@dataclass
class Individual:
    id: int
    parent_id: int | None
    founder_id: int
    generation: int
    birth_tick: int
    genome: int
    position: int
    energy: int
    offspring: int = 0
    death_tick: int | None = None


@dataclass
class World:
    config: Config
    tick: int = 0
    food: list[int] = field(default_factory=list)
    living: dict[int, Individual] = field(default_factory=dict)
    lineage: dict[int, Individual] = field(default_factory=dict)
    occupied: dict[int, int] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    supplied_energy: int = 0
    dissipated_energy: int = 0
    next_id: int = 0

    def __post_init__(self):
        self.rng = random.Random(self.config.seed)
        c = self.config
        self.food = [c.initial_food] * (c.width * c.height)
        self.supplied_energy = sum(self.food) + c.initial_population * c.initial_energy
        for position in self.rng.sample(range(len(self.food)), c.initial_population):
            self._birth(position, c.initial_energy, self.rng.randrange(1001), None)

    def _birth(self, position, energy, genome, parent):
        identity = self.next_id
        self.next_id += 1
        organism = Individual(identity, None if parent is None else parent.id,
                              identity if parent is None else parent.founder_id,
                              0 if parent is None else parent.generation + 1,
                              self.tick, genome, position, energy)
        self.living[identity] = self.lineage[identity] = organism
        self.occupied[position] = identity
        self.events.append({"tick": self.tick, "event": "birth", "id": identity,
                            "parent_id": organism.parent_id, "genome": genome,
                            "energy": energy, "position": position})
        return organism

    def neighbors(self, position):
        c = self.config
        x, y = position % c.width, position // c.width
        # Deduplicate in narrow worlds; order is part of the rules version.
        return list(dict.fromkeys([y*c.width+(x+1)%c.width,
                                   y*c.width+(x-1)%c.width,
                                   ((y+1)%c.height)*c.width+x,
                                   ((y-1)%c.height)*c.width+x]))

    def _pay(self, organism, amount):
        paid = min(organism.energy, amount)
        organism.energy -= paid
        self.dissipated_energy += paid

    def _die(self, organism):
        organism.death_tick = self.tick
        del self.living[organism.id]
        del self.occupied[organism.position]
        self.events.append({"tick": self.tick, "event": "death", "id": organism.id,
                            "energy": organism.energy, "position": organism.position})

    def step(self):
        c = self.config
        self.tick += 1
        for position, energy in enumerate(self.food):
            if self.rng.randrange(1000) < c.regrowth_probability:
                added = min(c.regrowth_amount, c.food_capacity - energy)
                self.food[position] += added
                self.supplied_energy += added
        order = list(self.living)
        self.rng.shuffle(order)
        for identity in order:
            organism = self.living[identity]
            self._pay(organism, c.basal_cost)
            if organism.energy == 0:
                self._die(organism)
                continue
            if self.rng.randrange(1000) < organism.genome:
                self._pay(organism, c.movement_cost)
                if organism.energy == 0:
                    self._die(organism)
                    continue
                destination = self.rng.choice(self.neighbors(organism.position))
                if destination not in self.occupied:
                    del self.occupied[organism.position]
                    organism.position = destination
                    self.occupied[destination] = organism.id
            eaten = min(c.feeding_rate, self.food[organism.position])
            self.food[organism.position] -= eaten
            organism.energy += eaten
            if organism.energy >= c.birth_threshold:
                empty = [p for p in self.neighbors(organism.position) if p not in self.occupied]
                if empty:
                    destination = self.rng.choice(empty)
                    self._pay(organism, c.birth_cost)
                    child_energy = organism.energy // 2
                    organism.energy -= child_energy
                    genome = organism.genome
                    # Always draw the mutation decision, including controls.
                    if self.rng.randrange(1000) < c.mutation_probability:
                        genome = max(0, min(1000, genome + self.rng.randint(-c.mutation_step,
                                                                                c.mutation_step)))
                    organism.offspring += 1
                    self._birth(destination, child_energy, genome, organism)
        # Newborns can occupy space immediately, but act starting next tick.

    def snapshot(self):
        population = list(self.living.values())
        count = len(population)
        return {"tick": self.tick, "population": count,
                "births": len(self.lineage) - self.config.initial_population,
                "deaths": len(self.lineage) - count,
                "organism_energy": sum(o.energy for o in population),
                "food_energy": sum(self.food),
                "supplied_energy": self.supplied_energy,
                "dissipated_energy": self.dissipated_energy,
                "mean_genome": sum(o.genome for o in population)/count if count else None,
                "genome_variants": len({o.genome for o in population}),
                "founder_lineages": len({o.founder_id for o in population}),
                "max_generation": max((o.generation for o in population), default=None)}

    def check_invariants(self):
        c = self.config
        assert len(self.occupied) == len(self.living)
        assert all(self.occupied[o.position] == o.id and o.energy > 0
                   and 0 <= o.genome <= 1000 and o.death_tick is None
                   for o in self.living.values())
        assert len(self.food) == c.width * c.height
        assert all(0 <= p < len(self.food) for p in self.occupied)
        assert all(0 <= value <= c.food_capacity for value in self.food)
        state = self.snapshot()
        assert state["organism_energy"] + state["food_energy"] + self.dissipated_energy == self.supplied_energy
