"""Per-action energy ledger layered on the pinned, research-only feeding observer."""
from scripts.observe_v0_feeding import FeedingWorld


class EnergyWorld(FeedingWorld):
    """Drain all three observation buffers after each successful step.

    Original feeding/terminal schemas are unchanged. This observer does not resume
    checkpoints and assumes the pinned engine's sequential, single-parent actions.
    """
    def __post_init__(self):
        super().__post_init__()
        self.energy_records = []
        self._energy_action = None

    def _finish_energy_action(self):
        row = self._energy_action
        if row is None:
            return
        actor = self.lineage[row['id']]
        feeding = self.feeding_records[-1] if self.feeding_records else None
        if feeding is not None and (feeding['tick'], feeding['id']) == (self.tick, actor.id):
            row['eaten'] = feeding['eaten']
        row['energy_after_action'] = actor.energy
        row['died'] = actor.death_tick == self.tick
        paid = sum(row[k] for k in ('basal_paid', 'movement_paid', 'birth_paid'))
        if row['energy_before_action'] + row['eaten'] != actor.energy + paid + row['child_energy']:
            raise ValueError('Observed individual energy ledger does not balance')
        self.energy_records.append(row)
        self._energy_action = None

    def _pay(self, organism, amount):
        new_actor = self._energy_action is None or self._energy_action['id'] != organism.id
        if new_actor:
            self._finish_energy_action()
            self._energy_action = dict(observation_schema=1, tick=self.tick, id=organism.id,
                energy_before_action=organism.energy, basal_paid=0, movement_paid=0,
                birth_paid=0, eaten=0, child_id=None, child_energy=0)
            phase = 'basal_paid'
        else:
            phase = 'birth_paid' if self._fed else 'movement_paid'
        before = organism.energy
        super()._pay(organism, amount)
        self._energy_action[phase] += before - organism.energy

    def _birth(self, position, energy, genome, parent):
        child = super()._birth(position, energy, genome, parent)
        if parent is not None:
            row = self._energy_action
            if row is None or row['id'] != parent.id or row['child_id'] is not None:
                raise ValueError('Energy transfer does not match active parent')
            row['child_id'], row['child_energy'] = child.id, energy
        return child

    def step(self):
        try:
            super().step()
            self._finish_energy_action()
        finally:
            self._energy_action = None

    def drain_energy(self):
        records, self.energy_records = self.energy_records, []
        return records
