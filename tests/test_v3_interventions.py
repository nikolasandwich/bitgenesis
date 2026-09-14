from copy import deepcopy
import unittest

from bitgenesis.v2.development import DevelopmentGenome
from bitgenesis.v3.genome import EcologyGenome
from bitgenesis.v3.interventions import boundary
from bitgenesis.v3.runner import state
from bitgenesis.v3.world import Config, World


class InterventionTests(unittest.TestCase):
    def world(self):
        genome=EcologyGenome(DevelopmentGenome((6,100,0,0,0,0,0,0,1,1)),16)
        world=World(Config(width=5,height=5,founders=2,initial_energy=400,birth_threshold=160),85500,
                    founder_genomes=[genome]*2)
        world.step()
        return world

    def test_remove_descendants_preserve_deposits_and_random_state(self):
        world=self.world()
        original=deepcopy(world)
        removed_ids={i for i,o in world.organisms.items() if o.founder==0}
        self.assertGreater(len(removed_ids),1)
        pools=list(world.substrate_b)
        random_states={n:r.getstate() for n,r in world.rng.items()}
        record=boundary(world,remove_founder=0)
        self.assertEqual({o['id'] for o in record['removed']},removed_ids)
        self.assertEqual(world.substrate_b,pools)
        self.assertEqual(random_states,{n:r.getstate() for n,r in world.rng.items()})
        self.assertTrue(all(world.lineage[i].energy==0 for i in removed_ids))
        self.assertTrue(all(i in original.organisms for i in removed_ids))
        world.step()  # The normal next-step ledger remains internally consistent.

    def test_import_clipping_order_and_atomic_validation(self):
        world=self.world()
        before=state(world)
        with self.assertRaises(ValueError):
            boundary(world,remove_founder=0,b_additions=[(0,3),(-1,1)])
        self.assertEqual(state(world),before)
        record=boundary(world,b_additions=[(0,24),(0,5)])
        self.assertEqual(world.substrate_b[0],24)
        self.assertEqual(record['b_deposits'][1]['accepted'],0)
        self.assertEqual(record['b_deposits'][1]['rejected'],5)
        self.assertEqual(record['energy_after'],record['energy_before']+record['imported_energy'])


if __name__=='__main__':
    unittest.main()
