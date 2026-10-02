import unittest
from itertools import product
from scripts.run_v4_study015 import aggregate


def grid():
    rows=[]
    for seed,m,a,ex in product(range(112000,112005),(0,100),(100,200,300,400),(True,False)):
        fractions={k:None for k in ('continuous','replacement','endpoint_closed','lineage_survival','original_retention','descendants')}
        rows.append(dict(seed=seed,mutation=m,anchor=a,exchange=ex,status='complete',occupied=2 if ex else 1,components=dict(initial_components=1,eligible_components=0,fractions=fractions)))
    return rows


class HistoryStudyTests(unittest.TestCase):
    def test_anchor_intersection_not_difference_of_available_means(self):
        old,new=grid(),grid()
        for rows,values in ((old,['1',None,'1','1']),(new,[None,'1',None,'3'])):
            for r in rows:
                if r['seed']!=112000:continue
                v=values[r['anchor']//100-1]
                r['components']['eligible_components']=1 if v else 0
                r['components']['fractions']['descendants']=(v if r['exchange'] else '0') if v else None
        s=aggregate(new,old)
        self.assertEqual(s['interaction']['groups'][0]['metrics']['descendants'],dict(mean='2',available=1,missing=4))
        self.assertEqual(s['interaction']['sources'][0]['metrics']['descendants'],dict(mean='2',available=1,missing=3))
        self.assertEqual(s['histories']['off']['sources'][0]['metrics']['descendants']['mean'],'2')
        self.assertEqual(s['histories']['on']['sources'][0]['metrics']['descendants']['mean'],'1')

    def test_world_counts_survive_empty_components_and_missing_grid_errors(self):
        old,new=grid(),grid()
        new[0]['occupied']=0
        result=aggregate(new,old)
        self.assertEqual(result['interaction']['sources'][0]['metrics']['occupied']['mean'],'-1/2')
        self.assertEqual(result['interaction']['groups'][0]['metrics']['occupied']['mean'],'-1/10')
        self.assertIsNone(result['interaction']['groups'][0]['metrics']['continuous']['mean'])
        for a,b in ((new[:-1],old),(new,old[:-1]),(new[:-1]+[new[0]],old)):
            with self.assertRaises(ValueError):aggregate(a,b)
        new[0]['status']='failed'
        with self.assertRaises(ValueError):aggregate(new,old)

    def test_bound_input_failure_budget_and_exclusive_outputs(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from contextlib import ExitStack
        from scripts import run_v4_study015 as runner
        with tempfile.TemporaryDirectory() as temp:
            for mode in ('failure','time','changed'):
                root=Path(temp)/mode
                with ExitStack() as stack:
                    stack.enter_context(patch.object(runner,'ROOT',root))
                    stack.enter_context(patch.object(runner,'code_paths',return_value=[]))
                    stack.enter_context(patch.object(runner,'old_bindings',return_value={}))
                    stack.enter_context(patch.object(runner,'verify_old',side_effect=ValueError('old input changed') if mode=='changed' else None))
                    stack.enter_context(patch.object(runner.subprocess,'check_output',side_effect=['','test']))
                    call=stack.enter_context(patch.object(runner,'baseline_run',side_effect=ValueError('baseline failed')))
                    if mode=='time':
                        stack.enter_context(patch.object(runner,'SECONDS',-1))
                        runner.main();call.assert_not_called()
                    else:
                        with self.assertRaisesRegex(ValueError,'old input changed' if mode=='changed' else 'baseline failed'):runner.main()
                        if mode=='changed':call.assert_not_called()
                meta=json.loads((root/'metadata.json').read_text())
                self.assertEqual(meta['status'],'time_limit' if mode=='time' else 'failed')
                self.assertEqual(meta['completed_sources'],0)
                before=(root/'metadata.json').read_bytes()
                with patch.object(runner,'ROOT',root),patch.object(runner.subprocess,'check_output',return_value=''):
                    with self.assertRaises(FileExistsError):runner.main()
                self.assertEqual(before,(root/'metadata.json').read_bytes())
