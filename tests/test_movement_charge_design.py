from dataclasses import asdict
from itertools import product
from pathlib import Path
import unittest
from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config
from scripts.run_v0_movement_charge import initialize


class MovementChargeDesignTests(unittest.TestCase):
    def test_all_eight_initial_treatments_match_and_observer_preserves_dynamics(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        founders=rng=None; maps={}
        for arm,threshold,cost in product(('dispersed','block'),(40,160),(0,1)):
            world=initialize(base,arm,threshold,cost,23)
            current=[asdict(o) for o in world.living.values()]
            if founders is None:founders=current; rng=world.rng.getstate()
            self.assertEqual(current,founders);self.assertEqual(world.rng.getstate(),rng)
            if arm not in maps:maps[arm]=list(world.food)
            self.assertEqual(list(world.food),maps[arm])
            self.assertEqual(sum(world.food),5120)
            self.assertEqual(world.config.movement_cost,cost)
            reference=World(world.config)
            reference.food[:]=world.food;reference.supplied_energy+=5120
            for o in reference.living.values():o.genome=250
            reference.events.clear()
            for tick in range(10):
                world.step();reference.step()
                self.assertEqual(world.snapshot(),reference.snapshot())
                self.assertEqual(world.food,reference.food)
                self.assertEqual(world.events,reference.events)
                self.assertEqual(world.rng.getstate(),reference.rng.getstate())
                self.assertEqual([asdict(o) for o in world.lineage.values()],
                                 [asdict(o) for o in reference.lineage.values()])
                rows=world.drain_energy();deaths=world.drain_pre_feeding_deaths();world.drain_feeding()
                if cost==0:
                    self.assertTrue(all(r['movement_paid']==0 for r in rows))
                    self.assertTrue(all(r['phase']!='movement' for r in deaths))
        self.assertEqual(sorted(maps['dispersed']),sorted(maps['block']))
