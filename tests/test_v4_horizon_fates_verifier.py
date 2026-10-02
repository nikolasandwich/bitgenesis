import unittest
from scripts.verify_v4_horizon_fates import rebuild, independent_results, independent_summary

class FateRebuildTests(unittest.TestCase):
    def case(self,groups):
        initial={'observation':{'components':{'material':[[0,1],[2]]}}}
        rows=[{'tick':i,'site_ids':[x for g in gs for x in g],'observation':{'components':{'material':gs}}} for i,gs in enumerate(groups,1)]
        return initial,rows,{'parents':[None,None,None,0,1,3]}
    def test_future_birth_replacement_then_break(self):
        args=self.case([[[0,1],[2]],[[0,3],[2]],[[3,4],[2]],[[3],[4],[2]]])
        r=rebuild(*args,checkpoints=(1,2,3,4))[0]
        self.assertEqual(r['checkpoints']['1']['descendants'],2)
        self.assertEqual(r['checkpoints']['3']['category'],'continuous_replaced')
        self.assertEqual(r['checkpoints']['4']['category'],'broken_replaced')
        self.assertEqual((r['first_complete_replacement_tick'],r['first_break_tick'],r['order']),(3,4,'replacement_first'))
        self.assertEqual(r['first_break_state'],'fragmented')
    def test_replacement_then_extinction_and_same_tick(self):
        r=rebuild(*self.case([[[0,1],[2]],[[3],[2]],[[2]],[[2]]]),checkpoints=(1,2,3,4))[0]
        self.assertEqual(r['order'],'same_tick')
        self.assertEqual(r['first_break_state'],'closed_singleton')
        self.assertEqual(r['checkpoints']['4']['category'],'extinct')
        self.assertEqual(r['first_complete_replacement_tick'],2)
    def test_reclosure_does_not_restore_continuity(self):
        r=rebuild(*self.case([[[0],[1],[2]],[[0,1],[2]]]),checkpoints=(1,2))[0]
        self.assertEqual(r['checkpoints']['2']['category'],'broken_retained')
        self.assertEqual(r['order'],'break_only')
        with self.assertRaises(AssertionError):rebuild(*self.case([[[0,0],[2]]]),checkpoints=(1,))

class FateAggregationTests(unittest.TestCase):
    def branches(self):
        from itertools import product
        result=[]
        for h,s,m,e in product((True,False),range(112000,112005),(0,100),(True,False)):
            category='continuous_retained' if e else 'broken_retained'
            components=[dict(component=0,anchor_members=[0,1],checkpoints={str(t):dict(category=category,original_survivors=2,descendants=2,continuous=e) for t in (100,200,300,400)},first_break_tick=None if e else 2,first_complete_replacement_tick=None,first_break_state='never' if e else 'mixed',order='neither' if e else 'break_only')]
            if s==112004:components=[]
            result.append(dict(history=h,seed=s,mutation=m,exchange=e,components=components))
        return result
    def test_missingness_and_all_categories(self):
        rows=independent_results(self.branches());s=independent_summary(rows)
        metric=s['checkpoint_groups'][0]['metrics']['continuous_retained']
        self.assertEqual(metric,dict(mean='1',available=4,missing=1))
        self.assertEqual(s['timing_groups'][0]['metrics']['order:break_only']['mean'],'-1')
        rows[0]['status']='failed'
        with self.assertRaises(AssertionError):independent_summary(rows)
    def test_denominator_and_fraction_tamper(self):
        rows=independent_results(self.branches());rows[0]['checkpoints']['100']['fractions']['continuous_retained']='0'
        with self.assertRaises(AssertionError):independent_summary(rows)
        rows=independent_results(self.branches());rows[0]['history']=1
        with self.assertRaises(AssertionError):independent_summary(rows)
    def test_equal_source_not_pooled_component_mean(self):
        import copy
        branches=self.branches()
        for b in branches:
            if b['seed']==112000:
                c=copy.deepcopy(b['components'][0]);c['component']=1;c['anchor_members']=[3,4]
                c.update(first_break_tick=1,first_break_state='fragmented',order='break_only')
                for cp in c['checkpoints'].values():cp.update(category='broken_retained',continuous=False)
                b['components'].append(c)
        s=independent_summary(independent_results(branches))
        self.assertEqual(s['checkpoint_groups'][0]['metrics']['continuous_retained']['mean'],'7/8')
