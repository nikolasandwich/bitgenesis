from collections import Counter
from dataclasses import asdict
from copy import deepcopy
import hashlib
import json
import unittest

from bitgenesis.v0.engine import Config
from scripts.run_v0_geometry_threshold import initialize
from scripts.summarize_v0_geometry_threshold import verify_initial, early_observations


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


class GeometryThresholdVerificationTests(unittest.TestCase):
    def test_high_threshold_initial_state_and_wrong_threshold(self):
        world=initialize(Config(),"block",160,1400)
        initial=dict(arm="block",birth_threshold=160,seed=1400,config=asdict(world.config),
            food=world.food,founders=[asdict(o) for o in world.living.values()],
            snapshot=world.snapshot(),rng_sha256=hashlib.sha256(json.dumps(world.rng.getstate()).encode()).hexdigest())
        self.assertGreater(verify_initial(initial,"block",160,1400)["founders_on_food"],0)
        broken=deepcopy(initial);broken["config"]["birth_threshold"]=40
        with self.assertRaisesRegex(ValueError,"configuration"):
            verify_initial(broken,"block",160,1400)
        broken=deepcopy(initial);broken["rng_sha256"]="wrong"
        with self.assertRaisesRegex(ValueError,"RNG"):
            verify_initial(broken,"block",160,1400)

    def test_early_window_ties_and_uptake_use_only_declared_ticks(self):
        rows=[dict(tick=t,population=1,births=0,food_energy=10,
                   supplied_energy=210,organism_energy=200-t,dissipated_energy=t)
              for t in range(101)]
        # A synthetic bookkeeping sequence tests the helper, not world validity.
        rows[2]["population"]=2;rows[3]["population"]=2
        result=early_observations(rows)
        self.assertEqual(result["early_peak_population"],2)
        self.assertEqual(result["first_peak_tick"],2)
        self.assertEqual(result["food_eaten_by_100"],0)
        with self.assertRaisesRegex(ValueError,"window"):
            early_observations(rows[:100])
        rows[50]["food_energy"]+=1
        with self.assertRaisesRegex(ValueError,"uptake"):
            early_observations(rows)
