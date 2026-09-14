import unittest
from scripts.verify_v4_study001 import windows


class WindowTests(unittest.TestCase):
    def test_exact_window_edges_and_empty_components(self):
        rows=[dict(tick=t,interaction=dict(bonds=[[0,1]] if t==251 else [],spent=0),
                   components=[],imported=1,rejected_import=0,leakage=0) for t in range(1,501)]
        result=windows(rows)
        self.assertEqual([r['imported'] for r in result],[100,150,250])
        self.assertEqual(result[-1]['active_fraction'],'1/250')
        self.assertEqual(result[-1]['mean_largest_component'],'0')
        for bad in (rows[:-1],rows+[rows[0]]):
            with self.assertRaises(ValueError):
                windows(bad)


if __name__=='__main__':
    unittest.main()
