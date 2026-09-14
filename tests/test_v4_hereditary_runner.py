import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.hereditary_runner import run
from bitgenesis.v4.hereditary_audit import audit


class HereditaryRunnerTests(unittest.TestCase):
    def test_replay_and_mutation_control_streams(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name,mutation in (('a',1000),('b',1000),('off',0)):
                summary=run(root/name,95002,20,width=4,height=4,occupancy=250,mutation_per_thousand=mutation)
                self.assertEqual(audit(root/name)['summary'],summary)
                self.assertEqual(summary['initial_energy']+summary['imported']-summary['spent'],summary['final_energy'])
                self.assertEqual(summary['copy_spent'],summary['formations'])
                self.assertEqual(summary['mutations'],summary['formations'] if mutation else 0)
            for name in ('initial.json','steps.jsonl','final.json','summary.json'):
                self.assertEqual((root/'a'/name).read_bytes(),(root/'b'/name).read_bytes())
            self.assertEqual((root/'a/initial.json').read_bytes(),(root/'off/initial.json').read_bytes())
            a=json.loads((root/'a/final.json').read_text())
            b=json.loads((root/'off/final.json').read_text())
            for key in ('mutation_rng','drive_rng','direction_rng'):
                self.assertEqual(a[key],b[key])

    def test_zero_horizon_and_cost_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'run'
            with self.assertRaises(ValueError):
                run(root,95003,0,threshold=6)
            self.assertFalse(root.exists())
            summary=run(root,95003,0,program_mode='constant')
            self.assertEqual(audit(root)['summary'],summary)
            self.assertEqual(summary['copy_spent'],0)
            self.assertEqual(summary['mutations'],0)
            initial=json.loads((root/'initial.json').read_text())
            self.assertTrue(all(u is None or u['program']==[u['material']]*4 for u in initial['units']))
