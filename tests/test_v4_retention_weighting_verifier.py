import unittest
from scripts.verify_v4_retention_weighting import measure, initial_records

class RetentionVerifierTests(unittest.TestCase):
    def test_weighting_can_reverse_sign(self):
        r=[dict(component=0,category='local_multi',size=2,on=2,off=0),dict(component=1,category='local_multi',size=10,on=0,off=3)]
        s=measure(r,12)
        self.assertEqual(s['component_difference'],'7/20')
        self.assertEqual(s['individual_difference'],'-1/12')
        self.assertEqual(s['covariance'],'-13/5')
        self.assertEqual(s['weighting_gap'],s['covariance_term'])
        self.assertEqual(s['covariance_term'],'-13/30')

    def test_empty_class_rate_is_missing_contribution_zero(self):
        s=measure([],12)
        self.assertEqual(s['components'],0)
        self.assertIsNone(s['individual_difference'])
        self.assertEqual(s['world_contribution'],'0')

    def test_original_identity_and_world_precedence(self):
        i=dict(site_ids=[0,None],observation=dict(components=dict(material=[[0]])))
        r=initial_records(i,dict(site_ids=[1,None]),dict(site_ids=[0,None]))
        self.assertEqual(r,[dict(component=0,category='world',size=1,on=0,off=1)])
