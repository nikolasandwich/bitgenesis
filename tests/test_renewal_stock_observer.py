from dataclasses import asdict
from itertools import product
from pathlib import Path
import unittest
from bitgenesis.v0.engine import World,Config
from bitgenesis.v0.runner import load_config
from scripts.run_v0_renewal_granularity import initialize,REGIMES
from scripts.observe_v0_renewal_stocks import capture,reconcile,check_engine


def state(world):
    return (world.snapshot(),list(world.food),dict(world.occupied),
            [asdict(o) for o in world.living.values()],
            [asdict(o) for o in world.lineage.values()],
            list(world.events),world.rng.getstate(),world.next_id)


class RenewalStockObserverTests(unittest.TestCase):
    def test_six_treatments_preserve_full_plain_engine_trajectory(self):
        check_engine()
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        for threshold,renewal in product((40,160),REGIMES):
            world=initialize(base,'block',threshold,renewal,23)
            plain=World(world.config)
            plain.food[:]=world.food;plain.supplied_energy+=5120
            for o in plain.living.values():o.genome=250
            plain.events.clear()
            for tick in range(100):
                before=world.snapshot();original=state(world)
                row=capture(world)
                self.assertEqual(state(world),original)
                world.step();plain.step()
                self.assertEqual(state(world),state(plain))
                checked=reconcile(row,before,world.snapshot())
                self.assertEqual(checked['uncapped_arrival_energy'],checked['admitted_energy']+checked['discarded_energy'])
                self.assertEqual(sum(row['histogram']),1024)
                world.drain_feeding();world.drain_pre_feeding_deaths();world.drain_energy()
                world.events.clear();plain.events.clear()

    def test_empty_and_near_full_worlds(self):
        for food in (0,23,24):
            for probability,amount in REGIMES.values():
                world=World(Config(seed=23,width=2,height=2,initial_population=0,
                    initial_food=food,regrowth_probability=probability,regrowth_amount=amount))
                for tick in range(100):
                    before=world.snapshot();original=state(world);row=capture(world)
                    self.assertEqual(state(world),original)
                    self.assertFalse(row['active_start'])
                    world.step();reconcile(row,before,world.snapshot())
                    if food==24:self.assertEqual(row['admitted_energy'],0)
