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
                for r in records:
                    self.assertEqual(r["tick"],tick+1)
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
