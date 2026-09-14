import unittest
from scripts.verify_v4_study007 import role_counts, primary


class Study007Tests(unittest.TestCase):
    def test_same_program_role_reuse_and_swap_reversal(self):
        rows=[]
        for tick in range(1,201):
            units=[None]*64
            for site in (34,38):
                units[site]=dict(program=[0]*4)
            material=dict(dissolved=[],proposals=[])
            if tick==1:
                material=dict(dissolved=[34],proposals=[dict(reason='formed',source=38,target=34)])
            rows.append(dict(tick=tick,units=units,material=material))
        a=role_counts(rows,[34,38])
        b=role_counts(rows,[38,34])
        self.assertEqual(a[0]['counts'],[0,2])
        self.assertEqual(b[0]['counts'],[2,0])
        self.assertEqual(primary(a)['value'],'-1/32')
        self.assertEqual(primary(b)['value'],'1/32')
        with self.assertRaises(ValueError):
            role_counts(rows[:-1],[34,38])
