import unittest
from copy import deepcopy
from scripts.analyze_v4_copy_episodes import analyze_case, phase_step, spans, summarize
from scripts.run_v4_copy_ablation import run_case

class EpisodesTest(unittest.TestCase):
    def test_compound_and_hidden(self):
        row=phase_step(4,[[0,1]],[[0,1],[3,4]],[[0,1]],[5],[2])
        self.assertEqual(row['crossings'],[True,False,False,True])
        self.assertTrue(row['hidden'])
        row=phase_step(4,[[0,1],[3,4]],[[0,1]],[[0,1],[3,5]],[5],[4])
        self.assertEqual(row['crossings'],[False,True,True,False])
        self.assertTrue(row['hidden'])
    def test_intervals(self):
        rows=[phase_step(i,[],[],([[1,2],[3,4]] if i in (2,4,5) else []),[],[]) for i in range(1,6)]
        e=spans(rows)
        self.assertEqual([(x['start'],x['end'],x['right_censored']) for x in e],[(2,2,False),(4,5,True)])
        self.assertEqual(e[0]['exit_step'],rows[2]);self.assertIsNone(e[1]['exit_step'])
    def test_real_and_event_tamper(self):
        x=run_case(120000,'random-feed',False)
        r=analyze_case(x)
        self.assertEqual([len(s['final']) for s in r['steps']],x['summary']['genetic_counts'])
        y=deepcopy(x)
        row=next(r for r in y['rows'] if r['physical']['material']['dissolved'])
        row['physical']['material']['dissolved']=[]
        with self.assertRaises((AssertionError,ValueError)):analyze_case(y)
    def test_grid_missing(self):
        with self.assertRaises((AssertionError,ValueError)):summarize([])

    def test_full_geometry_compound_and_exit(self):
        # Geometry/event fixture, not a native physics trajectory.
        def world(mapping):
            ids=[None]*256;units=[None]*256
            for i,site in mapping.items():
                ids[site]=i;m=3 if i==2 else 0
                units[site]=dict(material=m,energy=1,program=[m]*4)
            return ids,units
        initial={0:85,1:86,2:204}
        maps=[initial|{3:117,4:118,5:101},initial|{3:117,4:118,6:101},
              initial|{3:117,4:118},initial|{4:118}]
        maps+= [maps[-1]]*28
        prev=initial;rows=[];ids,units=world(initial)
        for t,mapping in enumerate(maps,1):
            ni,nu=world(mapping)
            rows.append(dict(tick=t,site_ids=ni,physical=dict(units=nu,material=dict(
                dissolved=[prev[i] for i in prev.keys()-mapping.keys()],proposals=[dict(reason='formed',source=85,target=mapping[i]) for i in sorted(mapping.keys()-prev.keys())]))))
            prev=mapping
        case=dict(seed=120000,mode='random-direction',exchange=False,initial=dict(site_ids=ids,units=units),rows=rows,
                  final=dict(site_ids=ni,units=nu,parents=[None,None,None,0,0,0,0]),summary=dict(genetic_counts=[0,0,2]+[1]*29,episodes=[[3,3]]))
        result=analyze_case(case)
        self.assertEqual(result['steps'][1]['dissolved'],[[0,1],[3,4]])
        self.assertEqual(result['steps'][1]['crossings'],[True,False,False,True])
        self.assertTrue(result['steps'][1]['hidden'])
        self.assertEqual(result['steps'][2]['crossings'],[True,False,False,False])
        self.assertEqual(result['steps'][3]['crossings'],[False,True,False,False])
        self.assertFalse(result['episodes'][0]['right_censored'])
        self.assertEqual(result['episodes'][0]['exit_step'],result['steps'][3])
