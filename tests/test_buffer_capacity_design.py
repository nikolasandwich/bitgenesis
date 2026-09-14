from dataclasses import asdict
from itertools import product
from pathlib import Path
import unittest
from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config
from scripts.run_v0_buffer_capacity import initialize, REGIMES
from scripts.verify_v0_movement_charge_observations import verify_early


class BufferCapacityDesignTests(unittest.TestCase):
    def test_all_twelve_initial_treatments_match_and_observer_preserves_dynamics(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        founders=rng=None; maps={}
        for arm,threshold,renewal,capacity in product(('block',),(40,160),REGIMES,(24,96)):
            world=initialize(base,arm,threshold,renewal,capacity,23)
            current=[asdict(o) for o in world.living.values()]
            if founders is None:founders=current; rng=world.rng.getstate()
            self.assertEqual(current,founders);self.assertEqual(world.rng.getstate(),rng)
            if arm not in maps:maps[arm]=list(world.food)
            self.assertEqual(list(world.food),maps[arm])
            self.assertEqual(sum(world.food),5120)
            self.assertEqual(world.config.food_capacity,capacity)
            self.assertEqual(world.snapshot()["supplied_energy"],7040)
            self.assertEqual(world.config.movement_cost,0)
            self.assertEqual(world.config.birth_cost,0)
            self.assertEqual((world.config.regrowth_probability,world.config.regrowth_amount),REGIMES[renewal])
            self.assertEqual(world.config.regrowth_probability*world.config.regrowth_amount,60)
            initial=dict(config=asdict(world.config),founders=current)
            metrics=[world.snapshot()];streams={k:[] for k in ("feeding","terminal","energy")}
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
                rows=world.drain_energy();deaths=world.drain_pre_feeding_deaths();feeds=world.drain_feeding()
                metrics.append(world.snapshot())
                streams["feeding"].extend(feeds);streams["terminal"].extend(deaths);streams["energy"].extend(rows)
                self.assertTrue(all(r['movement_paid']==0 for r in rows))
                self.assertTrue(all(r['phase']!='movement' for r in deaths))
                self.assertTrue(all(r['birth_paid']==0 for r in rows))
            checked=verify_early(initial,metrics,streams)
            self.assertEqual(checked['counts']['energy'],len(streams['energy']))


    def test_regrowth_is_capped_before_feeding_for_each_capacity(self):
        from bitgenesis.v0.engine import Config
        from scripts.observe_v0_energy import EnergyWorld
        for capacity,amount,remaining in product((24,96),(1,4,12),(0,1)):
            config=Config(seed=23,width=2,height=2,initial_population=1,initial_energy=1,
                food_capacity=capacity,initial_food=capacity-remaining,
                regrowth_probability=1000,regrowth_amount=amount,movement_cost=0,birth_cost=0)
            world=EnergyWorld(config);before=world.snapshot()
            world.step();after=world.snapshot()
            self.assertEqual(world.food,[capacity]*4)
            self.assertEqual(after['supplied_energy']-before['supplied_energy'],4*remaining)
            self.assertEqual(world.drain_feeding(),[])
            self.assertEqual(after['population'],0)
