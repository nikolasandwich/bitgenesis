"""Research-only feeding observer for the pinned V0 engine; no CLI or study yet."""

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
            world.feeding_records.append(dict(tick=world.tick,id=actor.id,
                founder_id=actor.founder_id,position=position,genome=actor.genome,
                food_before=previous,food_after=value,eaten=eaten,
                energy_before_feeding=actor.energy))
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
        self.food = _ObservedFood(self.food,self)

    def _pay(self, organism, amount):
        self._feeding_actor = organism
        super()._pay(organism,amount)

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
