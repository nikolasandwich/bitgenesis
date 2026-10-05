import unittest
from copy import deepcopy
from tests import test_v4_reformation_barriers as fixtures
from scripts.analyze_v4_policy_component_timing import identity_timing, summarize, make_index, analyze_pair


def row(tick, identities, new=False, double=False):
    return dict(tick=tick, slots=[dict(identities=identities,birth_ticks=[10 if x is not None else None for x in identities],new_copy=new,post_birth=True,selected_ancestry=True)],new_copy_count=2 if double else int(new),births=[],deaths=[])


class TimingTests(unittest.TestCase):
    def test_birth_copresence_qualification_are_distinct(self):
        d=row(9,[None,None]); rows=[row(t,[3,4],t==32,t==32) for t in range(10,33)]
        changes,pairs=identity_timing(d,rows)
        self.assertEqual(len(changes),1)
        self.assertEqual(changes[0]['before'],d)
        self.assertEqual(pairs,[dict(identities=[3,4],birth_ticks=[10,10],first_copresence_tick=10,first_future_copresence_tick=10,first_upper_new_copy_tick=32,first_double_new_tick=32)])

    def test_diagnostic_and_reappearance(self):
        d=row(29,[3,4],True); rows=[row(30,[3,None]),row(31,[3,4]),row(32,[3,4],True)]
        changes,pairs=identity_timing(d,rows)
        self.assertEqual([c['tick'] for c in changes],[30,31])
        self.assertEqual(pairs[0]['first_copresence_tick'],29)
        self.assertEqual(pairs[0]['first_future_copresence_tick'],31)
        self.assertEqual(pairs[0]['first_upper_new_copy_tick'],32)
        self.assertIsNone(pairs[0]['first_double_new_tick'])

    def test_full_negative_index_without_science(self):
        old=[dict(encoding='east',seed=120000,trigger=False,t0=None,remaining=0,short_window=False,source='saved')]
        index=make_index(old)
        self.assertEqual(index[0]['applicability'],'not_applicable')
        self.assertIsNone(index[0]['branch'])
        self.assertNotIn('rows',index[0])
        s=summarize([],index)
        self.assertEqual((s['index_cases'],s['triggered'],s['no_trigger']),(1,0,1))
        self.assertEqual(len(s['cells']),20)
        self.assertTrue(all(c['n']==0 for c in s['cells']))

    def test_thin_adapter_preserves_selection_and_original_metrics(self):
        u,ids,people=fixtures.BarrierTests().state();sourceids=[None]*256;sourceids[85:87]=[0,1]
        source=dict(initial=dict(units=deepcopy(u),site_ids=sourceids))
        selection=dict(mode='random-direction',exchange=False,category='short_window',genotype='heterogeneous',seed=120000,t0=31,remaining_steps=1,offspring_ids=[3,4])
        arm=dict(initial=dict(tick=31,units=u,site_ids=ids),final=dict(individuals=people),rows=[dict(tick=32,physical=dict(units=u),site_ids=ids,births=[],deaths=[])],new_copy_counts=[1],episodes=[],metrics=dict(double_new_ever=0,persistent10=0,longest_double=0))
        branch=dict(selection=selection,control=arm,ablation=deepcopy(arm));result=analyze_pair('east',branch,source)
        self.assertEqual(result['selection'],selection)
        self.assertEqual(result['arms']['control']['selection'],selection)
        self.assertIn('prior043',result['arms']['control'])
        self.assertNotIn('prior036',result['arms']['control'])
        branch['ablation']['metrics']['double_new_ever']=1
        with self.assertRaises(ValueError):analyze_pair('east',branch,source)

if __name__=='__main__':unittest.main()
