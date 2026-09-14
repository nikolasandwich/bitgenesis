import copy
from dataclasses import asdict
from pathlib import Path
import unittest
from bitgenesis.v0.runner import load_config
from scripts.run_v0_movement_charge import initialize
from scripts.verify_v0_movement_charge_observations import verify_early


class MovementChargeObservationTests(unittest.TestCase):
    def fixture(self,cost=0):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        world=initialize(base,'dispersed',40,cost,23)
        initial=dict(config=asdict(world.config),founders=[asdict(o) for o in world.living.values()])
        metrics=[world.snapshot()];streams={k:[] for k in ('feeding','terminal','energy')}
        for tick in range(100):
            world.step();metrics.append(world.snapshot())
            for kind,rows in (('feeding',world.drain_feeding()),('terminal',world.drain_pre_feeding_deaths()),('energy',world.drain_energy())):
                streams[kind].extend(rows)
        return initial,metrics,streams

    def test_both_costs_reconstruct_lifecycle_and_energy(self):
        for cost in (0,1):
            result=verify_early(*self.fixture(cost))
            self.assertGreater(result['counts']['energy'],0)
            if cost==0:self.assertEqual(result['counts']['movement_payment_deaths'],0)

    def test_corrupt_energy_and_duplicate_actor_are_rejected(self):
        initial,metrics,streams=self.fixture()
        bad=copy.deepcopy(streams);bad['energy'][0]['energy_after_action']+=1
        with self.assertRaisesRegex(ValueError,'energy ledger'):
            verify_early(initial,metrics,bad)
        bad=copy.deepcopy(streams);bad['energy'].append(bad['energy'][0])
        with self.assertRaisesRegex(ValueError,'partition'):
            verify_early(initial,metrics,bad)

    def test_wrong_founder_and_teleportation_are_rejected(self):
        initial,metrics,streams=self.fixture()
        bad=copy.deepcopy(streams);bad['feeding'][0]['founder_id']=999
        with self.assertRaisesRegex(ValueError,'Founder'):
            verify_early(initial,metrics,bad)
        bad=copy.deepcopy(streams)
        row=next(r for r in bad['feeding'] if r['moved'])
        row['position']=(row['position_before_action']+64)%1024
        with self.assertRaisesRegex(ValueError,'displacement'):
            verify_early(initial,metrics,bad)
