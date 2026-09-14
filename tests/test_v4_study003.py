from itertools import product
import unittest
from scripts.verify_v4_study003 import grid, observe


class Study003Tests(unittest.TestCase):
    def test_null_and_refill_matching_denominators(self):
        ref=[dict(material=0),dict(material=1),None]
        current=[dict(material=2),dict(material=1),dict(material=0)]
        row=observe(ref,current,[0,1,2])
        self.assertEqual(row['occupied_fraction'],'1')
        self.assertEqual(row['refill_fraction'],'1')
        self.assertEqual(row['material_match_fraction'],'1/2')
        self.assertIsNone(observe(ref,current,[2])['material_match_fraction'])
        self.assertEqual(observe(ref,[None]*3,[0,1])['material_match_fraction'],'0')

    def test_missing_duplicate_grid_rejected(self):
        rows=[dict(kind='prefix',seed=s) for s in range(93000,93005)]
        rows += [dict(kind='branch',seed=s,removal=r,threshold=t)
                 for s,r,t in product(range(93000,93005),(False,True),(16,65))]
        p,b=grid(rows)
        self.assertEqual((len(p),len(b)),(5,20))
        with self.assertRaises(ValueError):
            grid(rows[:-1])
        with self.assertRaises(ValueError):
            grid(rows[:-1]+[rows[-2]])
