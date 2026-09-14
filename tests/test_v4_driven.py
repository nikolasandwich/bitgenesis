from random import Random
import unittest
from bitgenesis.v4.local import Unit,interact
from bitgenesis.v4.driven import step


class DrivenTests(unittest.TestCase):
    def test_zero_drive_zero_leak_matches_closed(self):
        units=[Unit(0,40),Unit(0,12)]+[None]*7
        expected,record=interact(units,3,3)
        actual,driven=step(units,3,3,[0]*9,leak=0)
        self.assertEqual(actual,expected)
        self.assertEqual(driven['interaction'],record)

    def test_input_rejection_leak_and_reactivation(self):
        units=[Unit(0,0),Unit(0,0)]+[None]*7
        result,row=step(units,3,3,[4]*9,capacity=4,leak=1)
        self.assertEqual(row['imported'],8)
        self.assertEqual(row['rejected_import'],28)
        self.assertEqual(row['leakage'],2)
        self.assertEqual(row['interaction']['bonds'],[[0,1]])
        self.assertEqual([u.energy for u in result if u],[2,2])

    def test_random_energy_and_capacity_bounds(self):
        rng=Random(90300)
        for _ in range(100):
            units=[None if rng.randrange(5)==0 else Unit(rng.randrange(4),rng.randrange(17)) for _ in range(25)]
            after,row=step(units,5,5,[rng.randrange(20) for _ in units],capacity=16)
            self.assertTrue(all(0<=u.energy<=16 for u in after if u is not None))
            self.assertEqual(row['energy_before']+row['imported']-row['spent'],row['energy_after'])
        with self.assertRaises(ValueError):
            step([Unit(0,17)]+[None]*8,3,3,[0]*9,capacity=16)


if __name__=='__main__':
    unittest.main()
