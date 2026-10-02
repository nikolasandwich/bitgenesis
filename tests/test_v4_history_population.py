import unittest
from itertools import product
from scripts.analyze_v4_history_population import census,aggregate


def grid():
    result=[]
    for history,seed,mutation,anchor,exchange in product((True,False),range(112000,112005),(0,100),(100,200,300,400),(True,False)):
        path=[]
        for tick in range(101):
            # Distinct historical initial populations, common within each pair.
            initial=20 if history else 40
            births=(2 if history else 3)*(tick//2) if exchange else tick//2
            path.append(dict(tick=tick,occupied=initial+births,births=births,deaths=0,original_survivors=initial,new_survivors=births))
        result.append(dict(history=history,seed=seed,mutation=mutation,anchor=anchor,exchange=exchange,path=path))
    return result


class HistoryPopulationTests(unittest.TestCase):
    def test_different_initials_do_not_enter_history_effect(self):
        s=aggregate(grid());a=s['interaction']['groups'][0]['path'][100]['metrics']['occupied']
        self.assertEqual(a,dict(on_history='50',off_history='100',difference='50',positive=20,zero=0,negative=0))
        self.assertEqual(s['interaction']['groups'][0]['path'][0]['metrics']['occupied']['difference'],'0')

    def test_incomplete_grid_and_unpaired_initials_rejected(self):
        rows=grid()
        for bad in (rows[:-1],rows[:-1]+[rows[0]]):
            with self.assertRaises(ValueError):aggregate(bad)
        rows[0]['path'][0]['occupied']+=1
        with self.assertRaises(ValueError):aggregate(rows)

    def test_same_site_death_replacement_and_resurrection(self):
        initial=dict(site_ids=[0,1]);final=dict(site_ids=[2,1],parents=[None,None,1])
        first=dict(tick=1,site_ids=[2,1],physical=dict(units=[{},{}],material=dict(dissolved=[0],proposals=[dict(reason='formed',source=1,target=0)])))
        path=census(initial,[first],final)
        self.assertEqual(path[1],dict(tick=1,occupied=2,births=1,deaths=1,original_survivors=1,new_survivors=1))
        second=dict(tick=2,site_ids=[0,1],physical=dict(units=[{},{}],material=dict(dissolved=[0],proposals=[dict(reason='formed',source=1,target=0)])))
        with self.assertRaises(ValueError):census(initial,[first,second],dict(site_ids=[0,1],parents=[None,None,1]))

    def test_failure_budget_and_exclusive_output(self):
        from scripts import analyze_v4_history_population as runner
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from contextlib import ExitStack
        import json
        with TemporaryDirectory() as tmp:
            for mode in ('fail','time'):
                output=Path(tmp)/mode
                with ExitStack() as stack:
                    stack.enter_context(patch.object(runner,'OUTPUT',output))
                    stack.enter_context(patch.object(runner.subprocess,'check_output',side_effect=['','revision']))
                    stack.enter_context(patch.object(runner,'bindings',side_effect=ValueError('binding mismatch') if mode=='fail' else None,return_value={}))
                    stack.enter_context(patch.object(runner,'grid',return_value=[dict(directory='must-not-read')]))
                    if mode=='fail':
                        with self.assertRaisesRegex(ValueError,'binding mismatch'):runner.main()
                    else:
                        stack.enter_context(patch.object(runner,'SECONDS',-1));runner.main()
                meta=json.loads((output/'metadata.json').read_text());self.assertEqual(meta['status'],'failed' if mode=='fail' else 'time_limit')
                before=(output/'metadata.json').read_bytes()
                with patch.object(runner,'OUTPUT',output),patch.object(runner.subprocess,'check_output',return_value=''):
                    with self.assertRaises(FileExistsError):runner.main()
                self.assertEqual(before,(output/'metadata.json').read_bytes())
