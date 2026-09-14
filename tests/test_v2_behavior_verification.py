from fractions import Fraction
import unittest
from scripts.analyze_v2_study001 import probabilities,behavioral_difference


class IndependentSensitivityBehaviorTests(unittest.TestCase):
    def test_uniform_tickets_and_known_action_change(self):
        self.assertEqual(probabilities([0]*35,[0]*5,24),[Fraction(1,5)]*5)
        rest=[0]*35;rest[6]=1
        east=[0]*35;east[13]=1
        self.assertEqual(probabilities(rest,[0]*5,24),[1,0,0,0,0])
        self.assertEqual(behavioral_difference(rest,east),1)
        self.assertEqual(behavioral_difference(rest,rest),0)
