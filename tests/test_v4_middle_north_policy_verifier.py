import unittest
from copy import deepcopy
from unittest.mock import patch
from scripts import verify_v4_middle_north_policy as m

class NorthVerifierTests(unittest.TestCase):
    def test_two_slots_only_and_no_source_mutation(self):
        tape={'tick':20,'directions':[i%4 for i in range(256)],'mutation_tickets':[1,2],'driven':{'inputs':[3]}}
        before=deepcopy(tape);seen=[]
        def fake(units,raw,cfg,actual,exchange):seen.append(actual);return actual
        with patch.object(m.v,'physical_step',fake):result=m.north_physics([],[],{},tape,False)
        self.assertEqual(tape,before)
        self.assertEqual(result['directions'][101:103],[3,3])
        for i in set(range(256))-{101,102}:self.assertEqual(result['directions'][i],tape['directions'][i])
        self.assertEqual(result['mutation_tickets'],tape['mutation_tickets'])
        self.assertEqual(result['driven'],tape['driven'])
    def test_mask_includes_empty_unqualified_sites(self):
        case={'rows':[{'tick':1,'physical':{'directions':[0]*256}},{'tick':2,'physical':{'directions':[3]*256}}]}
        self.assertEqual(m.direction_mask(case,1),[dict(tick=2,site=s,original_direction=3,new_direction=3,changed=False) for s in (101,102)])
    def test_difference_in_differences(self):
        # Each encoding's new arm is1, yet policy differences vary with baseline.
        rows=[]
        for enc in m.ENCODINGS:
            for seed in range(120000,120020):
                c=dict.fromkeys(m.METRICS,0);a=dict.fromkeys(m.METRICS,0)
                a['births']=1;c['births']=int(enc=='north')
                rows.append(dict(encoding=enc,seed=seed,trigger=False,short_window=False,remaining=0,control_metrics=c,ablation_metrics=a,delta={k:a[k]-c[k] for k in c}))
        summary=m.summary(rows)
        self.assertEqual(summary['north_contrasts'][0]['mean_delta']['births'],'1')
        self.assertEqual(summary['cells'][0]['mean_delta']['births'],'1')
if __name__=='__main__':unittest.main()
