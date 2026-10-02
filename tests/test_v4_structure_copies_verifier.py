import unittest
from scripts.verify_v4_structure_copies import translated_equal,recount,intervals,make_results,make_summary

class DirectMatchTests(unittest.TestCase):
    def test_periodic_shift_and_rotation(self):
        a=((15,2,0),(0,2,0));b=((4,5,0),(5,5,0))
        self.assertTrue(translated_equal(a,b,16,16))
        self.assertFalse(translated_equal(a,((4,5,0),(4,6,0)),16,16))
    def test_properties_and_multiple_alignments(self):
        a=((0,0,0,(0,)),(8,0,0,(1,)));b=((0,0,0,(1,)),(8,0,0,(0,)))
        self.assertTrue(translated_equal(a,b,16,16))
        self.assertFalse(translated_equal(a,((0,0,1,(1,)),(8,0,0,(0,))),16,16))
        self.assertFalse(translated_equal(a,((0,0,0,(0,)),(8,0,0,(0,))),16,16))
    def test_nine_ten_and_multiple_episodes(self):
        self.assertEqual(intervals([2]*9+[1]+[3]*10),[[1,9],[11,20]])
        self.assertEqual(intervals([0,1,0]),[])


def fixture(groups):
    def snapshot(mapping,groups):
        ids=[None]*256;units=[None]*256
        for i,site,program in mapping:
            ids[site]=i;units[site]={'material':0,'program':[program]*4}
        return ids,units,{'components':{'material':groups}}
    ids,u,o=snapshot([(0,0,0),(1,1,1),(2,8,2)],[[0,1],[2]])
    initial=dict(site_ids=ids,units=u,observation=o)
    mapping=[(3,32,0),(4,33,1),(5,64,0),(6,65,1),(7,96,0),(8,97,1),(9,128,0),(10,129,1)]
    used={i for g in groups for i in g};mapping=[v for v in mapping if v[0] in used]
    ids,u,o=snapshot(mapping,groups)
    rows=[dict(tick=1,site_ids=ids,physical={'units':u},observation=o)]
    final={'parents':[None,None,None,0,1,0,1,2,2,2,2]}
    return initial,rows,final

class CopyAncestorTests(unittest.TestCase):
    def test_two_full_descendant_and_two_unrelated_components(self):
        p=recount(*fixture([[3,4],[5,6],[7,8],[9,10]]))[0]
        self.assertEqual(p['series'],{k:[2] for k in ('descendant_material','descendant_genetic','unrelated_material','unrelated_genetic')})
    def test_no_subgraph_cherry_picking_or_future_count(self):
        p=recount(*fixture([[3,4,5,6],[7,8]]))[0]
        self.assertEqual(p['series']['descendant_material'],[0])
        self.assertEqual(p['series']['unrelated_material'],[1])
    def test_mixed_target_ancestry_excluded(self):
        a=fixture([[3,4],[7,8]])
        a[2]['parents'][4]=2
        p=recount(*a)[0]
        self.assertEqual(p['series']['descendant_material'],[0])
        self.assertEqual(p['series']['unrelated_material'],[1])


class HistoricalRootTests(unittest.TestCase):
    def test_unrelated_can_mix_other_initial_parents(self):
        ids=[None]*256;units=[None]*256
        for i,site,program in [(0,0,0),(1,1,1),(2,8,2),(3,10,3)]:
            ids[site]=i;units[site]={'material':0,'program':[program]*4}
        initial=dict(site_ids=ids,units=units,observation={'components':{'material':[[0,1],[2],[3]]}})
        current=[None]*256;physical=[None]*256
        for i,site,program in [(4,64,0),(5,65,1)]:
            current[site]=i;physical[site]={'material':0,'program':[program]*4}
        rows=[dict(tick=1,site_ids=current,physical={'units':physical},observation={'components':{'material':[[4,5]]}})]
        final=dict(parents=[None,None,None,None,2,3],site_ids=current)
        p=recount(initial,rows,final)[0]
        self.assertEqual(p['series']['unrelated_genetic'],[1])
        self.assertEqual(p['series']['descendant_material'],[0])
        from scripts.analyze_v4_structure_copies import analyze
        self.assertEqual(analyze(initial,rows,final),[p])
    def test_dead_historical_founder_not_in_initial_world(self):
        initial,rows,final=fixture([[3,4],[7,8]])
        final['parents'].append(None)
        final['site_ids']=rows[-1]['site_ids']
        from scripts.analyze_v4_structure_copies import analyze
        self.assertEqual(recount(initial,rows,final),analyze(initial,rows,final))


class SummaryTests(unittest.TestCase):
    def records(self):
        from scripts.verify_v4_structure_copies import GRID,SERIES
        records=[]
        for h,s,m,e in GRID:
            parents=[]
            for i in range(0 if s==112004 else 2 if s==112000 else 1):
                series={k:([2]*10+[0]*390 if e and i==0 and k.startswith('descendant') else [0]*400) for k in SERIES}
                spans={k:intervals(v) for k,v in series.items()}
                parents.append(dict(component=i,anchor_members=[2*i,2*i+1],anchor_size=2,impossible_double=False,series=series,episodes=spans,longest={k:max((b-a+1 for a,b in v),default=0) for k,v in spans.items()}))
            records.append(dict(history=h,seed=s,mutation=m,exchange=e,parents=parents))
        return records
    def test_source_equal_weight_and_missingness(self):
        rows=make_results(self.records());summary=make_summary(rows)
        for group in summary['groups']:
            self.assertEqual(group['metrics']['descendant_genetic_persistent'],dict(mean='7/8',available=4,missing=1))
        from scripts.analyze_v4_structure_copies import summarize_records
        self.assertEqual(summarize_records(self.records()),(rows,summary))
    def test_invalid_grid_failure_and_threshold(self):
        records=self.records()
        with self.assertRaises(AssertionError):make_results(records[:-1])
        rows=make_results(records);rows[0]['status']='failed'
        with self.assertRaises(AssertionError):make_summary(rows)
        p=records[0]['parents'][0]
        for k in ('descendant_material','descendant_genetic'):
            p['series'][k]=[2]*9+[0]*391;p['episodes'][k]=[[1,9]];p['longest'][k]=9
        row=make_results(records)[0]
        self.assertEqual(row['counts']['descendant_genetic_ever'],1)
        self.assertEqual(row['counts']['descendant_genetic_persistent'],0)
