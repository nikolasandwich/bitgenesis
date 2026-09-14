"""Experimental V2 world; explicit development at every attempted birth."""
from dataclasses import dataclass, asdict
from hashlib import sha256
from random import Random

from bitgenesis.v1.controller import Genome, inputs, intervene
from .development import DevelopmentGenome, develop
from .direct_control import construct_direct

RULES_VERSION = "v2-world-1"
STREAMS = ("initial", "resources", "order", "ties", "sensors", "birth", "mutation")
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(frozen=True)
class Config:
    width: int = 32
    height: int = 32
    capacity: int = 24
    initial_food: int = 12
    founders: int = 80
    initial_energy: int = 640
    renewal_per_thousand: int = 15
    renewal_amount: int = 4
    basal_cost: int = 1
    decision_cost: int = 1
    movement_cost: int = 0
    feeding_limit: int = 8
    birth_threshold: int = 1280
    birth_cost: int = 0
    mutation_per_thousand: int = 100
    direct_padding_cost: int = 0

    def __post_init__(self):
        for name, value in asdict(self).items():
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if min(self.width, self.height) < 3:
            raise ValueError("dimensions must be at least three")
        if self.initial_food > self.capacity or self.founders > self.width * self.height:
            raise ValueError("initial occupancy or food exceeds capacity")
        if self.initial_energy < 1 or self.birth_threshold < self.birth_cost + 2:
            raise ValueError("initial and post-birth energies must be positive")
        if max(self.renewal_per_thousand, self.mutation_per_thousand) > 1000:
            raise ValueError("probability exceeds 1000")


@dataclass
class Organism:
    id: int
    parent: int | None
    founder: int
    generation: int
    birth_tick: int
    x: int
    y: int
    energy: int
    genome: Genome | DevelopmentGenome
    controller: Genome
    mode: str = "intact"
    death_tick: int | None = None
    offspring: int = 0


class World:
    def __init__(self, config: Config, seed: int, mode: str = "intact", encoding: str = "developmental",
                 founder_genomes=None):
        if encoding not in ("developmental", "direct"):
            raise ValueError("invalid encoding")
        self.encoding = encoding
        genetic_type = DevelopmentGenome if encoding == "developmental" else Genome
        if founder_genomes is not None and (len(founder_genomes) != config.founders or
                any(type(g) is not genetic_type for g in founder_genomes)):
            raise ValueError("one correctly typed genome per attempted founder required")
        if type(seed) is not int or mode not in ("intact", "blind", "shuffled"):
            raise ValueError("invalid seed or intervention")
        self.config, self.seed, self.tick = config, seed, 0
        self.rng = {name: Random(int.from_bytes(sha256(
            f"{RULES_VERSION}:{seed}:{name}".encode("ascii")).digest(), "big")) for name in STREAMS}
        self.food = [config.initial_food] * (config.width * config.height)
        self.organisms = {}
        self.lineage = {}
        self.occupied = {}
        self.events = []
        self.attempts = []
        self.initialization_spent = 0
        sites = self.rng["initial"].sample(range(len(self.food)), config.founders)
        for founder_index, site in enumerate(sites):
            genetic_type = DevelopmentGenome if encoding == "developmental" else Genome
            genes = genetic_type.random(self.rng["initial"])
            if founder_genomes is not None:
                genes = founder_genomes[founder_index]
            _, attempt = self._construct(None, site % config.width, site // config.width,
                                         config.initial_energy, genes, mode)
            self.initialization_spent += attempt['construction_cost'] + attempt['failure_loss']
        expected = sum(self.food) + config.founders * config.initial_energy - self.initialization_spent
        if self.total_energy() != expected:
            raise AssertionError("initial development ledger mismatch")

    def _construct(self, parent, x, y, allocation, genome, mode):
        identifier = len(self.attempts)
        result = (develop(genome, allocation) if self.encoding == "developmental" else
                  construct_direct(genome.weights, allocation, self.config.direct_padding_cost))
        remaining = allocation - result.cost
        valid = result.valid and remaining > 0
        attempt = {'id': identifier, 'tick': self.tick,
                   'parent': parent.id if parent is not None else None,
                   'x': x, 'y': y, 'encoding': self.encoding, 'genome': asdict(genome),
                   'allocation': allocation, 'construction_cost': result.cost,
                   'failure_loss': 0 if valid else remaining,
                   'living_energy': remaining if valid else 0, 'valid': valid,
                   'reason': result.reason if not result.valid or remaining > 0 else 'no_living_energy',
                   'construction': asdict(result)}
        self.attempts.append(attempt)
        self.events.append({'event': 'development', **attempt})
        if not valid:
            return None, attempt
        organism = Organism(identifier, parent.id if parent is not None else None,
            parent.founder if parent is not None else identifier,
            parent.generation + 1 if parent is not None else 0,
            self.tick, x, y, remaining, genome, Genome(result.weights), mode)
        self._add(organism)
        return organism, attempt

    def _add(self, organism):
        self.organisms[organism.id] = organism
        self.lineage[organism.id] = organism
        self.occupied[(organism.x, organism.y)] = organism.id
        self.events.append({"event": "birth", "tick": self.tick, **asdict(organism)})

    def neighbors(self, organism):
        return [((organism.x + dx) % self.config.width,
                 (organism.y + dy) % self.config.height) for dx, dy in DIRECTIONS]

    def total_energy(self):
        return sum(self.food) + sum(o.energy for o in self.organisms.values())

    def _charge(self, organism, cost, phase, record):
        paid = min(organism.energy, cost)
        organism.energy -= paid
        record[phase] = paid
        if organism.energy == 0:
            organism.death_tick = self.tick
            del self.organisms[organism.id]
            del self.occupied[(organism.x, organism.y)]
            self.events.append({"event": "death", "tick": self.tick,
                                "id": organism.id, "phase": phase})
            return False
        return True

    def step(self):
        c = self.config
        self.tick += 1
        before = self.total_energy()
        added = 0
        for site in range(len(self.food)):
            proposal = self.rng["resources"].randrange(1000)
            if proposal < c.renewal_per_thousand:
                amount = min(c.renewal_amount, c.capacity - self.food[site])
                self.food[site] += amount
                added += amount
        actors = list(self.organisms)
        self.rng["order"].shuffle(actors)
        records = []
        for identifier in actors:
            o = self.organisms[identifier]
            record = {"id": identifier, "tick": self.tick, "energy_before": o.energy,
                      "basal": 0, "decision": 0, "movement": 0, "birth_cost": 0,
                      "intake": 0, "child_energy": 0, "development_cost": 0, "failure_loss": 0, "action": None, "blocked": False}
            records.append(record)
            if not self._charge(o, c.basal_cost, "basal", record):
                record["energy_after"] = 0
                continue
            if not self._charge(o, c.decision_cost, "decision", record):
                record["energy_after"] = 0
                continue
            neighbors = self.neighbors(o)
            food = tuple(self.food[y * c.width + x] for x, y in [(o.x, o.y)] + neighbors)
            values = inputs(food, c.capacity, o.energy)
            permutation = self.rng["sensors"].randrange(24)
            ticket = self.rng["ties"].randrange(60)
            sensed = intervene(values, o.mode, permutation)
            action = o.controller.action(sensed, ticket)
            record.update(inputs=values, sensed=sensed, permutation=permutation,
                          tie_ticket=ticket, action=action)
            if action:
                target = neighbors[action - 1]
                record["blocked"] = target in self.occupied
                if not self._charge(o, c.movement_cost, "movement", record):
                    record["energy_after"] = 0
                    continue
                if not record["blocked"]:
                    del self.occupied[(o.x, o.y)]
                    o.x, o.y = target
                    self.occupied[target] = identifier
            site = o.y * c.width + o.x
            intake = min(c.feeding_limit, self.food[site])
            self.food[site] -= intake
            o.energy += intake
            record["intake"] = intake
            free = [p for p in self.neighbors(o) if p not in self.occupied]
            if o.energy >= c.birth_threshold and free:
                x, y = self.rng["birth"].choice(free)
                self._charge(o, c.birth_cost, "birth_cost", record)
                child_energy = o.energy // 2
                o.energy -= child_energy
                child, attempt = self._construct(o, x, y, child_energy,
                    o.genome.offspring(self.rng["mutation"], c.mutation_per_thousand), o.mode)
                if child is not None:
                    o.offspring += 1
                record["child_energy"] = attempt['living_energy']
                record["development_cost"] = attempt['construction_cost']
                record["failure_loss"] = attempt['failure_loss']
                record["development_attempt"] = attempt['id']
            record["energy_after"] = o.energy
        spent = sum(sum(r[k] for k in ("basal", "decision", "movement", "birth_cost", "development_cost", "failure_loss")) for r in records)
        after = self.total_energy()
        if after != before + added - spent:
            raise AssertionError("world energy ledger mismatch")
        return {"tick": self.tick, "population": len(self.organisms),
                "energy_before": before, "resource_added": added, "spent": spent,
                "energy_after": after, "actors": records}
