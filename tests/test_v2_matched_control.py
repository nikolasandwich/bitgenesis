import tempfile
from pathlib import Path
import unittest
import json
from bitgenesis.v2.development import DevelopmentGenome
from bitgenesis.v2.world import Config
from bitgenesis.v2.matched_control import paired_control


class MatchedWorldTests(unittest.TestCase):
    def test_same_phenotype_cost_and_trajectories_with_failed_children(self):
        with tempfile.TemporaryDirectory() as directory:
            genome=DevelopmentGenome((6,100,0,0,0,0,0,0,1,3))
            config=Config(width=5,height=5,founders=8,initial_energy=270,birth_threshold=160,
                          mutation_per_thousand=0)
            result=paired_control(Path(directory)/'pair',config,81400,80,genome)
            self.assertEqual(result['direct_padding_cost'],70)
            self.assertEqual(result['ticks_compared'],80)
            summary=json.loads((Path(directory)/'pair/developmental/summary.json').read_text())
            self.assertGreater(summary['failed_attempts'],0)

    def test_rejects_mutating_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                paired_control(Path(directory)/'pair',Config(),81401,5,
                               DevelopmentGenome((6,100,0,0,0,0,0,0,1,1)))
