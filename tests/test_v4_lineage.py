from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.lineage import Observer, trace
from bitgenesis.v4.hereditary_runner import run


class LineageTests(unittest.TestCase):
    def test_identical_programs_are_distinct_and_site_reuse_is_new_birth(self):
        u=dict(material=0,program=[0]*4,energy=8)
        observer=Observer([u,u,None])
        observer.accept(dict(tick=1,units=[u,u,None],material=dict(dissolved=[0],proposals=[
            dict(reason='formed',source=1,target=0,material=0,parent_program=[0]*4,
                 child_program=[0]*4,child_energy=8,mutated=False)])))
        result=observer.result()
        self.assertEqual(result['final_site_ids'],[2,1,None])
        self.assertEqual(result['individuals'][0]['death_tick'],1)
        self.assertEqual(result['individuals'][2]['parent'],1)
        self.assertEqual(result['individuals'][2]['founder'],1)
        self.assertEqual(result['individuals'][2]['generation'],1)
        self.assertEqual(result['individuals'][1]['offspring'],1)

    def test_audited_runtime_trace_and_zero_horizon(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name,steps in (('zero',0),('run',20)):
                summary=run(root/name,95006,steps,width=4,height=4,occupancy=250,mutation_per_thousand=1000)
                result=trace(root/name)
                self.assertEqual(result['summary']['births'],summary['formations'])
                for r in result['individuals']:
                    if r['parent'] is not None:
                        parent=result['individuals'][r['parent']]
                        self.assertLess(parent['birth_tick'],r['birth_tick'])
                        self.assertEqual(r['founder'],parent['founder'])
                        self.assertNotEqual(r['program'],parent['program'])
