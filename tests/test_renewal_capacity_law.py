from fractions import Fraction
import unittest
from scripts.calibrate_v0_renewal_capacity import law,REGIMES


class RenewalCapacityLawTests(unittest.TestCase):
    def test_exact_moments_against_all_discrete_draws(self):
        for stock in range(25):
            for probability,amount in REGIMES.values():
                # Enumerate the engine's integer draw and capped next stock.
                draws=[min(24,stock+amount)-stock if draw<probability else 0 for draw in range(1000)]
                mean=Fraction(sum(draws),1000)
                variance=sum((Fraction(x)-mean)**2 for x in draws)/1000
                result=law(stock,probability,amount)
                self.assertEqual(result['mean'],mean)
                self.assertEqual(result['variance'],variance)
                self.assertEqual(result['positive_probability'],Fraction(sum(x>0 for x in draws),1000))

    def test_full_and_one_unit_capacity(self):
        self.assertEqual(law(24,60,1)['mean'],0)
        self.assertEqual(law(23,5,12)['mean'],Fraction(1,200))
        self.assertEqual(law(23,5,12)['lost_nominal_mean'],Fraction(11,200))
        for args in ((True,60,1),(25,60,1),(0,1001,1),(0,60,0)):
            with self.assertRaises(ValueError):law(*args)
