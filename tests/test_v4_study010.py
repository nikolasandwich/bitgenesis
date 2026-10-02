from copy import deepcopy
from itertools import product
import unittest
from scripts.run_v4_study010 import aggregate, average, panel_summary, METRICS
from bitgenesis.v4.structure_continuity import follow


class Study010Tests(unittest.TestCase):
    def test_equal_anchor_then_source_weight_and_null_coverage(self):
        definitions = (('interaction','contact'),('interaction','material'),('interaction','bond'),
                       ('final','contact'),('final','material'))
        results = []
        for seed,drive,mutation in product(range(96000,96005),(250,500),(0,100)):
            rows = []
            for (phase,boundary),anchor,horizon,stratum in product(definitions,(100,200,300,400),(10,50,100),('singleton','multi')):
                value = (None if anchor>=300 else '1' if anchor==100 else '0') if seed==96000 else '0'
                rows.append(dict(phase=phase,boundary=boundary,anchor=anchor,horizon=horizon,stratum=stratum,
                                 fractions={k:value for k in METRICS}))
            results.append(dict(seed=seed,drive=drive,mutation=mutation,summary=rows))
        result = aggregate(results)
        self.assertEqual(len(result['source_means']),600)
        self.assertEqual(len(result['groups']),120)
        self.assertTrue(all(r['metrics']['primary']['mean']=='1/10' for r in result['groups']))
        self.assertEqual(result['source_means'][0]['metrics']['primary'],dict(mean='1/2',available=2,missing=2))
        for broken in (results[:-1],results[:-1]+[results[0]]):
            with self.assertRaises(ValueError): aggregate(broken)
        broken=deepcopy(results)
        broken[0]['summary'][-1]=broken[0]['summary'][0]
        with self.assertRaises(ValueError): aggregate(broken)
        self.assertEqual(average([None,None]),dict(mean=None,available=0,missing=2))

    def test_nonempty_denominators_and_static_world_are_not_primary(self):
        record = follow({1:[[0,1]],2:[[0,1]]},[None,None],1,(1,))[1]
        panels=[dict(phase='final',boundary='contact',anchor=1,horizon=1,records=record)]
        singleton,multi=panel_summary(panels)
        self.assertEqual(singleton['components'],0)
        self.assertTrue(all(v is None for v in singleton['fractions'].values()))
        self.assertEqual(multi['counts']['whole_world_anchor'],1)
        self.assertEqual(multi['counts']['continuous_closed_multi'],1)
        self.assertEqual(multi['counts']['primary'],0)
        self.assertEqual(multi['original_survivors'],2)


class LaunchFailureTests(unittest.TestCase):
    def test_rejected_preflight_is_persisted_without_measurement(self):
        import json
        import os
        from pathlib import Path
        import tempfile
        from unittest.mock import patch
        from scripts.run_v4_study010 import main
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                Path('data').mkdir()
                with patch('scripts.run_v4_study010.subprocess.check_output', return_value=''), \
                     patch('scripts.run_v4_study010.digest', return_value='test-hash'), \
                     patch('scripts.run_v4_study010.sources', side_effect=ValueError('broken source hash')), \
                     patch('scripts.run_v4_study010.analyze') as measure:
                    with self.assertRaisesRegex(ValueError, 'broken source hash'):
                        main()
                    measure.assert_not_called()
                meta = json.loads(Path('data/v4-study-010/metadata.json').read_text())
                self.assertEqual(meta['status'], 'failed')
                self.assertEqual(meta['completed_sources'], 0)
                self.assertIn('broken source hash', meta['error'])
                self.assertFalse(Path('data/v4-study-010/results.json').exists())
            finally:
                os.chdir(original)
