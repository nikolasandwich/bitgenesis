import unittest
from scripts.probe_v1_study001 import probe_states, probe_genome


class StudyProbeTests(unittest.TestCase):
    def test_exact_registered_states_and_occupancy_duplicates(self):
        states=list(probe_states())
        self.assertEqual(len(states),32)
        self.assertEqual(len({(tuple(s['food']),s['post_charge_energy']) for s in states}),32)
        self.assertEqual({s['post_charge_energy'] for s in states},{1,24,80,160})
        result=probe_genome([0]*35)
        self.assertEqual(result['mean_total_variation'],{'blind':'0','shuffled':'0'})
        for first,second in zip(result['states'][::2],result['states'][1::2]):
            self.assertFalse(first['occupied_east'])
            self.assertTrue(second['occupied_east'])
            self.assertEqual(first['probabilities'],second['probabilities'])
            self.assertEqual(first['probabilities']['intact'],['1/5']*5)
