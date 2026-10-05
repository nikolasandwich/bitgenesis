import unittest
from scripts.verify_v4_triggered_policy import saved_physics, full_metrics

class PolicyVerifierTests(unittest.TestCase):
    def test_saved_adapter_rejects_wrong_initial_energy(self):
        row={'tick':2,'energy_before':5}
        provider=saved_physics([{'physical':row}])
        with self.assertRaises(ValueError):provider([{'energy':4}],[],{},row,False)
    def test_no_trigger_keeps_real_accounts(self):
        case={'initial':{'units':[{'energy':10}]},'rows':[{'physical':{'imported':3,'spent':2,'rejected_import':7,'material':{'proposals':[],'dissolved':[]}}}], 'final':{'units':[{'energy':11}]}}
        m=full_metrics(case,None,None)
        self.assertEqual(m['persistent10'],0)
        self.assertEqual(m['final_energy'],11)
        self.assertEqual(m['rejected_import'],7)

    def test_energy_export_counted_once(self):
        case={'initial':{'units':[{'energy':10}]},'rows':[{'physical':{'imported':3,'spent':2,'rejected_import':7,'material':{'proposals':[],'dissolved':[]}}}], 'final':{'units':[{'energy':11}]}}
        arm={'initial':{'energy_export':4,'removals':[{'identity':0}]},'rows':[],'final':{'units':[{'energy':7}]},'metrics':{}}
        self.assertEqual(full_metrics(case,{'t0':1},arm)['final_energy'],7)
        arm['final']['units'][0]['energy']=11
        with self.assertRaises(ValueError):full_metrics(case,{'t0':1},arm)
