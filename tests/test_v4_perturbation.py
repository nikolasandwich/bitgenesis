import unittest
from bitgenesis.v4.local import Unit
from bitgenesis.v4.perturbation import remove
from bitgenesis.v4.recovery import observe


class PerturbationTests(unittest.TestCase):
    def test_exports_and_no_recycling_or_input_mutation(self):
        units = [Unit(0, 5), None, Unit(2, 0), Unit(1, 9)]
        raw = [1, 2, 3, 4]
        after, stock, row = remove(units, raw, [2, 1, 0])
        self.assertEqual(after, [None, None, None, Unit(1, 9)])
        self.assertEqual(stock, raw)
        self.assertEqual(row['exported_material'], 2)
        self.assertEqual(row['exported_energy'], 5)
        self.assertEqual(row['material_before']-row['material_after'], 2)
        self.assertEqual(row['energy_before']-row['energy_after'], 5)
        self.assertEqual(units[0], Unit(0, 5))
        self.assertEqual(remove(units, raw, [0, 1, 2]), (after, stock, row))
        self.assertEqual(remove(units, raw, [])[0], units)
        for sites in ([0, 0], [-1], [True], [4]):
            with self.assertRaises(ValueError):
                remove(units, raw, sites)

    def test_refill_is_not_material_pattern_recovery(self):
        reference = [Unit(0, 5), Unit(1, 5), None]
        current = [Unit(2, 5), Unit(1, 8), Unit(3, 9)]
        row = observe(reference, current, [0, 1, 2])
        self.assertEqual(row['occupied_fraction'], '1')
        self.assertEqual(row['refill_fraction'], '1')
        self.assertEqual(row['material_match_fraction'], '1/2')
        self.assertIsNone(observe(reference, current, [2])['refill_fraction'])
        self.assertIsNone(observe(reference, current, [])['occupied_fraction'])
        self.assertEqual(observe(reference, [None]*3, [0, 1])['material_match_fraction'], '0')
        with self.assertRaises(ValueError):
            observe(reference, current, [0, 0])
