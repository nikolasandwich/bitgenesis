import copy
from dataclasses import asdict
import json
import unittest
from bitgenesis.v0.engine import Config
from scripts.observe_v0_local_resources import LocalResourceWorld
from scripts.replay_v0_local_resources import boundary
from scripts.verify_v0_local_actions import verify_actions


class LocalActionVerifierTests(unittest.TestCase):
    def fixture(self):
        c=Config(seed=23,width=8,height=8,initial_population=12,movement_cost=0,birth_cost=0)
        w=LocalResourceWorld(c)
        for a in w.living.values():a.genome=250
        boundaries=[boundary(w)];streams={k:[] for k in ('local','feeding','terminal','energy')}
        for _ in range(30):
            w.step();boundaries.append(boundary(w))
            for k,drain in [('local','drain_local_resources'),('feeding','drain_feeding'),('terminal','drain_pre_feeding_deaths'),('energy','drain_energy')]:streams[k].extend(getattr(w,drain)())
        return json.loads(json.dumps(boundaries)),streams,asdict(c)

    def test_valid_sequential_reconstruction(self):
        b,s,c=self.fixture();result=verify_actions(b,s,c)
        self.assertEqual(result['actions'],len(s['local']))
        self.assertGreater(sum(r['child_id'] is not None for r in s['feeding']),0)

    def test_local_food_occupant_and_order_corruption(self):
        b,s,c=self.fixture()
        for key,value in [('food',999),('occupant_id',999)]:
            bad=copy.deepcopy(s);bad['local'][0]['sites'][0][key]=value
            with self.assertRaisesRegex(ValueError,'snapshot'):verify_actions(b,bad,c)
        bad=copy.deepcopy(s);bad['local'][0],bad['local'][1]=bad['local'][1],bad['local'][0]
        with self.assertRaisesRegex(ValueError,'order'):verify_actions(b,bad,c)

    def test_food_write_and_energy_corruption(self):
        b,s,c=self.fixture();bad=copy.deepcopy(s);bad['feeding'][0]['food_before']+=1
        with self.assertRaisesRegex(ValueError,'food write'):verify_actions(b,bad,c)
        bad=copy.deepcopy(s);bad['energy'][0]['child_energy']+=1
        with self.assertRaisesRegex(ValueError,'energy'):verify_actions(b,bad,c)
