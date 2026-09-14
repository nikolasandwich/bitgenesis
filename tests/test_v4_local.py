from random import Random
import unittest
from bitgenesis.v4.local import Unit,interact,components


class LocalUnitTests(unittest.TestCase):
    def test_energy_conservation_with_dense_random_neighbors(self):
        rng=Random(90000)
        for _ in range(100):
            units=[None if rng.randrange(5)==0 else Unit(rng.randrange(4),rng.randrange(80)) for _ in range(25)]
            after,row=interact(units,5,5)
            self.assertEqual(sum(u.energy for u in units if u)-row['spent'],sum(u.energy for u in after if u))
            self.assertTrue(all(u.energy>=0 for u in after if u))

    def test_wraparound_bond_and_exchange_removal(self):
        units=[None]*9
        units[0],units[2]=Unit(1,25),Unit(1,9)
        after,row=interact(units,3,3)
        control,other=interact(units,3,3,exchange=False)
        self.assertEqual(row['bonds'],[[2,0]])
        self.assertEqual((after[0].energy,after[2].energy),(22,10))
        self.assertEqual((control[0].energy,control[2].energy),(24,8))
        self.assertEqual(row['spent'],other['spent'])
        self.assertEqual(components(after,row['bonds']),[[0,2]])

    def test_unaffordable_endpoint_and_material_mismatch(self):
        units=[None]*9
        units[0],units[1],units[3]=Unit(0,1),Unit(0,20),Unit(1,20)
        _,row=interact(units,3,3)
        self.assertEqual(row['bonds'],[[0,1]])
        units[3]=Unit(0,20)
        after,row=interact(units,3,3)
        self.assertEqual(row['bonds'],[])
        self.assertEqual(components(after,row['bonds']),[[0],[1],[3]])


if __name__=='__main__':
    unittest.main()
