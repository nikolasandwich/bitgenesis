"""Research-only feeding and birth-opportunity observer for the pinned V0 engine."""

import hashlib
from pathlib import Path
from bitgenesis.v0 import engine

ENGINE_SHA256 = "8f3ed33ad0ebe802c099e3e6f8ae61f9bcc526b98512f31f48ec40478fbfa7ff"


class _ObservedFood(list):
    def __init__(self, values, world):
        super().__init__(values)
        self.world = world

    def __setitem__(self, position, value):
        world = self.world
        actor = world._feeding_actor
        if actor is not None:
            previous = self[position]
            eaten = previous-value
            if position != actor.position or eaten != min(world.config.feeding_rate,previous):
                raise ValueError("Observed food write differs from pinned feeding semantics")
            world.feeding_records.append(dict(observation_schema=3,tick=world.tick,id=actor.id,
                founder_id=actor.founder_id,position=position,genome=actor.genome,
                food_before=previous,food_after=value,eaten=eaten,
                energy_before_feeding=actor.energy,
                position_before_action=world._action_position,
                movement_attempted=world._movement_attempted,
                moved=actor.position != world._action_position,
                birth_eligible=actor.energy+eaten >= world.config.birth_threshold,
                empty_neighbors_before_birth=sum(p not in world.occupied for p in world.neighbors(position)),
                child_id=None))
            world._fed = True
        super().__setitem__(position,value)


class FeedingWorld(engine.World):
    """Retain feeding attempts (including zero intake), separate from world events.

    The actor is identified by the preceding energy payment. At each tick start,
    regrowth has no active actor. This depends on the pinned engine's ordering.
    Call drain_feeding after each recorded tick to bound observer retention.
    """
    def __post_init__(self):
        digest = hashlib.sha256(Path(engine.__file__).read_text(encoding="utf-8").encode()).hexdigest()
        if digest != ENGINE_SHA256:
            raise ValueError("Feeding observer requires its pinned V0 engine source")
        super().__post_init__()
        self._feeding_actor = None
        self.feeding_records = []
        self.pre_feeding_deaths = []
        self.food = _ObservedFood(self.food,self)

    def _pay(self, organism, amount):
        if self._feeding_actor is not organism:
            self._action_position = organism.position
            self._action_energy = organism.energy
            self._movement_attempted = False
            self._fed = False
        elif not self._fed:
            self._movement_attempted = True
        self._feeding_actor = organism
        super()._pay(organism,amount)

    def _die(self, organism):
        if self._feeding_actor is not organism or self._fed or organism.energy != 0:
            raise ValueError("Death differs from pinned pre-feeding phases")
        self.pre_feeding_deaths.append(dict(observation_schema=1,tick=self.tick,id=organism.id,
            founder_id=organism.founder_id,position=organism.position,
            position_before_action=self._action_position,energy_before_action=self._action_energy,
            phase="movement" if self._movement_attempted else "basal",
            movement_attempted=self._movement_attempted))
        super()._die(organism)

    def _birth(self, position, energy, genome, parent):
        child = super()._birth(position,energy,genome,parent)
        if parent is not None:
            row = self.feeding_records[-1]
            if row["id"] != parent.id or row["tick"] != self.tick or row["child_id"] is not None:
                raise ValueError("Birth does not match the current feeding observation")
            row["child_id"] = child.id
        return child

    def step(self):
        if not isinstance(self.food,_ObservedFood) or self.food.world is not self:
            raise ValueError("Initialize observed food in place; do not replace the list")
        self._feeding_actor = None
        try:
            super().step()
        finally:
            self._feeding_actor = None

    def drain_feeding(self):
        records,self.feeding_records = self.feeding_records,[]
        return records

    def drain_pre_feeding_deaths(self):
        records,self.pre_feeding_deaths = self.pre_feeding_deaths,[]
        return records
