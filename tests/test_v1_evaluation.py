import unittest
from fractions import Fraction
from pathlib import Path
import tempfile

from bitgenesis.v1.evaluation import action_distribution, sample_endpoint, total_variation
from bitgenesis.v1.runner import run
from bitgenesis.v1.world import Config


class EvaluationTests(unittest.TestCase):
    def test_exact_behavior_and_permutation_multiplicity(self):
        weights = [0]*35
        for action in range(1,5):
            weights[action*7+action] = 1
        values = [0,1000,0,0,0,500,1000]
        intact = action_distribution(weights,values)
        shuffled = action_distribution(weights,values,'shuffled')
        self.assertEqual(intact, (0,1,0,0,0))
        self.assertEqual(shuffled, (0,Fraction(1,4),Fraction(1,4),Fraction(1,4),Fraction(1,4)))
        self.assertEqual(total_variation(intact,shuffled), Fraction(3,4))
        self.assertEqual(action_distribution(weights,values,'blind'), (Fraction(1,5),)*5)
        equal = [1000]*5 + [500,1000]
        self.assertEqual(action_distribution(weights,equal), action_distribution(weights,equal,'shuffled'))
        self.assertEqual(action_distribution([0]*35,values,'shuffled'), (Fraction(1,5),)*5)

    def test_reproducible_read_only_samples_and_extinction(self):
        with tempfile.TemporaryDirectory() as directory:
            for founders in (0,6):
                root=Path(directory)/str(founders)
                run(root,Config(width=5,height=5,founders=founders,initial_energy=80),70300,5)
                before={p.name:p.read_bytes() for p in root.iterdir()}
                first=sample_endpoint(root,100,70301)
                self.assertEqual(first,sample_endpoint(root,100,70301))
                self.assertEqual(before,{p.name:p.read_bytes() for p in root.iterdir()})
                self.assertEqual(first['sample_count'],first['survivors'])
                self.assertEqual(len({s['id'] for s in first['samples']}),first['sample_count'])
                for sample in first['samples']:
                    self.assertEqual(sample['ancestry'][0],sample['id'])
                    self.assertEqual(sample['ancestry'][-1],sample['founder_id'])
                    self.assertIn(sample['founder_id'],range(founders))
                if not founders:
                    self.assertEqual(first['status'],'extinct')
                    self.assertIsNone(first['conditional_estimate'])
