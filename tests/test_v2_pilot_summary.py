from itertools import product
import unittest
from scripts.verify_v2_pilot001 import summarize


class V2PilotSummaryTests(unittest.TestCase):
    def test_requires_reproduction_and_preserves_cell_order(self):
        rows=[]
        for energy,renewal,encoding,seed in product((640,1280),(15,30),('developmental','direct'),range(82000,82005)):
            rows.append(dict(energy=energy,renewal=renewal,encoding=encoding,seed=seed,population=1,
                births=0 if energy==640 else 1,founder_attempts=32,successful_founders=2,
                failed_reasons={'founder':{'empty_structure':30},'offspring':{}}))
        result=summarize(rows)
        self.assertEqual(result['selected_developmental_cell'],{'energy':1280,'renewal':15})
        self.assertFalse(result['cells'][0]['usable'])
        self.assertEqual(result['cells'][0]['failed_reasons']['founder']['empty_structure'],150)
        for row in rows:
            row['births']=0
        self.assertIsNone(summarize(rows)['selected_developmental_cell'])
        with self.assertRaises(ValueError):
            summarize(rows[:-1])
        with self.assertRaises(ValueError):
            summarize(rows+[rows[0]])
