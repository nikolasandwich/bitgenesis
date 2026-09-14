from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.competition import run
from bitgenesis.v4.competition_lineage import trace
from bitgenesis.v4.competition_audit import audit


class CompetitionTests(unittest.TestCase):
    def test_neutral_role_swap_same_world_opposite_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            p=(0,1,2,3)
            for name,sites in (('a',(11,13)),('swap',(13,11))):
                result=run(root/name,99000,(p,p),30,width=5,height=5,initial_sites=sites)
                self.assertEqual(audit(root/name)['summary'],result)
            for name in ('initial.json','steps.jsonl','final.json','summary.json'):
                self.assertEqual((root/'a'/name).read_bytes(),(root/'swap'/name).read_bytes())
            a,b=trace(root/'a'),trace(root/'swap')
            self.assertEqual(a['founders_by_role'],[0,1])
            self.assertEqual(b['founders_by_role'],[1,0])
            for left,right in zip(a['counts'],b['counts']):
                self.assertEqual(left['counts'],right['counts'][::-1])

    def test_distinct_program_ancestry_and_zero_horizon(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            programs=((0,0,0,0),(1,2,3,0))
            for name,steps in (('a',20),('zero',0)):
                run(root/name,99001,programs,steps,width=5,height=5,initial_sites=(13,11))
                result=trace(root/name)
                for r in result['lineage']['individuals']:
                    role=result['founders_by_role'].index(r['founder'])
                    self.assertEqual(r['program'],list(programs[role]))
            with self.assertRaises(ValueError):
                run(root/'bad',99001,programs,0,initial_sites=(1,1))
            self.assertFalse((root/'bad').exists())
