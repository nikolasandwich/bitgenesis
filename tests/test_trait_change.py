from fractions import Fraction
import unittest

from scripts.analyze_v0_trait_change import components


class TraitChangeTests(unittest.TestCase):
    def test_birth_death_and_mutation_have_separate_contributions(self):
        # [100, 300] becomes [300, 350]: high-trait parent births, low trait dies.
        self.assertEqual(components(2, 400, [300], [350], [100]),
                         (Fraction(50), Fraction(50), Fraction(25), Fraction(125)))

    def test_population_growth_uses_new_population_denominator(self):
        # [100, 300] becomes [100, 300, 300], mean increases by 100/3.
        self.assertEqual(components(2, 400, [300], [300], []),
                         (Fraction(100, 3), Fraction(0), Fraction(0), Fraction(100, 3)))

    def test_death_only_and_no_event_boundaries(self):
        self.assertEqual(components(2, 400, [], [], [100]), (0, 100, 0, 100))
        self.assertEqual(components(2, 400, [], [], []), (0, 0, 0, 0))

    def test_extinction_has_no_defined_mean(self):
        with self.assertRaisesRegex(ValueError, "extinction"):
            components(1, 100, [], [], [100])


if __name__ == "__main__":
    unittest.main()
