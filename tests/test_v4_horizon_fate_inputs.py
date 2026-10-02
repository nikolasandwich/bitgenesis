import unittest
from itertools import product
from scripts.horizon_fate_inputs import validate_grid

class InputGridTests(unittest.TestCase):
    def rows(self):
        return [dict(history=h,seed=s,mutation=m,exchange=e) for h,s,m,e in product((True,False),range(112000,112005),(0,100),(True,False))]
    def test_all_and_duplicate_missing(self):
        rows=self.rows();validate_grid(rows)
        for bad in (rows[:-1],rows+[rows[0]],rows[:-1]+[rows[0]]):
            with self.assertRaises(AssertionError):validate_grid(bad)
    def test_boolean_integer_alias_rejected(self):
        for key in ('history','exchange'):
            rows=self.rows();rows[0][key]=1
            with self.assertRaises(AssertionError):validate_grid(rows)
        rows=self.rows();rows[0]['seed']=112000.0
        with self.assertRaises(AssertionError):validate_grid(rows)
