from collections import Counter
from dataclasses import asdict
import unittest

from bitgenesis.v0.engine import Config
from scripts.run_v0_geometry_threshold import initialize


class GeometryThresholdTests(unittest.TestCase):
    def test_all_declared_initial_quadruplets_are_paired(self):
        for seed in range(1400,1410):
            worlds={(arm,threshold):initialize(Config(),arm,threshold,seed)
                    for arm in ("dispersed","block") for threshold in (40,160)}
            reference=worlds["dispersed",40]
            for (arm,threshold),world in worlds.items():
                with self.subTest(seed=seed,arm=arm,threshold=threshold):
                    self.assertEqual(world.rng.getstate(),reference.rng.getstate())
                    self.assertEqual([asdict(o) for o in world.living.values()],
                                     [asdict(o) for o in reference.living.values()])
                    self.assertEqual(world.food,worlds[arm,40].food)
                    self.assertEqual(Counter(world.food),Counter({0:810,24:213,8:1}))
                    self.assertEqual(world.supplied_energy,7040)
                    self.assertEqual(world.config.birth_threshold,threshold)
                    self.assertEqual(world.config.regrowth_probability,15)
                    self.assertEqual(world.config.mutation_probability,0)
                    self.assertEqual({o.genome for o in world.living.values()},{250})

    def test_undeclared_treatments_are_rejected(self):
        for arm,threshold in (("uniform",40),("block",80)):
            with self.assertRaises(ValueError):
                initialize(Config(),arm,threshold,1400)
