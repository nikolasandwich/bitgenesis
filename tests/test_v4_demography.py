import unittest
from bitgenesis.v4.structure_demography import measure


def life(identity, parent=None, birth=0, death=None):
    return dict(id=identity,parent=parent,birth_tick=birth,death_tick=death)


class DemographyTests(unittest.TestCase):
    def test_hidden_short_lived_child_and_original_death(self):
        lives=[life(0),life(1,death=3),life(2,0,2,3),life(3,0,3)]
        r=measure(lives,[0,1],[0,1],'final',1,2)
        self.assertEqual((r['births'],r['deaths'],r['original_deaths'],r['descendant_deaths']), (2,2,1,1))
        self.assertEqual(r['birth_ids'],[2,3])
        self.assertEqual(r['death_ids'],[1,2])
        self.assertEqual(r['original_survivors_by_snapshot'],[2,2,1])
        self.assertEqual(r['endpoint_population'],2)
        self.assertEqual(r['category'],'with_deaths')

    def test_interaction_window_includes_anchor_events_excludes_last_tick(self):
        lives=[life(0),life(1),life(2,0,2),life(3,0,3)]
        early=measure(lives,[0,1],[0,1],'interaction',2,1)
        self.assertEqual(early['birth_ids'],[2])
        late=measure(lives,[0,1,2],[0,1],'final',2,1)
        self.assertEqual(late['birth_ids'],[3])
        self.assertEqual(early['category'],'births_only')

    def test_anchor_parent_child_cut_static_and_invalid_anchor(self):
        lives=[life(0),life(1,0,1),life(2,1,2),life(3,0,2)]
        parent=measure(lives,[0,1],[0],'final',1,1)
        child=measure(lives,[0,1],[1],'final',1,1)
        self.assertEqual(parent['birth_ids'],[3])
        self.assertEqual(child['birth_ids'],[2])
        static=measure([life(0),life(1)],[0,1],[0,1],'final',1,2)
        self.assertEqual(static['category'],'stasis')
        with self.assertRaises(ValueError):
            measure(lives,[0],[0],'final',1,1)
        with self.assertRaises(ValueError):
            measure([life(0,1),life(1,0)],[0,1],[0,1],'final',1,1)


class DemographyIntegrationTests(unittest.TestCase):
    def test_short_engineering_trace_both_phases_empty_subset_and_corruption(self):
        import tempfile
        from pathlib import Path
        from copy import deepcopy
        from hashlib import sha256
        from bitgenesis.v4.hereditary_runner import run
        from bitgenesis.v4.structure_trace import trace
        from bitgenesis.v4.lineage import trace as lineage
        from bitgenesis.v4.structure_continuity import analyze
        from bitgenesis.v4.structure_demography import observe
        from bitgenesis.v4.demography_audit import check
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'engineering'
            run(root,104000,8,width=4,height=4,occupancy=750)
            before={p.name:sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
            observed=trace(root);lives=lineage(root)['individuals']
            parents=[r['parent'] for r in lives]
            old=analyze(observed,parents,anchors=(2,4),horizons=(2,))
            result=observe(lives,observed,old,horizon=2)
            audit=check(root,observed,old,result,horizon=2)
            self.assertEqual(audit['panels'],10)
            self.assertGreater(audit['cohort_windows'],0)
            altered=deepcopy(result)
            record=next(p['records'][0] for p in altered if p['records'])
            record['births']+=1
            with self.assertRaises(ValueError):check(root,observed,old,altered,horizon=2)
            empty=deepcopy(old)
            for panel in empty:
                for record in panel['records']:record['continuous_closed_multi']=False
            blank=observe(lives,observed,empty,horizon=2)
            self.assertEqual(check(root,observed,empty,blank,horizon=2)['cohort_windows'],0)
            self.assertTrue(all(p['records']==[] for p in blank))
            self.assertEqual(before,{p.name:sha256(p.read_bytes()).hexdigest() for p in root.iterdir()})
