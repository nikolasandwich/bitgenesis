from dataclasses import asdict
from itertools import product
from pathlib import Path
import unittest
from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config
from scripts.run_v0_renewal_granularity import initialize, REGIMES


class RenewalGranularityDesignTests(unittest.TestCase):
    def test_all_six_initial_treatments_match_and_observer_preserves_dynamics(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        founders=rng=None; maps={}
        for arm,threshold,renewal in product(('block',),(40,160),REGIMES):
            world=initialize(base,arm,threshold,renewal,23)
            current=[asdict(o) for o in world.living.values()]
            if founders is None:founders=current; rng=world.rng.getstate()
            self.assertEqual(current,founders);self.assertEqual(world.rng.getstate(),rng)
            if arm not in maps:maps[arm]=list(world.food)
            self.assertEqual(list(world.food),maps[arm])
            self.assertEqual(sum(world.food),5120)
            self.assertEqual(world.config.movement_cost,0)
            self.assertEqual(world.config.birth_cost,0)
            self.assertEqual((world.config.regrowth_probability,world.config.regrowth_amount),REGIMES[renewal])
            self.assertEqual(world.config.regrowth_probability*world.config.regrowth_amount,60)
            reference=World(world.config)
            reference.food[:]=world.food;reference.supplied_energy+=5120
            for o in reference.living.values():o.genome=250
            reference.events.clear()
            for tick in range(100):
                world.step();reference.step()
                self.assertEqual(world.snapshot(),reference.snapshot())
                self.assertEqual(world.food,reference.food)
                self.assertEqual(world.events,reference.events)
                self.assertEqual(world.rng.getstate(),reference.rng.getstate())
                self.assertEqual([asdict(o) for o in world.lineage.values()],
                                 [asdict(o) for o in reference.lineage.values()])
                rows=world.drain_energy();deaths=world.drain_pre_feeding_deaths();world.drain_feeding()
                self.assertTrue(all(r['movement_paid']==0 for r in rows))
                self.assertTrue(all(r['phase']!='movement' for r in deaths))
                self.assertTrue(all(r['birth_paid']==0 for r in rows))


    def test_regrowth_is_capped_before_feeding_for_each_packet(self):
        from dataclasses import replace
        from bitgenesis.v0.engine import Config
        from scripts.observe_v0_energy import EnergyWorld
        for probability,amount in REGIMES.values():
            config=Config(seed=23,width=2,height=2,initial_population=1,initial_energy=1,
                initial_food=23,regrowth_probability=1000,regrowth_amount=amount,movement_cost=0,birth_cost=0)
            world=EnergyWorld(config);before=world.snapshot()
            world.step();after=world.snapshot()
            self.assertEqual(world.food,[24]*4)
            self.assertEqual(after['supplied_energy']-before['supplied_energy'],4)
            self.assertEqual(world.drain_feeding(),[])
            self.assertEqual(after['population'],0)
