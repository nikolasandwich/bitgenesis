from statistics import NormalDist
import unittest

from scripts.analyze_v0_survival_uncertainty import wilson


class SurvivalUncertaintyTests(unittest.TestCase):
    def test_endpoints_invert_binomial_score_equation(self):
        z_squared = NormalDist().inv_cdf(0.975) ** 2
        for trials in (1, 10, 100):
            for successes in range(trials + 1):
                lower, upper = wilson(successes, trials)
                self.assertLessEqual(lower, successes / trials)
                self.assertGreaterEqual(upper, successes / trials)
                for bound in (lower, upper):
                    if 0 < bound < 1:
                        score_squared = (successes - trials * bound) ** 2 / (trials * bound * (1 - bound))
                        self.assertAlmostEqual(score_squared, z_squared, places=10)
        self.assertEqual(wilson(0, 10)[0], 0)
        self.assertEqual(wilson(10, 10)[1], 1)

    def test_invalid_counts_are_rejected(self):
        for successes, trials in ((0, 0), (-1, 10), (11, 10), (1.0, 10), (True, 10)):
            with self.subTest(successes=successes, trials=trials), self.assertRaises(ValueError):
                wilson(successes, trials)
