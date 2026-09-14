import unittest
from scripts.verify_v3_pilot001 import summarize


class PilotTests(unittest.TestCase):
    def test_fixed_choice_reproduction_requirement_and_grid(self):
        rows=[dict(renewal=r,recycling=c,seed=s,population=1,births=0)
              for r in (15,30) for c in (1,0) for s in range(86000,86005)]
        self.assertIsNone(summarize(rows)['selected_renewal'])
        for row in rows:
            if row['renewal']==30 and row['recycling']==1:
                row['births']=1
        self.assertEqual(summarize(rows)['selected_renewal'],30)
        for row in rows:
            row['births']=1
        self.assertEqual(summarize(rows)['selected_renewal'],15)
        for bad in (rows[:-1], rows+[rows[0]]):
            with self.assertRaises(ValueError):
                summarize(bad)


if __name__=='__main__':
    unittest.main()
