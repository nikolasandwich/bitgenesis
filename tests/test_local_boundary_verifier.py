import copy
from dataclasses import asdict
import unittest
from bitgenesis.v0.engine import Config
from scripts.observe_v0_local_resources import LocalResourceWorld
from scripts.replay_v0_local_resources import boundary
from scripts.verify_v0_local_boundaries import verify_boundary


class LocalBoundaryVerifierTests(unittest.TestCase):
    def fixture(self):
        world=LocalResourceWorld(Config(seed=23,width=8,height=8,initial_population=12))
        for actor in world.living.values():actor.genome=250
        for _ in range(20):world.step()
        import json
        row=json.loads(json.dumps(boundary(world)))
        return row,world.snapshot(),asdict(world.config)

    def test_valid_boundary_and_spatial_corruptions(self):
        row,metric,config=self.fixture();verify_boundary(row,metric,config)
        bad=copy.deepcopy(row);bad['food'][0]+=1
        with self.assertRaisesRegex(ValueError,'food'):verify_boundary(bad,metric,config)
        bad=copy.deepcopy(row);bad['occupied'][0][0]=(bad['occupied'][0][0]+1)%64
        with self.assertRaisesRegex(ValueError,'occupancy'):verify_boundary(bad,metric,config)
        bad=copy.deepcopy(row);bad['living'][0]['energy']+=1
        with self.assertRaisesRegex(ValueError,'accounting'):verify_boundary(bad,metric,config)
        bad=copy.deepcopy(row);bad['living'][1]['id']=bad['living'][0]['id']
        with self.assertRaisesRegex(ValueError,'individual'):verify_boundary(bad,metric,config)
