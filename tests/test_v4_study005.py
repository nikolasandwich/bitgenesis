import unittest
from scripts.verify_v4_study005 import programs, windows


class Study005Tests(unittest.TestCase):
    def test_initial_set_excludes_empty_sites_and_counts_duplicates(self):
        p=[0,1,2,3]
        counts=programs([None,dict(program=p),dict(program=p)])
        self.assertEqual(dict(counts),{tuple(p):2})

    def test_windows_and_initially_absent_counts(self):
        rows=[]
        for tick in range(1,501):
            units=[None]*256
            if tick==101:
                units[0]=dict(program=[1,1,1,1])
            rows.append(dict(tick=tick,units=units,imported=0,rejected_import=0,
                driven=dict(leakage=0,interaction=dict(spent=0)),
                material=dict(proposals=[],dissolved=[],construction_spent=0,copy_spent=0)))
        early,late=windows(rows,{(0,0,0,0)})
        self.assertEqual(early['mean_initially_absent_units'],'0')
        self.assertEqual(late['mean_initially_absent_units'],'1/400')
        self.assertEqual(late['mean_occupied_fraction'],'1/102400')
        with self.assertRaises(ValueError):
            windows(rows[:-1],set())
