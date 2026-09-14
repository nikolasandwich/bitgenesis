import random
import unittest

from bitgenesis.v4.growing import step
from bitgenesis.v4.local import Unit


class GrowingTests(unittest.TestCase):
    def test_newborn_input_waits_and_components_precede_conversion(self):
        units = [Unit(2, 24)] + [None] * 8
        raw = [1] * 9
        after, remaining, row = step(units, raw, 3, 3, [8] * 9, [0] * 9)
        self.assertEqual(after[:3], [Unit(2, 14), Unit(2, 13), None])
        self.assertEqual(row['imported'], 8)
        self.assertEqual(row['rejected_import'], 64)
        self.assertEqual(row['spent'], 5)
        self.assertEqual(row['interaction_components'], [[0]])
        self.assertIsNone(row['interaction_units'][1])
        self.assertEqual(remaining[1], 0)
        self.assertEqual(units[0], Unit(2, 24))
        self.assertEqual(raw, [1] * 9)

    def test_bond_exhaustion_dissolves_after_interaction(self):
        units = [Unit(1, 1), Unit(1, 1)] + [None] * 7
        after, raw, row = step(units, [0] * 9, 3, 3, [0] * 9, [0] * 9, leak=0)
        self.assertEqual(after, [None] * 9)
        self.assertEqual(raw[:2], [1, 1])
        self.assertEqual(row['interaction_components'], [[0, 1]])
        self.assertEqual(row['material']['dissolved'], [0, 1])
        self.assertEqual(row['spent'], 2)

    def test_input_can_rescue_initial_zero_before_dissolution(self):
        units = [Unit(1, 0)] + [None] * 8
        after, raw, row = step(units, [0] * 9, 3, 3, [8] * 9, [0] * 9)
        self.assertEqual(after[0], Unit(1, 7))
        self.assertEqual(row['material']['dissolved'], [])
        self.assertEqual(sum(raw), 0)

    def test_closed_positive_leak_eventually_returns_all_material(self):
        units = [Unit(0, 40)] + [None] * 8
        raw = [1] * 9
        for _ in range(40):
            units, raw, row = step(units, raw, 3, 3, [0] * 9, [0] * 9)
        self.assertEqual(units, [None] * 9)
        self.assertEqual(sum(raw), 10)
        self.assertEqual(row['energy_after'], 0)

    def test_random_multistep_mass_energy_and_capacity(self):
        rng = random.Random(90600)
        for exchange in (False, True):
            for _ in range(50):
                units = [Unit(rng.randrange(4), rng.randrange(65))
                         if rng.randrange(2) else None for _ in range(16)]
                raw = [rng.randrange(3) for _ in units]
                mass = sum(raw) + sum(u is not None for u in units)
                energy = sum(u.energy for u in units if u is not None)
                for _ in range(20):
                    proposals = [rng.randrange(17) for _ in units]
                    directions = [rng.randrange(4) for _ in units]
                    units, raw, row = step(units, raw, 4, 4, proposals, directions,
                                           exchange=exchange)
                    energy += row['imported'] - row['spent']
                    self.assertEqual(sum(raw) + sum(u is not None for u in units), mass)
                    self.assertEqual(sum(u.energy for u in units if u is not None), energy)
                    self.assertTrue(all(u is None or 0 < u.energy <= 64 for u in units))


if __name__ == '__main__':
    unittest.main()
