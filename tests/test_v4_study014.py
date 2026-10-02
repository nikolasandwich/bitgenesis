import unittest
from fractions import Fraction
from itertools import product
from scripts.run_v4_study014 import aggregate

class ReplicationTests(unittest.TestCase):
    def grid(self):
        result=[]
        for seed,mutation,anchor,flag in product(range(112000,112005),(0,100),(100,200,300,400),(True,False)):
            fractions={k:None for k in ('continuous','replacement','endpoint_closed','lineage_survival','original_retention','descendants')}
            result.append(dict(seed=seed,mutation=mutation,anchor=anchor,exchange=flag,status='complete',occupied=(anchor//100 if flag else 0),components=dict(initial_components=1,eligible_components=0,fractions=fractions)))
        return result

    def test_world_count_retained_when_component_denominator_empty(self):
        s=aggregate(self.grid())
        self.assertEqual(s['groups'][0]['metrics']['occupied'],dict(mean='5/2',available=5,missing=0))
        self.assertEqual(s['groups'][0]['metrics']['continuous'],dict(mean=None,available=0,missing=5))

    def test_incomplete_and_duplicate_rejected(self):
        rows=self.grid()
        for bad in (rows[:-1],rows[:-1]+[rows[0]]):
            with self.assertRaises(ValueError):aggregate(bad)
        rows[0]['status']='failed'
        with self.assertRaises(ValueError):aggregate(rows)

    def test_secondary_means_and_independent_aggregation(self):
        from scripts.verify_v4_study014_summary import aggregate_saved
        rows=self.grid()
        for r in rows:
            r['components'].update(initial_components=2,eligible_components=2)
            r['components']['fractions']={k:'0' for k in r['components']['fractions']}
            r['components']['fractions']['continuous']=('0' if r['seed']==112000 else '1/2') if r['exchange'] else '1/4'
        a=aggregate(rows);self.assertEqual(a,aggregate_saved(rows))
        self.assertEqual(a['groups'][0]['metrics']['continuous']['mean'],'3/20')
        self.assertEqual(a['sources'][0]['metrics']['continuous']['mean'],'-1/4')

    def test_failure_limit_and_exclusive_outputs(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from scripts import run_v4_study014 as runner
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'failure'
            with patch.object(runner,'ROOT',root),patch.object(runner,'code_paths',return_value=[]),patch.object(runner.subprocess,'check_output',side_effect=['','test']),patch.object(runner,'baseline_run',side_effect=ValueError('baseline failed')):
                with self.assertRaisesRegex(ValueError,'baseline failed'):runner.main()
            m=json.loads((root/'metadata.json').read_text());self.assertEqual(m['status'],'failed');self.assertEqual(m['completed_sources'],0)
            before=(root/'metadata.json').read_bytes()
            with patch.object(runner,'ROOT',root),patch.object(runner.subprocess,'check_output',return_value=''):
                with self.assertRaises(FileExistsError):runner.main()
            self.assertEqual(before,(root/'metadata.json').read_bytes())
            root=Path(tmp)/'limited'
            with patch.object(runner,'ROOT',root),patch.object(runner,'SECONDS',-1),patch.object(runner,'code_paths',return_value=[]),patch.object(runner.subprocess,'check_output',side_effect=['','test']),patch.object(runner,'baseline_run') as call:
                runner.main();call.assert_not_called()
            self.assertEqual(json.loads((root/'metadata.json').read_text())['status'],'time_limit')
