import unittest
from scripts.verify_v4_copy_bottlenecks import recount, intervals


def fixture(programs,groups,copy_count=0):
    ids=[None]*256;units=[None]*256
    for i,site,g in [(0,0,0),(1,1,1),(2,8,2)]:
        ids[site]=i;units[site]=dict(material=0,program=[g]*4)
    initial=dict(site_ids=ids,units=units,observation={'components':{'material':[[0,1],[2]]}})
    current=[None]*256;physical=[None]*256
    for offset,g in enumerate(programs):
        current[32+offset]=3+offset;physical[32+offset]=dict(material=0,program=[g]*4)
    final=dict(parents=[None,None,None]+[0]*len(programs),site_ids=current)
    rows=[dict(tick=1,site_ids=current,physical={'units':physical},observation={'components':{'material':groups}})]
    cp=[dict(component=0,anchor_members=[0,1],anchor_size=2,series={'descendant_genetic':[copy_count]})]
    return initial,rows,final,cp

class BottleneckTests(unittest.TestCase):
    def test_each_ordered_failure_and_pass(self):
        cases=[([0],[[3]],0),([0]*4,[[3,4],[5,6]],0),([0,1,0,1],[[3,4,5,6]],0),([0,1,0,1],[[3,4],[5,6]],0),([0,1,0,1],[[3,4],[5,6]],2)]
        states=('population_fail','inventory_fail','partition_fail','copy_fail','copy_pass')
        for index,case in enumerate(cases):
            p=recount(*fixture(*case))[0]
            self.assertEqual(p['state_steps'],{k:int(i==index) for i,k in enumerate(states)})
    def test_extra_types_do_not_obstruct_inventory(self):
        p=recount(*fixture([0,1,0,1,2],[[3,4,5,6,7]]))[0]
        self.assertEqual(p['series']['inventory'],[True])
        self.assertEqual(p['series']['partition'],[False])
    def test_mixed_component_counts_inventory_but_not_partition(self):
        a=fixture([0,1,0,1,2],[[3,4],[5,6,7]])
        a[2]['parents'][7]=2
        p=recount(*a)[0]
        self.assertEqual(p['series']['inventory'],[True]);self.assertEqual(p['series']['partition'],[False])
    def test_copy_contradiction_rejected(self):
        with self.assertRaises(AssertionError):recount(*fixture([0],[[3]],2))
    def test_intervals_and_future_ancestor(self):
        self.assertEqual(intervals([True]*9+[False]+[True]*10),[[1,9],[11,20]])
        a=fixture([0],[[3]])
        a[2]['parents'] += [0,None]
        self.assertEqual(recount(*a)[0]['series']['population'],[False])

class SummaryTests(unittest.TestCase):
    def records(self):
        from scripts.verify_v4_copy_bottlenecks import GRID,GATES,STATES
        records=[]
        for h,s,m,e in GRID:
            parents=[]
            for i in range(0 if s==112004 else 2 if s==112000 else 1):
                active=e and i==0
                series={k:([True]*10+[False]*390 if active and k!='copy' else [False]*400) for k in GATES}
                spans={k:intervals(v) for k,v in series.items()};states=dict.fromkeys(STATES,0)
                states['population_fail']=390 if active else 400;states['copy_fail']=10 if active else 0
                parents.append(dict(component=i,anchor_members=[2*i,2*i+1],anchor_size=2,series=series,episodes=spans,longest={k:max((b-a+1 for a,b in runs),default=0) for k,runs in spans.items()},state_steps=states))
            records.append(dict(history=h,seed=s,mutation=m,exchange=e,parents=parents))
        return records
    def test_exact_event_and_time_weighting(self):
        from scripts.verify_v4_copy_bottlenecks import make_results,make_summary
        result=make_summary(make_results(self.records()))
        for r in result['groups']:
            self.assertEqual(r['metrics']['partition_ever'],dict(mean='7/8',available=4,missing=1))
            self.assertEqual(r['metrics']['copy_fail'],dict(mean='7/320',available=4,missing=1))
            self.assertEqual(r['metrics']['population_fail']['mean'],'-7/320')
    def test_invalid_partition_nesting_state_total_and_failed_branch(self):
        from scripts.verify_v4_copy_bottlenecks import make_results,make_summary
        a=self.records();a[0]['parents'][0]['state_steps']['copy_fail']=11
        with self.assertRaises(AssertionError):make_results(a)
        a=self.records();a[0]['parents'][0]['series']['population']=[False]*400
        with self.assertRaises(AssertionError):make_results(a)
        rows=make_results(self.records());rows[0]['status']='failed'
        with self.assertRaises(AssertionError):make_summary(rows)
        with self.assertRaises(AssertionError):make_summary(rows[:-1])
    def test_repeated_initial_type_needs_double_multiplicity(self):
        a=fixture([0,0,0,1],[[3,4],[5,6]])
        a[0]['units'][1]['program']=[0]*4
        p=recount(*a)[0]
        self.assertTrue(p['series']['population'][0]);self.assertFalse(p['series']['inventory'][0])
