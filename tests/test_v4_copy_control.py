import unittest
from scripts.run_v4_copy_control import run_case

class PhysicalControlTests(unittest.TestCase):
    def test_constructed_off_and_immutable_inputs(self):
        c=run_case('constructed-off');s=c['summary']
        self.assertTrue(s['persistent10']);self.assertEqual(s['births'],4)
        self.assertEqual(s['initial_mass'],7);self.assertEqual(s['final_mass'],7)
        self.assertEqual(s['initial_energy']+s['imported']-s['spent'],s['final_energy'])
        self.assertEqual(len(c['rows']),32)
        self.assertEqual(c['rows'][0]['physical']['directions'][85],2)
        self.assertEqual(c['rows'][1]['physical']['directions'][101],2)
        self.assertEqual(c['rows'][2]['physical']['directions'][101],0)
        self.assertEqual(c['rows'][2]['physical']['directions'][102],1)
        self.assertEqual(c['initial']['units'][85]['energy'],64)
    def test_no_raw_negative_and_on_case_complete(self):
        c=run_case('no-raw-off');s=c['summary']
        self.assertEqual(s['births'],0);self.assertFalse(s['persistent10'])
        self.assertEqual(s['genetic_counts'],[1]*32)
        self.assertEqual(s['initial_mass'],3)
        on=run_case('constructed-on')
        self.assertEqual(len(on['rows']),32);self.assertTrue(on['exchange'])
    def test_unknown_case_rejected(self):
        with self.assertRaises(ValueError):run_case('tuned-retry')

class ControlRunnerTests(unittest.TestCase):
    def test_unmet_expectation_preserves_all_cases(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from scripts import run_v4_copy_control as r
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'control'
            def case(name):return dict(summary=dict(name=name,persistent10=False,births=0))
            with patch.object(r,'OUTPUT',root),patch.object(r.subprocess,'check_output',side_effect=['','commit']),patch.object(r,'bindings',return_value={}),patch.object(r,'run_case',side_effect=case):r.main()
            meta=json.loads((root/'metadata.json').read_text())
            self.assertEqual(meta['status'],'complete');self.assertFalse(meta['expectations_met'])
            self.assertEqual(meta['completed_cases'],3);self.assertEqual(meta['new_simulation_steps'],96)
    def test_execution_error_preserves_completed_case(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from scripts import run_v4_copy_control as r
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'control'
            with patch.object(r,'OUTPUT',root),patch.object(r.subprocess,'check_output',side_effect=['','commit']),patch.object(r,'bindings',return_value={}),patch.object(r,'run_case',side_effect=[dict(summary={}),RuntimeError('case failed')]):
                with self.assertRaisesRegex(RuntimeError,'case failed'):r.main()
            meta=json.loads((root/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed');self.assertEqual(meta['completed_cases'],1)
            self.assertEqual(len(json.loads((root/'cases.json').read_text())),1)
    def test_budget_and_exclusive_output(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from scripts import run_v4_copy_control as r
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'control'
            with patch.object(r,'OUTPUT',root),patch.object(r.subprocess,'check_output',side_effect=['','commit']),patch.object(r,'bindings',return_value={}),patch.object(r.time,'monotonic',side_effect=[0,61,61,61]):
                with self.assertRaisesRegex(ValueError,'budget'):r.main()
            before=(root/'metadata.json').read_bytes();meta=json.loads(before)
            self.assertEqual(meta['status'],'failed');self.assertEqual(meta['completed_cases'],0)
            with patch.object(r,'OUTPUT',root),patch.object(r.subprocess,'check_output',return_value=''):
                with self.assertRaises(FileExistsError):r.main()
            self.assertEqual((root/'metadata.json').read_bytes(),before)
