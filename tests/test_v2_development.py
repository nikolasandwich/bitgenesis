import unittest
from bitgenesis.v2.development import DevelopmentGenome, develop


class DevelopmentTests(unittest.TestCase):
    def test_local_diffusion_and_synchronous_growth(self):
        genome=DevelopmentGenome((17,80,0,0,0,0,1,0,1,1))
        result=develop(genome,100)
        self.assertTrue(result.valid)
        self.assertEqual(result.weights[17],60)
        self.assertEqual({i:result.weights[i] for i in result.active_sites}, {10:5,16:5,17:60,18:5,24:5})
        self.assertEqual(result.cost,40)
        self.assertEqual(result,develop(genome,100))

    def test_cost_boundaries_and_no_partial_viable_structure(self):
        genome=DevelopmentGenome((17,80,0,0,0,0,1,0,1,1))
        for budget,reason,cost in ((34,'round_budget',0),(39,'expression_budget',35),(40,'developed',40)):
            result=develop(genome,budget)
            self.assertEqual((result.reason,result.cost),(reason,cost))
            self.assertLessEqual(result.cost,budget)
            self.assertEqual(result.valid,budget==40)
            if not result.valid:
                self.assertEqual(result.weights,(0,)*35)

    def test_empty_structure_and_inherited_parameter_effect(self):
        empty=develop(DevelopmentGenome((0,0,0,0,0,0,1,0,1,2)),100)
        self.assertFalse(empty.valid)
        self.assertEqual(empty.reason,'empty_structure')
        a=develop(DevelopmentGenome((17,80,0,0,0,0,0,0,1,1)),100)
        b=develop(DevelopmentGenome((17,80,0,0,0,0,1,0,1,1)),100)
        self.assertEqual(len(a.active_sites),1)
        self.assertEqual(len(b.active_sites),5)

    def test_signed_symmetry_and_bounds(self):
        positive=develop(DevelopmentGenome((0,100,17,80,34,60,4,1,1,8)),1000)
        negative=develop(DevelopmentGenome((0,-100,17,-80,34,-60,4,1,1,8)),1000)
        self.assertEqual(positive.weights,tuple(-v for v in negative.weights))
        self.assertTrue(all(-100<=v<=100 for row in positive.history for v in row))
