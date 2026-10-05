import unittest
from copy import deepcopy
from scripts import verify_v4_program_position as v

class PositionVerifierTests(unittest.TestCase):
    def test_all_direction_encodings(self):
        for i,name in enumerate(('east','west','south','north')):
            for identity in (0,1):
                expected=[0]*4;expected[i]=identity+1
                self.assertEqual(v.program(name,identity),expected)
        self.assertEqual(v.program('homogeneous',1),[0]*4)
    def test_strict_types(self):
        with self.assertRaises(ValueError):v.same(True,1,'count')
    def test_own_template_and_original_exclusion(self):
        initial=dict(units=[None]*256,site_ids=[None]*256)
        for site,i in ((85,0),(86,1)):
            initial['site_ids'][site]=i;initial['units'][site]=dict(material=0,program=v.program('east',i))
        units=deepcopy(initial['units']);ids=initial['site_ids'].copy()
        for s,i,p in ((117,2,0),(118,3,1)):
            ids[s]=i;units[s]=dict(material=0,program=v.program('east',p))
        row=dict(site_ids=ids,physical=dict(units=units))
        self.assertEqual(v.new_counts(initial,[row],[None,None,0,1]),[1])
        initial['units'][85]['program']=v.program('north',0)
        initial['units'][86]['program']=v.program('north',1)
        self.assertEqual(v.new_counts(initial,[row],[None,None,0,1]),[0])
