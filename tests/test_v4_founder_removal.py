import unittest
from copy import deepcopy
from scripts.run_v4_founder_removal import intervene, summarize_arm, match_copies
from bitgenesis.v4.lineage import Observer
from bitgenesis.v4.structure import snapshot


class FounderRemovalTests(unittest.TestCase):
    def test_removal_conserves_local_mass_exports_energy_preserves_history(self):
        units=[None]*256; raw=[0]*256
        for site in (85,86,117,118):units[site]=dict(material=0,energy=20,program=[0]*4)
        ob=Observer(units); ob.tick=6
        ob.individuals.append(dict(ob.individuals[-1],id=4,death_tick=5))
        before=deepcopy(ob.individuals)
        removed,exported=intervene(units,raw,ob)
        self.assertEqual(exported,40)
        self.assertEqual([r['identity'] for r in removed],[0,1])
        self.assertEqual(sum(raw)+sum(u is not None for u in units),4)
        self.assertEqual(ob.individuals,before)
        self.assertEqual(len(ob.individuals),5)
        self.assertEqual(ob.alive[85:87],[None,None])

    def test_diagnostic_not_counted_and_short_window_cannot_persist(self):
        final=dict(units=[],individuals=[])
        arm=dict(initial=dict(tick=24),rows=[],final=final)
        result=summarize_arm(arm,[])
        self.assertEqual(result['new_copy_counts'],[])
        self.assertEqual(result['metrics']['persistent10'],0)
        self.assertEqual(result['metrics']['formation_supported'],0)

    def test_matching_requires_whole_genetic_component_new_ids_and_root(self):
        units=[None]*256; ids=[None]*256
        for site,i in ((85,0),(86,1),(117,3),(118,4)):
            units[site]=dict(material=0,energy=20,program=[0]*4);ids[site]=i
        anchor=dict(units=deepcopy(units),site_ids=deepcopy(ids))
        individuals=[dict(parent=None,founder=i) for i in range(3)]+[dict(parent=0,founder=0),dict(parent=1,founder=1)]
        obs=snapshot(units,ids,16,16,phase='final')
        matches=match_copies(anchor,units,ids,obs,individuals)
        self.assertEqual([m['all_new'] for m in matches],[False,True])
        units[118]['program'][0]=1
        self.assertEqual(len(match_copies(anchor,units,ids,obs,individuals)),1)
        units[118]['program'][0]=0; units[119]=deepcopy(units[118]);ids[119]=5
        individuals.append(dict(parent=1,founder=1))
        self.assertEqual(len(match_copies(anchor,units,ids,snapshot(units,ids,16,16,phase='final'),individuals)),1)

    def test_formation_and_selected_ancestry_are_distinct_persistent_witnesses(self):
        people=[dict(parent=None,birth_tick=0,site=i) for i in range(2)]
        people += [dict(parent=0,birth_tick=4,site=117),dict(parent=1,birth_tick=4,site=118),
                   dict(parent=2,birth_tick=7,site=85),dict(parent=3,birth_tick=7,site=86)]
        copies=[dict(members=[2,3],sites=[117,118],all_new=True),dict(members=[4,5],sites=[85,86],all_new=True)]
        rows=[dict(tick=t,copies=deepcopy(copies),births=[],deaths=[],physical=dict(imported=0,spent=0)) for t in range(7,17)]
        arm=dict(initial=dict(tick=6),rows=rows,final=dict(units=[],individuals=people))
        r=summarize_arm(arm,[2,3])
        self.assertEqual(r['episodes'],[[7,16]])
        self.assertEqual(r['metrics']['persistent10'],1)
        self.assertEqual(r['metrics']['formation_persistent10'],1)
        self.assertEqual(r['metrics']['selected_ancestry_persistent10'],1)
        self.assertEqual(r['upper_witnesses'][0]['selected_ancestry'][0]['chain'],[4,2])
        people[4]['parent']=0
        r=summarize_arm(arm,[2,3])
        self.assertEqual(r['metrics']['formation_persistent10'],1)
        self.assertEqual(r['metrics']['selected_ancestry_supported'],0)
        arm['rows']=rows[:9]
        self.assertEqual(summarize_arm(arm,[2,3])['metrics']['persistent10'],0)

    def test_rebirth_uses_all_history_including_dead_identity_and_t0_birth(self):
        units=[None]*256
        for site in (85,86):units[site]=dict(material=0,energy=20,program=[0]*4)
        ob=Observer(units)
        ob._birth(117,5,0,[0]*4,4,0,False)
        ob.individuals[2]['death_tick']=6;ob.alive[117]=None
        ob._birth(118,6,0,[0]*4,4,1,False)
        ob.tick=6;units[118]=dict(material=0,energy=4,program=[0]*4)
        intervene(units,[0]*256,ob)
        units[85]=dict(material=0,energy=4,program=[0]*4)
        ob.accept(dict(tick=7,units=units,material=dict(dissolved=[],proposals=[dict(reason='formed',source=118,target=85,parent_program=[0]*4,child_program=[0]*4,material=0,child_energy=4,mutated=False)])))
        self.assertEqual(ob.alive[85],4)
        self.assertEqual(ob.individuals[4]['parent'],3)
        self.assertEqual(ob.individuals[2]['death_tick'],6)

    def test_synthetic_horizontal_zero_and_control_tamper_rejected(self):
        from scripts.run_v4_copy_control import run_case
        from scripts.run_v4_founder_removal import run_branch, _steps
        source=run_case('constructed-off');source.update(mode='random-feed',seed=1)
        ob=Observer(source['initial']['units']);selected=None
        for row in source['rows']:
            ob.accept(row['physical'])
            copies=match_copies(source['initial'],row['physical']['units'],ob.alive,row['observation'],ob.individuals)
            if any(c['all_new'] for c in copies):
                selected=dict(genotype='homogeneous',mode='random-feed',seed=1,exchange=False,eligible=True,
                              t0=row['tick'],remaining_steps=32-row['tick'],category='horizontal_structural_zero',
                              original_sites=[85,86],offspring_sites=[117,118],offspring_ids=[ob.alive[117],ob.alive[118]],
                              energy_export_preview=sum(row['physical']['units'][s]['energy'] for s in (85,86)))
                break
        self.assertIsNotNone(selected)
        result=run_branch(source,selected)
        self.assertEqual(result['ablation']['metrics']['double_new_ever'],0)
        self.assertTrue(all(r['site_ids'][85] is None and r['site_ids'][86] is None for r in result['ablation']['rows']))
        source['rows'][selected['t0']]['physical']['energy']+=1
        with self.assertRaisesRegex(ValueError,'control exact'):
            run_branch(source,selected)
        before=dict(_steps)
        def exhausted():raise ValueError('budget exhausted')
        with self.assertRaisesRegex(ValueError,'budget exhausted'):
            run_branch(source,selected,exhausted)
        self.assertEqual(before,_steps)
