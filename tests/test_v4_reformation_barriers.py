import unittest
from copy import deepcopy
from scripts.analyze_v4_reformation_barriers import observe, spans, summarize, analyze_case, FLAGS


def person(i, parent=None, birth=0):
    return dict(id=i, parent=parent, birth_tick=birth, death_tick=None, site=85+i, material=0, program=[0]*4)


class BarrierTests(unittest.TestCase):
    def state(self, extra=False, mismatch=False):
        ids=[None]*256; units=[None]*256
        for s,i in [(85,3),(86,4)]+([(101,5)] if extra else []):
            ids[s]=i;units[s]=dict(material=0,program=[0]*4,energy=1)
        if mismatch:units[86]['program']=[0,0,0,1]
        people=[person(0),person(1),person(2),person(3,0,2),person(4,1,3),person(5,3,4)]
        return units,ids,people

    def test_independent_program_component_and_ancestry(self):
        template=[dict(material=0,program=[0]*4)]*2
        for extra,mismatch in [(False,False),(True,False),(False,True)]:
            u,i,p=self.state(extra,mismatch)
            r=observe(5,u,i,p,template,[3,4],1)
            s=r['slots'][0]
            self.assertEqual(s['genetic_match'],not mismatch)
            self.assertEqual(s['whole_component'],not extra)
            self.assertTrue(s['selected_ancestry']);self.assertTrue(s['post_birth'])
            self.assertEqual(r['upper_failure'],'program' if mismatch else 'component' if extra else 'pass')
            self.assertEqual(r['connector_sites'],[101] if extra else [])

    def test_missing_clears_all_eight(self):
        u,i,p=self.state();u[86]=None;i[86]=None
        r=observe(5,u,i,p,[dict(material=0,program=[0]*4)]*2,[3,4],1)
        self.assertFalse(any(r['slots'][0][f] for f in FLAGS))
        self.assertEqual(r['upper_failure'],'missing')

    def test_episodes_censor_and_threshold(self):
        self.assertEqual(spans([(5,True),(6,False),(7,True)]),[dict(start=5,end=5,length=1,right_censored=False),dict(start=7,end=7,length=1,right_censored=True)])
        self.assertEqual(spans([(i,True) for i in range(10,20)])[0]['length'],10)
        self.assertEqual(spans([(1,False)]),[])

    def test_diagnostic_excluded_no_false_enter_and_ten_steps(self):
        u,ids,people=self.state()
        t0=22
        rows=[dict(tick=t,physical=dict(units=deepcopy(u)),site_ids=list(ids),births=[],deaths=[]) for t in range(23,33)]
        source_ids=[None]*256;source_ids[85:87]=[0,1]
        source=dict(initial=dict(units=deepcopy(u),site_ids=source_ids))
        selection=dict(mode='random-direction',exchange=False,category='remaining_conditional',genotype='homogeneous',t0=t0,remaining_steps=10,offspring_ids=[3,4])
        branch=dict(selection=selection,ablation=dict(initial=dict(tick=t0,units=u,site_ids=ids),final=dict(individuals=people),rows=rows,new_copy_counts=[1]*10,episodes=[]))
        record=analyze_case(branch,source)
        self.assertEqual(record['transitions'],[])
        self.assertEqual(record['longest']['upper_new_copy'],10)
        self.assertEqual(record['longest']['upper_selected_post_copy'],0)
        self.assertTrue(record['episodes']['upper_new_copy'][0]['right_censored'])
        summary=summarize([record])['overall']
        self.assertEqual(summary['saved_steps'],10)
        self.assertEqual(summary['persistence']['upper_new_copy']['cases_persistent10'],1)
        self.assertEqual(summary['flags']['occupied'],10)
        # A natural death exits at the first future state; the diagnostic is baseline only.
        people[4]['death_tick']=23
        for row in rows:
            row['physical']['units'][86]=None;row['site_ids'][86]=None
        rows[0]['deaths']=[4];branch['ablation']['new_copy_counts']=[0]*10
        record=analyze_case(branch,source)
        self.assertEqual(len(record['transitions']),1)
        event=record['transitions'][0]
        self.assertEqual((event['tick'],event['direction']),(23,'exit'))
        self.assertEqual(event['deaths'][0]['identity'],4)
        self.assertEqual(record['episodes']['upper_new_copy'],[])

    def test_enter_events_include_births_and_both_metrics(self):
        u,ids,people=self.state()
        for p,site in zip(people[3:5],(85,86)):
            p['birth_tick']=32;p['site']=site
        for identity,site in ((5,117),(6,118)):
            p=person(identity,0,1);p['site']=site;people.append(p)
            u[site]=dict(material=0,program=[0]*4,energy=1);ids[site]=identity
        initial_u=deepcopy(u);initial_ids=list(ids)
        for site in (85,86):initial_u[site]=None;initial_ids[site]=None
        source_ids=[None]*256;source_ids[85:87]=[0,1]
        source=dict(initial=dict(units=deepcopy(u),site_ids=source_ids))
        branch=dict(selection=dict(mode='random-direction',exchange=False,category='short_window',genotype='homogeneous',t0=31,remaining_steps=1,offspring_ids=[5,6]),ablation=dict(initial=dict(tick=31,units=initial_u,site_ids=initial_ids),final=dict(individuals=people),rows=[dict(tick=32,physical=dict(units=u),site_ids=ids,births=people[3:5],deaths=[])],new_copy_counts=[2],episodes=[[32,32]]))
        result=analyze_case(branch,source)
        self.assertEqual([e['metric'] for e in result['transitions']],['upper_new_copy','double_new'])
        self.assertTrue(all(e['direction']=='enter' for e in result['transitions']))
        self.assertEqual([b['identity'] for b in result['rows'][0]['births']],[3,4])
        self.assertEqual(result['longest']['double_new'],1)
        self.assertTrue(result['episodes']['double_new'][0]['right_censored'])

    def test_selected_root_and_birth_predicates_are_distinct(self):
        u,ids,p=self.state();p[3]['parent']=2
        row=observe(5,u,ids,p,[dict(material=0,program=[0]*4)]*2,[3,4],2)
        upper=row['slots'][0]
        self.assertTrue(upper['selected_ancestry'])
        self.assertFalse(upper['root_descendant']);self.assertFalse(upper['post_birth'])
        self.assertTrue(upper['all_new']);self.assertFalse(upper['copy'])
        self.assertEqual(row['upper_failure'],'ancestry_root')

    def test_summary_empty_zero_cells(self):
        s=summarize([])
        self.assertEqual(len(s['cells']),4)
        self.assertEqual(s['overall']['saved_steps'],0)
        self.assertEqual(set(s['overall']['flags']),set(FLAGS))

if __name__=='__main__':unittest.main()
