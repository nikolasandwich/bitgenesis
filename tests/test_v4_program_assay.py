import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.program_assay import run
from bitgenesis.v4.program_assay_audit import audit


class ProgramAssayTests(unittest.TestCase):
    def test_equal_program_replay_and_matched_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name,program in (('a',(0,1,2,3)),('b',(0,1,2,3)),('other',(3,2,1,0))):
                result=run(root/name,97000,program,20,width=5,height=5)
                self.assertEqual(audit(root/name)['summary'],result)
                self.assertEqual(result['mutations'],0)
            for name in ('initial.json','steps.jsonl','final.json','summary.json'):
                self.assertEqual((root/'a'/name).read_bytes(),(root/'b'/name).read_bytes())
            initial=json.loads((root/'a/initial.json').read_text())
            other=json.loads((root/'other/initial.json').read_text())
            self.assertEqual(sum(u is not None for u in initial['units']),1)
            self.assertEqual(initial['units'][12]['energy'],64)
            for state in (initial,other):
                state['units'][12].pop('program')
            self.assertEqual(initial,other)
            a=json.loads((root/'a/final.json').read_text())
            b=json.loads((root/'other/final.json').read_text())
            for key in ('drive_rng','direction_rng','mutation_rng'):
                self.assertEqual(a[key],b[key])

    def test_invalid_program_before_output_and_zero_horizon(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'run'
            with self.assertRaises(ValueError):
                run(root,97001,(0,1,2,4),0)
            self.assertFalse(root.exists())
            result=run(root,97001,(0,0,0,0),0)
            self.assertEqual(audit(root)['summary'],result)
            self.assertEqual(result['units'],1)
