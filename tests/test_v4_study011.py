from copy import deepcopy
from itertools import product
import unittest
from scripts.run_v4_study011 import aggregate,summarize,DEFINITIONS,METRICS


class DemographicSummaryTests(unittest.TestCase):
    def test_conditional_and_unconditional_denominators_and_empty_subset(self):
        records=[dict(category='stasis',births=0,deaths=0,original_deaths=0,descendant_deaths=0,whole_world_anchor=False),
                 dict(category='with_deaths',births=2,deaths=1,original_deaths=0,descendant_deaths=1,whole_world_anchor=True)]
        p=dict(phase='final',boundary='material',anchor=100,horizon=100,initial_multi_components=8,eligible_components=2,records=records)
        r=summarize([p])[0]
        self.assertEqual(r['fractions']['eligible_rate'],'1/4')
        self.assertEqual(r['fractions']['with_deaths'],'1/2')
        self.assertEqual(r['fractions']['with_original_deaths'],'0')
        self.assertEqual(r['event_totals']['births'],2)
        p.update(eligible_components=0,records=[])
        empty=summarize([p])[0]
        self.assertEqual(empty['fractions']['eligible_rate'],'0')
        self.assertIsNone(empty['fractions']['stasis'])

    def test_equal_anchor_then_source_means_missing_and_duplicate_panels(self):
        results=[]
        for seed,d,m in product(range(96000,96005),(250,500),(0,100)):
            rows=[]
            for (phase,boundary),a in product(DEFINITIONS,(100,200,300,400)):
                value=(None if a>200 else '1' if a==100 else '0') if seed==96000 else '0'
                rows.append(dict(phase=phase,boundary=boundary,anchor=a,horizon=100,fractions={k:value for k in METRICS}))
            results.append(dict(seed=seed,drive=d,mutation=m,summary=rows))
        r=aggregate(results)
        self.assertEqual(len(r['source_means']),100)
        self.assertEqual(len(r['groups']),20)
        self.assertTrue(all(g['metrics']['stasis']['mean']=='1/10' for g in r['groups']))
        self.assertEqual(r['source_means'][0]['metrics']['stasis']['missing'],2)
        with self.assertRaises(ValueError):aggregate(results[:-1])
        broken=deepcopy(results);broken[0]['summary'][-1]=broken[0]['summary'][0]
        with self.assertRaises(ValueError):aggregate(broken)

    def test_preflight_error_leaves_failed_record_without_measurement(self):
        import json,os,tempfile
        from pathlib import Path
        from unittest.mock import patch
        from scripts.run_v4_study011 import main
        current=Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder);Path('data').mkdir()
                with patch('scripts.run_v4_study011.subprocess.check_output',return_value=''), \
                     patch('scripts.run_v4_study011.digest',return_value='test'), \
                     patch('scripts.run_v4_study011.preflight',side_effect=ValueError('bad hash')), \
                     patch('scripts.run_v4_study011.observe') as observation:
                    with self.assertRaisesRegex(ValueError,'bad hash'):main()
                    observation.assert_not_called()
                m=json.loads(Path('data/v4-study-011/metadata.json').read_text())
                self.assertEqual((m['status'],m['completed_sources']),('failed',0))
            finally:os.chdir(current)


class VerificationCoverageTests(unittest.TestCase):
    def test_empty_missing_duplicate_and_unknown_rows_fail(self):
        from scripts.verify_v4_study011_summary import require_coverage
        expected={(1,'a'),(2,'b')}
        rows=[dict(seed=1,phase='a'),dict(seed=2,phase='b')]
        require_coverage(rows,('seed','phase'),expected)
        for bad in ([],rows[:1],[rows[0],rows[0]],rows+[rows[1]],[rows[0],dict(seed=3,phase='b')]):
            with self.assertRaises(ValueError):require_coverage(bad,('seed','phase'),expected)
