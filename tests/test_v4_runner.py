import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.runner import run


class LocalRunnerTests(unittest.TestCase):
    def test_replay_records_and_energy(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name in ('a','b'):
                summary=run(root/name,90100,30,width=5,height=5)
            for name in ('initial.json','steps.jsonl','final.json','summary.json'):
                self.assertEqual((root/'a'/name).read_bytes(),(root/'b'/name).read_bytes())
            self.assertEqual(summary['initial_energy']-summary['spent'],summary['final_energy'])
            for line in (root/'a/steps.jsonl').read_text().splitlines():
                row=json.loads(line)
                self.assertEqual(sum(u['energy'] for u in row['units'] if u),row['energy'])
                self.assertEqual(sorted(i for group in row['components'] for i in group),
                                 [i for i,u in enumerate(row['units']) if u is not None])

    def test_empty_zero_horizon_and_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            summary=run(root/'empty',90101,0,width=3,height=3,occupancy=0)
            self.assertEqual(summary['units'],0)
            self.assertIsNone(summary['last_transition_bonds'])
            with self.assertRaises(ValueError):
                run(root/'bad',90101,10,width=3,height=3,max_site_records=98)
            self.assertFalse((root/'bad').exists())
            with self.assertRaises(FileExistsError):
                run(root/'empty',90101,0)


if __name__=='__main__':
    unittest.main()
