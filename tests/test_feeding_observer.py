from dataclasses import asdict
import unittest
from unittest.mock import patch

from bitgenesis.v0.engine import Config,World
from scripts.observe_v0_feeding import FeedingWorld


class FeedingObserverTests(unittest.TestCase):
    def test_observation_preserves_world_and_reconciles_food(self):
        cases=[Config(seed=s,width=8,height=8,initial_population=12) for s in (1,2,3)]
        cases += [Config(width=2,height=2,initial_population=4,initial_food=24),
                  Config(width=2,height=2,initial_population=4,initial_energy=1),
                  Config(width=2,height=2,initial_population=4,initial_energy=2,initial_food=0)]
        total=0
        for config in cases:
            observed,reference=FeedingWorld(config),World(config)
            for tick in range(100):
                previous=observed.snapshot()
                observed.step();reference.step()
                records=observed.drain_feeding();total+=len(records)
                self.assertEqual(observed.snapshot(),reference.snapshot())
                self.assertEqual(observed.food,reference.food)
                self.assertEqual(observed.events,reference.events)
                self.assertEqual(observed.rng.getstate(),reference.rng.getstate())
                self.assertEqual([asdict(o) for o in observed.lineage.values()],
                                 [asdict(o) for o in reference.lineage.values()])
                now=observed.snapshot()
                self.assertEqual(sum(r["eaten"] for r in records),
                    now["supplied_energy"]-previous["supplied_energy"]+
                    previous["food_energy"]-now["food_energy"])
                self.assertEqual(len({r["id"] for r in records}),len(records))
                self.assertEqual(sum(r["child_id"] is not None for r in records),now["births"]-previous["births"])
                for r in records:
                    self.assertEqual(r["tick"],tick+1)
                    self.assertEqual(r["child_id"] is not None, r["birth_eligible"] and r["empty_neighbors_before_birth"]>0)
                    if r["child_id"] is not None:
                        self.assertEqual(observed.lineage[r["child_id"]].parent_id,r["id"])
                    self.assertGreater(r["energy_before_feeding"],0)
                    self.assertEqual(r["eaten"],min(config.feeding_rate,r["food_before"]))
                    self.assertLess(observed.lineage[r["id"]].birth_tick,r["tick"])
            self.assertEqual(observed.drain_feeding(),[])
        self.assertGreater(total,0)

    def test_death_before_feeding_and_zero_intake(self):
        dead=FeedingWorld(Config(width=2,height=2,initial_population=4,initial_energy=1))
        dead.step();self.assertEqual(dead.drain_feeding(),[])
        empty=FeedingWorld(Config(width=2,height=2,initial_population=4,initial_food=0,regrowth_probability=0))
        empty.step();records=empty.drain_feeding()
        self.assertEqual(len(records),4);self.assertEqual(sum(r["eaten"] for r in records),0)

    def test_changed_engine_or_replaced_food_fails_explicitly(self):
        with patch("scripts.observe_v0_feeding.ENGINE_SHA256","unsupported"):
            with self.assertRaisesRegex(ValueError,"pinned"):
                FeedingWorld(Config())
        world=FeedingWorld(Config());world.food=list(world.food)
        with self.assertRaisesRegex(ValueError,"replace"):
            world.step()


    def test_eligible_full_world_has_no_birth_space(self):
        world=FeedingWorld(Config(width=2,height=2,initial_population=4,initial_energy=40,initial_food=24))
        world.step();records=world.drain_feeding()
        self.assertEqual(len(records),4)
        self.assertTrue(all(r["birth_eligible"] and r["empty_neighbors_before_birth"]==0 and r["child_id"] is None for r in records))

    def test_eligible_parent_with_space_records_actual_child(self):
        world=FeedingWorld(Config(width=3,height=3,initial_population=1,initial_energy=40,initial_food=24))
        world.step();records=world.drain_feeding()
        self.assertEqual(len(records),1)
        row=records[0];self.assertEqual(row["child_id"],1)
        self.assertTrue(row["birth_eligible"])
        self.assertEqual(row["empty_neighbors_before_birth"],4)
        self.assertEqual(world.lineage[1].birth_tick,1)


    def test_movement_outcomes_in_full_and_single_occupancy_worlds(self):
        for population,genome,attempted,moved in ((4,1000,True,False),(1,1000,True,True),(1,0,False,False)):
            config=Config(width=2,height=2,initial_population=population,initial_energy=40,initial_food=24)
            observed,reference=FeedingWorld(config),World(config)
            for world in (observed,reference):
                for o in world.living.values():o.genome=genome
            observed.step();reference.step();records=observed.drain_feeding()
            self.assertEqual(observed.snapshot(),reference.snapshot())
            self.assertEqual(observed.events,reference.events)
            self.assertEqual(observed.rng.getstate(),reference.rng.getstate())
            for row in records:
                self.assertEqual(row["movement_attempted"],attempted)
                self.assertEqual(row["moved"],moved)
                self.assertEqual(row["position"]!=row["position_before_action"],moved)

    def test_lethal_movement_is_not_counted_as_a_feeding_attempt(self):
        world=FeedingWorld(Config(width=2,height=2,initial_population=1,initial_energy=2))
        world.living[0].genome=1000
        world.step()
        self.assertEqual(world.snapshot()["deaths"],1)
        self.assertEqual(world.drain_feeding(),[])
