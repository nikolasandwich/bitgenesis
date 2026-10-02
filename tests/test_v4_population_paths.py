import unittest
from scripts.analyze_v4_population_paths import census, aggregate
from scripts.verify_v4_population_paths import recount


class PopulationPathsTests(unittest.TestCase):
    def fixture(self):
        initial=dict(site_ids=[0,None,1],units=[{},None,{}])
        rows=[dict(tick=1,site_ids=[2,None,1],physical=dict(units=[{},None,{}],material=dict(dissolved=[0],proposals=[dict(source=2,target=0,reason='formed')])))]
        final=dict(site_ids=[2,None,1],parents=[None,None,1])
        return initial,rows,final

    def test_same_site_death_birth_is_not_zero_events(self):
        i,r,f=self.fixture();a=census(i,r,f);b=recount(i,r,f)
        self.assertEqual(a,b)
        self.assertEqual(a[-1],dict(tick=1,occupied=2,births=1,deaths=1,original_survivors=1,new_survivors=1))

    def test_revival_rejected(self):
        i,r,f=self.fixture()
        r.append(dict(tick=2,site_ids=[0,None,1],physical=dict(units=[{},None,{}],material=dict(dissolved=[0],proposals=[dict(source=2,target=0,reason='formed')]))))
        f['site_ids']=[0,None,1]
        for fn in (census,recount):
            with self.assertRaises((ValueError,AssertionError)):fn(i,r,f)

    def test_missing_pair_rejected(self):
        with self.assertRaises(ValueError):aggregate([])

    def test_full_grid_exact_means_and_reverse_source(self):
        from scripts.verify_v4_population_paths import independent_summary
        from itertools import product
        branches=[]
        for seed,mut,anchor,exchange in product(range(96000,96005),(0,100),(100,200,300,400),(True,False)):
            path=[dict(tick=0,occupied=10,births=0,deaths=0,original_survivors=10,new_survivors=0)]
            change=(anchor//100)*(1 if seed!=96000 else -1) if exchange else 0
            for tick in range(1,101):path.append(dict(tick=tick,occupied=10+change,births=max(change,0),deaths=max(-change,0),original_survivors=10+min(change,0),new_survivors=max(change,0)))
            branches.append(dict(seed=seed,mutation=mut,anchor=anchor,exchange=exchange,path=path))
        result=aggregate(branches)
        self.assertEqual(result,independent_summary(branches))
        metric=result['groups'][0]['path'][100]['metrics']['occupied']
        self.assertEqual(metric,dict(on='23/2',off='10',difference='3/2',positive=16,zero=0,negative=4))
        self.assertEqual(result['sources'][0]['path'][100]['differences']['occupied'],'-5/2')
        with self.assertRaises(ValueError):aggregate(branches[:-1]+[branches[0]])

    def test_omitted_upstream_inventory_rejected(self):
        from unittest.mock import patch
        from pathlib import Path
        from scripts.population_path_inputs import bindings
        meta=dict(status='complete',completed_branches=80,planned_branches=80,bindings_sha256={},source_bindings_sha256={})
        with patch('scripts.population_path_inputs.read',side_effect=[meta,[],{}]),patch('scripts.population_path_inputs.expected_bindings',return_value=({Path('required')},set())):
            with self.assertRaisesRegex(ValueError,'binding inventory'):bindings()
