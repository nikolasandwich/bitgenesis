import copy
from dataclasses import asdict
import json
import unittest
from bitgenesis.v0.engine import Config
from scripts.observe_v0_local_resources import LocalResourceWorld
from scripts.replay_v0_local_resources import boundary
from scripts.verify_v0_local_random_choices import verify_random_choices


class LocalRandomChoicesTests(unittest.TestCase):
    def fixture(self,cost=0):
        c=Config(seed=23,width=8,height=8,initial_population=12,movement_cost=cost,birth_cost=0,mutation_probability=0)
        w=LocalResourceWorld(c)
        for a in w.living.values():a.genome=250
        b=[boundary(w)];s={k:[] for k in ('local','feeding','terminal','energy')}
        for _ in range(30):
            w.step();b.append(boundary(w))
            for k,drain in [('local','drain_local_resources'),('feeding','drain_feeding'),('terminal','drain_pre_feeding_deaths'),('energy','drain_energy')]:s[k].extend(getattr(w,drain)())
        return json.loads(json.dumps(b)),s,asdict(c)

    def test_valid_random_draw_sequences(self):
        for cost in (0,1):
            b,s,c=self.fixture(cost)
            self.assertEqual(verify_random_choices(b,s,c)['random_ticks_checked'],30)

    def test_changed_boundary_rng_rejected(self):
        b,s,c=self.fixture();bad=copy.deepcopy(b)
        bad[-1]['rng_state'][1][-1]=(bad[-1]['rng_state'][1][-1]+1)%624
        with self.assertRaisesRegex(ValueError,'Random ending'):verify_random_choices(bad,s,c)
        bad=copy.deepcopy(b);bad[0]['rng_state']=copy.deepcopy(b[1]['rng_state'])
        with self.assertRaisesRegex(ValueError,'Random'):verify_random_choices(bad,s,c)
