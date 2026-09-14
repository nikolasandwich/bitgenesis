"""Research-only local food/occupancy snapshots before each actor's basal payment."""
from scripts.observe_v0_energy import EnergyWorld


class LocalResourceWorld(EnergyWorld):
    """No sensing is supplied to organisms; drain all four streams after each step.

    Snapshots follow tick regrowth and all earlier actors, but precede this actor's
    basal payment, movement, feeding and birth. Neighbor order follows pinned V0.
    Food availability is descriptive, not a guarantee of survival or reachability.
    """
    def __post_init__(self):
        super().__post_init__()
        self.local_resource_records = []
        self.local_capture_enabled = True

    def _pay(self, organism, amount):
        if self.local_capture_enabled and (self._energy_action is None or self._energy_action['id'] != organism.id):
            positions = list(dict.fromkeys([organism.position, *self.neighbors(organism.position)]))
            self.local_resource_records.append(dict(
                observation_schema=1, tick=self.tick, id=organism.id,
                founder_id=organism.founder_id, position=organism.position,
                energy_before_action=organism.energy,
                sites=[dict(position=p, food=self.food[p], occupant_id=self.occupied.get(p))
                       for p in positions]))
        super()._pay(organism, amount)

    def step(self):
        if type(self.local_capture_enabled) is not bool:
            raise ValueError("Local capture switch must be boolean")
        super().step()

    def drain_local_resources(self):
        records, self.local_resource_records = self.local_resource_records, []
        return records
