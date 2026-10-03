import unittest
from copy import deepcopy
from scripts.analyze_v4_copy_members import describe, episode_records, analyze_case, summarize
from scripts.run_v4_copy_control import run_case

class MemberTest(unittest.TestCase):
    def test_founders_and_depths(self):
        parents=[None,None,None,0,1,3,4]
        self.assertEqual(describe([5,6],parents),dict(members=[5,6],original_members=[],depths=[2,2],founder_roots=[0,1],all_new=True))
        self.assertEqual(describe([0,5],parents)['depths'],[0,2])
        self.assertFalse(describe([0,5],parents)['all_new'])
        with self.assertRaises((ValueError,AssertionError)):describe([2,5],parents)
    def test_rotating_pairs_three_groups(self):
        a,b,c=[0,1],[3,4],[5,6]
        spans=episode_records([[a,b],[a,b,c],[b,c],[a,c]])
        self.assertEqual(spans,[dict(start=1,end=4,length=4,right_censored=True,stable_groups=[],stable_pair=False,max_same_pair_run=2)])
        stable=episode_records([[a,b]]*10+[[]])[0]
        self.assertTrue(stable['stable_pair']);self.assertEqual(stable['max_same_pair_run'],10);self.assertFalse(stable['right_censored'])
    def test_real_control_and_tamper(self):
        c=run_case('constructed-off');r=analyze_case(c,'control-constructed-off')
        self.assertEqual(r['episodes'][0]['max_same_pair_run'],27)
        self.assertEqual(r['new_longest'],0)
        c=deepcopy(c);c['summary']['genetic_counts'][5]=0
        with self.assertRaises((ValueError,AssertionError)):analyze_case(c,'control-constructed-off')
    def test_empty_grid(self):
        with self.assertRaises((ValueError,AssertionError)):summarize([])

    def test_two_new_components_and_ancestry_tamper(self):
        # Synthetic identity reassignment, not a new physical trajectory.
        c=run_case('constructed-off');last=deepcopy(c['rows'][-1])
        for site,i in enumerate(last['site_ids']):
            if i in (0,1):last['site_ids'][site]=7+i
        c['rows']=[]
        for tick in range(1,33):
            row=deepcopy(last);row['tick']=tick;c['rows'].append(row)
        c['final']['site_ids']=deepcopy(last['site_ids']);c['final']['parents']+=[5,6]
        c['summary']['genetic_counts']=[2]*32;c['summary']['episodes']=[[1,32]]
        r=analyze_case(c,'control-constructed-off')
        self.assertEqual(r['new_longest'],32);self.assertTrue(r['new_persistent10'])
        self.assertEqual([g['depths'] for g in r['steps'][0]['copies']],[[2,2],[3,3]])
        c['final']['parents'][7]=2
        with self.assertRaises((ValueError,AssertionError)):analyze_case(c,'control-constructed-off')
