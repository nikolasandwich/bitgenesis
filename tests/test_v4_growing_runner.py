import json
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v4.growing_runner import run
from bitgenesis.v4.growing_audit import audit


class GrowingRunnerTests(unittest.TestCase):
    def test_replay_matched_streams_and_material_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, probability, exchange in (
                ('a', 500, True), ('b', 500, True), ('off', 0, True),
                ('no_exchange', 500, False)
            ):
                summary = run(root/name, 90601, 30, width=5, height=5,
                              drive_per_thousand=probability, exchange=exchange)
                self.assertEqual(audit(root/name)['summary'], summary)
                initial = json.loads((root/name/'initial.json').read_text())
                population = sum(u is not None for u in initial['units'])
                mass = sum(initial['raw']) + population
                energy = sum(u['energy'] for u in initial['units'] if u is not None)
                rows = [json.loads(s) for s in (root/name/'steps.jsonl').read_text().splitlines()]
                self.assertEqual([r['tick'] for r in rows], list(range(1, 31)))
                for row in rows:
                    energy += row['imported'] - row['spent']
                    population += sum(p['reason'] == 'formed' for p in row['material']['proposals'])
                    population -= len(row['material']['dissolved'])
                    self.assertEqual(sum(u is not None for u in row['units']), population)
                    self.assertEqual(sum(row['raw']) + population, mass)
                    self.assertEqual(sum(u['energy'] for u in row['units'] if u is not None), energy)
                self.assertEqual(summary['units'], population)
                self.assertEqual(summary['final_energy'], energy)
                self.assertEqual(summary['final_material'], mass)
            for name in ('initial.json', 'steps.jsonl', 'final.json', 'summary.json'):
                self.assertEqual((root/'a'/name).read_bytes(), (root/'b'/name).read_bytes())
            for control in ('off', 'no_exchange'):
                self.assertEqual((root/control/'initial.json').read_bytes(), (root/'a/initial.json').read_bytes())
                actual = json.loads((root/control/'final.json').read_text())
                reference = json.loads((root/'a/final.json').read_text())
                for key in ('drive_rng', 'direction_rng'):
                    self.assertEqual(actual[key], reference[key])

    def test_preflight_and_empty_zero_horizon(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'run'
            for config in ({'initial_raw': -1}, {'threshold': 5}, {'max_site_records': 1}):
                with self.assertRaises(ValueError):
                    run(root, 90602, **config)
                self.assertFalse(root.exists())
            summary = run(root, 90602, steps=0, occupancy=0)
            self.assertEqual(audit(root)['summary'], summary)
            self.assertEqual(summary['formations'], 0)
            self.assertEqual(summary['dissolutions'], 0)
            self.assertEqual(summary['units'], 0)
            self.assertEqual(summary['final_material'], 256)
            self.assertEqual((root/'steps.jsonl').read_bytes(), b'')
            with self.assertRaises(FileExistsError):
                run(root, 90602, steps=0)


if __name__ == '__main__':
    unittest.main()
