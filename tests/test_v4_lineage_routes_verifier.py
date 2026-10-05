import unittest
from scripts.verify_v4_lineage_routes import label_history, reconstruct_gates
class RouteVerifierTests(unittest.TestCase):
    def test_forward_labels_other_and_selected(self):
        people=[{'parent':None},{'parent':None},{'parent':0},{'parent':1},{'parent':2},{'parent':None}]
        self.assertEqual(label_history(people,[2,3]),['other','other','left','right','left','other'])
    def test_dissolution_then_collision_and_energy_priority(self):
        units=[None]*256;raw=[0]*256;directions=[0]*256
        units[85]={'energy':16};units[87]={'energy':16};units[86]={'energy':0};directions[87]=1
        result=reconstruct_gates(units,raw,directions)
        self.assertEqual(result[85]['reason'],'collision')
        self.assertEqual(result[87]['reason'],'collision')
        self.assertEqual(result[85]['target_raw'],1)
        units[85]['energy']=15
        result=reconstruct_gates(units,raw,directions)
        self.assertEqual(result[85]['reason'],'energy')
        self.assertEqual(result[87]['reason'],'formed')
        self.assertNotIn(86,result)
    def test_priority_hides_multiple_failed_gates(self):
        units=[None]*256;raw=[0]*256;directions=[0]*256
        units[85]={'energy':1};units[86]={'energy':20}
        result=reconstruct_gates(units,raw,directions)[85]
        self.assertEqual(result['reason'],'energy')
        self.assertFalse(result['target_empty']);self.assertFalse(result['raw_ok'])
    def test_parent_cycle_rejected(self):
        with self.assertRaises(ValueError):label_history([{'parent':0}],[])
