import unittest
from bitgenesis.v2.development import DevelopmentGenome
from scripts.run_v2_study001 import variants,build,compare


class V2SensitivityTests(unittest.TestCase):
    def test_full_neighborhood_keeps_clipped_duplicates(self):
        genome=DevelopmentGenome((0,0,0,0,0,0,0,0,0,1))
        rows=list(variants(genome))
        self.assertEqual(len(rows),20)
        self.assertEqual(len({(c,d) for c,d,g in rows}),20)
        self.assertEqual(rows[0][2],genome)
        self.assertGreater(sum(g==genome for c,d,g in rows),1)

    def test_invalid_behavior_is_null_and_valid_neutral_is_zero(self):
        invalid=build(DevelopmentGenome((0,0,0,0,0,0,0,0,0,1)))
        valid=build(DevelopmentGenome((6,100,0,0,0,0,0,0,1,2)))
        self.assertIsNone(compare(invalid,invalid)['behavior_mean_tv'])
        self.assertEqual(compare(invalid,valid)['validity_transition'],'invalid_to_valid')
        self.assertEqual(compare(valid,valid)['behavior_mean_tv'],'0')
        self.assertEqual(valid['development']['cost'],valid['direct_control']['cost'])
