from dataclasses import asdict
import unittest
from bitgenesis.v0.engine import Config
from scripts.observe_v0_feeding import FeedingWorld
from scripts.observe_v0_energy import EnergyWorld


class EnergyObserverTests(unittest.TestCase):
    def test_ledger_preserves_old_observations_and_world(self):
        cases = [Config(seed=s,width=8,height=8,initial_population=12) for s in (1,2,3)]
        cases += [Config(seed=4,width=8,height=8,initial_population=12,movement_cost=0),
                  Config(width=2,height=2,initial_population=4,initial_energy=40,movement_cost=0),
                  Config(width=2,height=2,initial_population=4,initial_energy=40),
                  Config(width=2,height=2,initial_population=1,initial_energy=2,basal_cost=5),
                  Config(width=2,height=2,initial_population=1,initial_energy=3,movement_cost=9)]
        for config in cases:
            with self.subTest(config=config):
                observed, reference = EnergyWorld(config), FeedingWorld(config)
                for world in (observed, reference):
                    for organism in world.living.values():
                        organism.genome = 1000
                for tick in range(100):
                    before = observed.snapshot()
                    actors = {i:o.energy for i,o in observed.living.items()}
                    observed.step(); reference.step()
                    rows = observed.drain_energy()
                    self.assertEqual({r['id'] for r in rows}, set(actors))
                    self.assertEqual(len(rows), len(actors))
                    self.assertEqual(observed.drain_feeding(), reference.drain_feeding())
                    self.assertEqual(observed.drain_pre_feeding_deaths(), reference.drain_pre_feeding_deaths())
                    self.assertEqual(observed.snapshot(), reference.snapshot())
                    self.assertEqual(observed.food, reference.food)
                    self.assertEqual(observed.events, reference.events)
                    self.assertEqual(observed.rng.getstate(), reference.rng.getstate())
                    self.assertEqual([asdict(o) for o in observed.lineage.values()],
                                     [asdict(o) for o in reference.lineage.values()])
                    after = observed.snapshot()
                    costs = sum(r[k] for r in rows for k in ('basal_paid','movement_paid','birth_paid'))
                    self.assertEqual(costs, after['dissipated_energy']-before['dissipated_energy'])
                    self.assertEqual(sum(r['eaten'] for r in rows),
                        after['supplied_energy']-before['supplied_energy']+before['food_energy']-after['food_energy'])
                    self.assertEqual(sum(r['energy_after_action']+r['child_energy'] for r in rows), after['organism_energy'])
                    for r in rows:
                        self.assertEqual(r['energy_before_action'], actors[r['id']])
                        self.assertEqual(r['energy_after_action'], observed.lineage[r['id']].energy)
                        if r['child_id'] is not None:
                            child = observed.lineage[r['child_id']]
                            self.assertEqual((child.parent_id,child.energy),(r['id'],r['child_energy']))
                self.assertEqual(observed.drain_energy(), [])

    def test_odd_split_and_zero_costs_are_actual_transfers(self):
        world = EnergyWorld(Config(width=3,height=3,initial_population=1,initial_energy=42,
                                   initial_food=0,regrowth_probability=0,movement_cost=0,birth_cost=0))
        world.living[0].genome = 1000
        world.step(); row, = world.drain_energy()
        self.assertEqual((row['basal_paid'],row['movement_paid'],row['birth_paid']),(1,0,0))
        self.assertEqual((row['energy_after_action'],row['child_energy']),(21,20))
        self.assertFalse(row['died'])

    def test_lethal_payment_records_actual_amount_not_requested_cost(self):
        for basal,movement,expected in ((5,1,(3,0)),(1,9,(1,2))):
            world = EnergyWorld(Config(width=2,height=2,initial_population=1,initial_energy=3,
                                       basal_cost=basal,movement_cost=movement))
            world.living[0].genome = 1000
            world.step(); row, = world.drain_energy()
            self.assertEqual((row['basal_paid'],row['movement_paid']),expected)
            self.assertEqual((row['eaten'],row['energy_after_action'],row['child_energy']),(0,0,0))
            self.assertTrue(row['died'])
