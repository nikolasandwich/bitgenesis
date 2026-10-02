import unittest
from fractions import Fraction
from itertools import product
from unittest.mock import patch
from scripts.analyze_v4_retention_weighting import ledger_pair, cell, aggregate
from scripts.retention_weighting_inputs import verify_inventory


class RetentionWeightingTests(unittest.TestCase):
    def test_size_reversal_and_exact_covariance(self):
        rows=[dict(component=0,category='local_multi',size=2,on=2,off=0),dict(component=1,category='local_multi',size=10,on=0,off=6)]
        c=cell(rows,12)
        self.assertEqual(c['component_difference'],'1/5')
        self.assertEqual(c['individual_difference'],'-1/3')
        self.assertEqual(c['weighting_gap'],'-8/15')
        self.assertEqual(c['covariance_term'],c['weighting_gap'])
        self.assertEqual(Fraction(c['covariance'])/Fraction(c['mean_size']),Fraction('-8/15'))

    def test_world_priority_and_original_deaths(self):
        arm=dict(component=0,anchor_size=1,anchor_members=[7],whole_world_anchor=True,original_deaths=1,endpoint=dict(descendants=8,original_survivors=0))
        p=dict(seed=96000,mutation=0,anchor=100,initial_components=1,records=[dict(component=0,on=arm,off=arm.copy())])
        self.assertEqual(ledger_pair(p)['records'],[dict(component=0,category='world',size=1,on=0,off=0)])
        arm['endpoint']['original_survivors']=1
        with self.assertRaises(ValueError):ledger_pair(p)

    def test_empty_rates_and_zero_contribution(self):
        c=cell([],4)
        self.assertEqual(c['initial'],0)
        self.assertIsNone(c['individual_difference'])
        self.assertIsNone(c['component_on'])
        self.assertEqual(c['world_contribution'],'0')

    def test_hierarchy_counts_use_all_anchors_and_sources(self):
        pairs=[]
        for seed,m,a in product(range(96000,96005),(0,100),(100,200,300,400)):
            records=[dict(component=0,category='world',size=1,on=1,off=0)] if seed==96000 and a==100 else [dict(component=0,category='local_multi',size=2,on=0,off=1),dict(component=1,category='singleton',size=1,on=0,off=0)]
            pairs.append(dict(seed=seed,mutation=m,anchor=a,records=records))
        result=aggregate(pairs)
        g=result['groups'][0]['cells']['world']
        self.assertEqual(g['components'],dict(mean='1/20',available=5,missing=0))
        self.assertEqual(g['component_difference'],dict(mean='1',available=1,missing=4))
        self.assertEqual(result['sources'][0]['cells']['world']['component_on'],dict(mean='1',available=1,missing=3))
        self.assertEqual(set(result['anchors'][0]['sizes']),{'1','2'})
        self.assertEqual(result['anchors'][0]['sizes']['2']['components'],0)
        with self.assertRaises(ValueError):aggregate(pairs[:-1])

    def test_independent_summary_agrees_on_missing_hierarchy(self):
        from scripts.verify_v4_retention_weighting import summary_from_records
        pairs=[]
        for seed,m,a in product(range(96000,96005),(0,100),(100,200,300,400)):
            rows=[dict(component=0,category='world',size=1,on=0,off=1)] if seed==96000 else [dict(component=0,category='local_multi',size=2,on=2,off=0),dict(component=1,category='local_multi',size=10,on=0,off=6)]
            pairs.append(dict(seed=seed,mutation=m,anchor=a,records=rows))
        self.assertEqual(aggregate(pairs),summary_from_records(pairs))

    def test_binding_omissions_and_duplicates_rejected(self):
        with patch('scripts.retention_weighting_inputs.digest',return_value='hash'):
            with self.assertRaisesRegex(ValueError,'inventory'):verify_inventory({}, {'needed'})
            with self.assertRaisesRegex(ValueError,'inventory'):verify_inventory({'extra':'hash'}, {'needed'})
            verify_inventory({'needed':'hash'}, {'needed'})
