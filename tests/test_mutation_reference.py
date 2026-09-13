from fractions import Fraction
import unittest

from scripts.analyze_v0_mutation_reference import kernel_reference


class MutationReferenceTests(unittest.TestCase):
    def test_three_outcome_boundary_kernel(self):
        # At zero, {-1, 0, +1} becomes {0, 0, 1}; mutation attempted 1/10 births.
        self.assertEqual(kernel_reference(0, 100, 1), Fraction(1, 30))
        self.assertEqual(kernel_reference(1000, 100, 1), Fraction(-1, 30))
        self.assertEqual(kernel_reference(500, 100, 1), 0)

    def test_disabled_and_zero_step_have_no_reference_change(self):
        self.assertEqual(kernel_reference(1000, 0, 100), 0)
        self.assertEqual(kernel_reference(0, 1000, 0), 0)

    def test_default_kernel_matches_exact_boundary_calibration(self):
        self.assertEqual(kernel_reference(0, 100, 100), Fraction(505, 201))
        self.assertEqual(kernel_reference(1000, 100, 100), Fraction(-505, 201))
        self.assertEqual(kernel_reference(900, 100, 100), 0)


if __name__ == "__main__":
    unittest.main()
