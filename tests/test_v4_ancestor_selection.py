import unittest
from scripts.trace_v4_study005 import select


class AncestorSelectionTests(unittest.TestCase):
    def test_real_founder_and_equal_program_pairs_retained(self):
        records=[dict(id=0,parent=None,founder=0,death_tick=None,program=[0]*4)]
        for i in range(1,6):
            records.append(dict(id=i,parent=i-1,founder=0,death_tick=None,program=[0]*4))
        result=select(dict(individuals=records),1,250,0)
        self.assertEqual(result['eligible'],5)
        self.assertEqual(len(result['pairs']),3)
        self.assertEqual(result,select(dict(individuals=records),1,250,0))
        for pair in result['pairs']:
            self.assertTrue(pair['equal_program'])
            self.assertEqual(pair['founder']['id'],0)
            self.assertEqual(pair['parent_chain'][-1],0)
        self.assertEqual(select(dict(individuals=records[:1]),1,250,0)['status'],'unavailable')
