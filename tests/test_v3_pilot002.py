import unittest
from scripts.verify_v3_pilot002 import summarize


class Pilot002Tests(unittest.TestCase):
    def test_order_null_grid_and_paired_contrasts(self):
        rows=[dict(feeding=f,renewal=r,recycling=c,seed=s,population=1,births=0)
              for f in (8,16) for r in (30,60) for c in (1,0) for s in range(87000,87005)]
        self.assertIsNone(summarize(rows)['selected'])
        for row in rows:
            if row['feeding']==16 or row['renewal']==60:
                row['births']=2
        result=summarize(rows)
        self.assertEqual(result['selected'],dict(feeding=16,renewal=30))
        self.assertEqual(len(result['paired_contrasts']),40)
        self.assertEqual(result['paired_contrasts'][0]['birth_difference'],2)
        for bad in (rows[:-1],rows+[rows[0]]):
            with self.assertRaises(ValueError):
                summarize(bad)


if __name__=='__main__':
    unittest.main()
