from itertools import product
import unittest
from scripts.verify_v4_study004 import grid, observe


class Study004Tests(unittest.TestCase):
    def test_exact_three_intervention_grid(self):
        rows=[dict(kind='prefix',seed=s) for s in range(94000,94005)]
        rows += [dict(kind='branch',seed=s,intervention=i,threshold=t)
                 for s,i,t in product(range(94000,94005),('sham','extraction','damage'),(16,65))]
        self.assertEqual(tuple(map(len,grid(rows))),(5,30))
        with self.assertRaises(ValueError):
            grid(rows[:-1]+[rows[-2]])
        with self.assertRaises(ValueError):
            grid(rows[:-1])

    def test_empty_reference_and_wrong_material_refill(self):
        ref=[None,dict(material=0)]
        current=[dict(material=0),dict(material=1)]
        row=observe(ref,current,[0,1])
        self.assertEqual(row['refill_fraction'],'1')
        self.assertEqual(row['material_match_fraction'],'0')
        self.assertIsNone(observe(ref,current,[0])['material_match_fraction'])
