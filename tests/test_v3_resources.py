import unittest

from bitgenesis.v3.resources import feed


class ResourceTests(unittest.TestCase):
    def test_exhaustive_small_stock_conservation_and_removal(self):
        for a in range(9):
            for b in range(9):
                for allocation in range(17):
                    for recycle in (True, False):
                        result = feed(a, b, 8, allocation, recycle=recycle)
                        self.assertEqual(a + b, result.remaining_a + result.remaining_b
                                         + result.energy_gain + result.dissipated)
                        self.assertTrue(0 <= result.remaining_a <= 8)
                        self.assertTrue(0 <= result.remaining_b <= 8)
                        self.assertLessEqual(result.consumed_a + result.consumed_b, 8)
                        self.assertLessEqual(result.consumed_b, b)
                        if not recycle:
                            self.assertEqual(result.released_b, 0)

    def test_new_byproduct_waits_and_partner_can_use_it(self):
        first = feed(8, 0, 24, 16)
        self.assertEqual((first.energy_gain, first.remaining_b, first.consumed_b), (4, 4, 0))
        second = feed(first.remaining_a, first.remaining_b, 24, 0)
        self.assertEqual((second.energy_gain, second.remaining_b, second.dissipated), (2, 0, 2))
        removed = feed(8, 0, 24, 16, recycle=False)
        self.assertEqual((removed.energy_gain, removed.remaining_b, removed.dissipated), (4, 0, 4))

    def test_overflow_and_no_unused_quota_transfer(self):
        self.assertEqual(feed(8, 8, 8, 16).dissipated, 4)
        self.assertEqual(feed(8, 0, 8, 0).consumed_a, 0)
        self.assertEqual(feed(1, 0, 8, 16).energy_gain, 0)

    def test_invalid_inputs(self):
        for args in ((-1, 0, 8, 0), (9, 0, 8, 0), (0, 0, 8, 17), (True, 0, 8, 0)):
            with self.assertRaises(ValueError):
                feed(*args)


if __name__ == '__main__':
    unittest.main()
