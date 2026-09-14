import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.driven_runner import run


class DrivenRunnerTests(unittest.TestCase):
    def test_replay_and_matched_initialization_and_drive_stream(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name,probability,exchange in (('a',500,True),('b',500,True),('off',0,True),('no_exchange',500,False)):
                result=run(root/name,90400,20,width=5,height=5,drive_per_thousand=probability,exchange=exchange)
                self.assertEqual(result['initial_energy']+result['imported']-result['spent'],result['final_energy'])
            for name in ('initial.json','steps.jsonl','final.json','summary.json'):
                self.assertEqual((root/'a'/name).read_bytes(),(root/'b'/name).read_bytes())
            for name in ('off','no_exchange'):
                self.assertEqual((root/name/'initial.json').read_bytes(),(root/'a/initial.json').read_bytes())
                a=json.loads((root/'a/final.json').read_text())
                b=json.loads((root/name/'final.json').read_text())
                self.assertEqual(a['drive_rng'],b['drive_rng'])
            self.assertEqual(json.loads((root/'off/summary.json').read_text())['imported'],0)

    def test_capacity_validation_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'bad'
            with self.assertRaises(ValueError):
                run(root,90401,10,capacity=10,max_energy=11)
            self.assertFalse(root.exists())


if __name__=='__main__':
    unittest.main()
