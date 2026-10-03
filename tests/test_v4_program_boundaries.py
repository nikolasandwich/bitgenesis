import unittest
from copy import deepcopy
from scripts import analyze_v4_program_boundaries as a
from scripts.run_v4_copy_ablation import run_case

class BoundaryTests(unittest.TestCase):
    def test_events_and_tamper(self):
        c=run_case(120000,'random-direction',False)
        r=a.analyze_case(c,'homogeneous')
        self.assertEqual(sum(map(len,r['formations'])),c['summary']['births'])
        self.assertEqual([s['final'] for s in r['phases']['steps']],[[g['members'] for g in s['copies']] for s in r['members']['steps']])
        bad=deepcopy(c);bad['summary']['genetic_counts'][0]=99
        with self.assertRaises(ValueError):a.analyze_case(bad,'homogeneous')
    def test_grid(self):
        with self.assertRaises(ValueError):a.summarize([])
        with self.assertRaises(ValueError):a.analyze_case({},'invalid')
    def test_failure_keeps_provenance(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from unittest.mock import patch
        import json
        from scripts import program_boundary_inputs as io
        with TemporaryDirectory() as d:
            out=Path(d)/'out'
            with patch.object(a,'OUTPUT',out),patch.object(a.subprocess,'check_output',side_effect=['','a'*40]),patch.object(io,'bindings',return_value={'source':'hash'}),patch.object(io,'source_cases',return_value=[('homogeneous',Path('missing'))]),patch.object(io,'read',side_effect=ValueError('source failure')):
                with self.assertRaisesRegex(ValueError,'source failure'):a.main()
            m=json.loads((out/'metadata.json').read_text())
            self.assertEqual(m['status'],'failed');self.assertEqual(m['input_sha256'],m['input_sha256_after']);self.assertEqual(m['completed_cases'],0)

    def test_changed_source_finalization(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from unittest.mock import patch
        import json
        from scripts import program_boundary_inputs as io
        with TemporaryDirectory() as d:
            source=Path(d)/'source';source.write_text('changed');out=Path(d)/'out'
            with patch.object(a,'OUTPUT',out),patch.object(a.subprocess,'check_output',side_effect=['','a'*40]),patch.object(io,'bindings',side_effect=[{str(source):'old'},AssertionError('changed')]),patch.object(io,'source_cases',return_value=[('homogeneous',source)]),patch.object(io,'read',side_effect=ValueError('source failure')):
                with self.assertRaises(ValueError):a.main()
            m=json.loads((out/'metadata.json').read_text())
            self.assertEqual(m['input_sha256_after'][str(source)],io.digest(source))
            self.assertIn('changed',m['finalization_error'])
