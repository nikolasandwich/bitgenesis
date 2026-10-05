import unittest
from scripts import verify_v4_reformation_barriers as v

class BarrierVerifierTests(unittest.TestCase):
    def test_intervals_exclude_diagnostic_and_mark_right_censor(self):
        self.assertEqual(v.spans([False,True,True],30),[dict(start=31,end=32,length=2,right_censored=True)])
        self.assertEqual(v.spans([],33),[])
        self.assertEqual(v.spans([True]*10,20),[dict(start=20,end=29,length=10,right_censored=False)])
    def test_chain_selected_and_full_root_distinct(self):
        people=[dict(parent=None),dict(parent=None),dict(parent=0),dict(parent=2)]
        self.assertEqual(v.lineage(3,people,{2}),(0,[3,2],2))
        self.assertEqual(v.lineage(3,people,{1}),(0,[3,2,0],None))
    def test_strict_equal(self):
        with self.assertRaises(ValueError):v.same(True,1,'strict')

class SlotBoundaryTests(unittest.TestCase):
    def test_program_failure_does_not_hide_component_failure(self):
        from copy import deepcopy
        units=[None]*256;ids=[None]*256
        people=[dict(parent=None,birth_tick=0) for _ in range(3)]
        people += [dict(parent=0,birth_tick=6),dict(parent=1,birth_tick=6),dict(parent=3,birth_tick=7),dict(parent=4,birth_tick=7),dict(parent=3,birth_tick=8)]
        source=dict(initial=dict(units=[None]*256))
        for site,program in ((85,[0,0,0,1]),(86,[0,0,0,2])):
            source['initial']['units'][site]=dict(material=0,program=program)
            units[site]=deepcopy(source['initial']['units'][site])
        ids[85],ids[86]=5,6
        selection=dict(t0=6,offspring_ids=[3,4])
        r=v.inspect_state(units,ids,8,people,selection,source,[],[])
        self.assertEqual(r['upper_failure'],'pass')
        self.assertTrue(r['slots'][0]['post_birth'])
        self.assertTrue(r['slots'][0]['selected_ancestry'])
        units[101]=dict(material=0,program=[0]*4);ids[101]=7
        units[85]['program']=[0]*4
        r=v.inspect_state(units,ids,8,people,selection,source,[],[])
        self.assertEqual(r['upper_failure'],'program')
        self.assertFalse(r['slots'][0]['genetic_match'])
        self.assertFalse(r['slots'][0]['whole_component'])
        self.assertEqual(r['connector_sites'],[101])
        units[85]['program']=[0,0,0,1]
        self.assertEqual(v.inspect_state(units,ids,8,people,selection,source,[],[])['upper_failure'],'component')
        units[86]=None;ids[86]=None
        r=v.inspect_state(units,ids,8,people,selection,source,[],[])
        self.assertTrue(all(r['slots'][0][flag] is False for flag in v.FLAGS))
        self.assertEqual(r['upper_failure'],'missing')
