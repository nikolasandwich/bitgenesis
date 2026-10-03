import copy
import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from scripts import run_v4_copy_ablation as r


class AblationTapesTests(unittest.TestCase):
    def test_complete_independent_streams(self):
        rows = r.tapes(120000)
        streams = [random.Random(int.from_bytes(hashlib.sha256(
            f'v4-copy-ablation-1:120000:{name}'.encode('ascii')).digest(), 'big'))
            for name in ('directions', 'feeds')]
        self.assertEqual(len(rows), 32)
        for row in rows:
            self.assertEqual(row['directions'], [streams[0].randrange(4) for _ in range(256)])
            self.assertEqual(row['feed_sites'], streams[1].sample(range(256), 4))
        self.assertNotEqual(rows, r.tapes(120001))


class AblationPhysicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {(mode, exchange): r.run_case(120000, mode, exchange)
                     for mode in r.MODES for exchange in (False, True)}

    def test_paired_inputs_and_native_accounting(self):
        tapes = r.tapes(120000)
        for (mode, exchange), case in self.cases.items():
            summary = case['summary']
            self.assertEqual([i for i, n in enumerate(case['initial']['raw']) if n], [101, 102, 117, 118])
            self.assertEqual(sum(case['initial']['raw']), 4)
            self.assertEqual(summary['initial_mass'], 7)
            self.assertEqual(summary['final_mass'], 7)
            self.assertEqual(summary['living'], 3 + summary['births'] - summary['deaths'])
            self.assertEqual(summary['initial_energy'] + summary['imported'] - summary['spent'], summary['final_energy'])
            self.assertEqual(summary['proposed'], 1024)
            self.assertEqual(summary['imported'] + summary['rejected_import'], 1024)
            self.assertEqual(len(case['rows']), 32)
            for tick, row in enumerate(case['rows'], 1):
                physical = row['physical']
                other = self.cases[mode, not exchange]['rows'][tick - 1]['physical']
                inputs = physical['driven']['inputs']
                self.assertEqual(sum(v['proposed'] for v in inputs), 32)
                self.assertEqual(physical['directions'], other['directions'])
                self.assertEqual([v['proposed'] for v in inputs], [v['proposed'] for v in other['driven']['inputs']])
                self.assertEqual(physical['energy_before'] + physical['imported'] - physical['spent'], physical['energy_after'])
                self.assertEqual(physical['material_before'], physical['material_after'])
                if mode != 'random-feed':
                    self.assertEqual(physical['directions'], tapes[tick - 1]['directions'])
                else:
                    expected = [1 if site % 16 == 6 else 0 for site in range(256)]
                    if tick == 1:
                        expected[85] = expected[86] = 2
                    if tick == 2:
                        expected[101] = expected[102] = 2
                    self.assertEqual(physical['directions'], expected)
                sites = [v['site'] for v in inputs if v['proposed']]
                expected_sites = tapes[tick - 1]['feed_sites'] if mode != 'random-direction' else [85, 86, 117, 118]
                self.assertEqual(sorted(sites), sorted(expected_sites))
                for unit in physical['units']:
                    if unit is not None:
                        self.assertEqual(unit['program'], [unit['material']] * 4)
            self.assertEqual(set(case['copy_parents'][0]['series']), {'descendant_material', 'descendant_genetic', 'unrelated_material', 'unrelated_genetic'})

    def test_strict_case_identity(self):
        for args in ((120020, 'random-feed', False), (True, 'random-feed', False),
                     (120000, 'tuned', False), (120000, 'random-feed', 0)):
            with self.assertRaises(ValueError):
                r.run_case(*args)


def summaries():
    rows = []
    for seed, mode, exchange in r.GRID:
        # Five each: neither, on-only, off-only, both; five-step transient in failures.
        success = (seed % 4 in ((1, 3) if exchange else (2, 3)))
        counts = [2] * (10 if success else 5) + [1] * (22 if success else 27)
        rows.append(dict(seed=seed, mode=mode, exchange=exchange, steps=32,
                         births=4, deaths=1, living=6, initial_energy=192,
                         final_energy=200, imported=100, rejected_import=924,
                         spent=92, proposed=1024, initial_mass=7, final_mass=7,
                         genetic_counts=counts, episodes=[[1, 10 if success else 5]],
                         longest=10 if success else 5, persistent10=success, ever=True))
    return rows


class AblationAggregateTests(unittest.TestCase):
    def test_source_equal_mixed_pairs(self):
        result = r.summarize(summaries())
        self.assertEqual(len(result['cells']), 6)
        self.assertEqual(len(result['pairs']), 60)
        for cell in result['cells']:
            self.assertEqual(cell['n'], 20)
            self.assertEqual(cell['successes'], 10)
            self.assertEqual(cell['success_fraction'], '1/2')
            self.assertEqual(cell['ever_fraction'], '1')
            self.assertEqual(cell['mean_longest'], '15/2')
            self.assertEqual(cell['mean_imported'], '100')
        for group in result['groups']:
            self.assertEqual([group[k] for k in ('on_only', 'off_only', 'both', 'neither')], [5]*4)
            self.assertEqual(group['mean_difference'], '0')
        self.assertEqual([p['difference'] for p in result['pairs'][:12:3]], [0, 1, -1, 0])

    def test_missing_duplicate_and_wrong_types_rejected(self):
        original = summaries()
        malformed = [original[:-1], original[:-1] + [original[0]]]
        for field, value in [('seed', True), ('exchange', 0), ('steps', 32.0), ('births', True),
                             ('persistent10', 1), ('ever', 1), ('longest', 9),
                             ('genetic_counts', [True]*32), ('episodes', [[True, 5]]),
                             ('imported', '100')]:
            rows = copy.deepcopy(original)
            rows[0][field] = value
            malformed.append(rows)
        for rows in malformed:
            with self.assertRaises(ValueError):
                r.summarize(rows)


class AblationRunnerTests(unittest.TestCase):
    def setup_run(self, root):
        return (patch.object(r, 'OUTPUT', root),
                patch.object(r.subprocess, 'check_output', side_effect=['', 'commit']),
                patch.object(r, 'bindings', return_value={str(i): 'hash' for i in range(57)}))

    def test_full_negative_retention_and_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'run'
            rows = summaries()
            with self.setup_run(root)[0], self.setup_run(root)[1], self.setup_run(root)[2], patch.object(r, 'run_case', side_effect=[dict(summary=s) for s in rows]), patch('builtins.print'):
                r.main()
            meta = json.loads((root/'metadata.json').read_text())
            self.assertEqual(meta['status'], 'complete')
            self.assertEqual(meta['completed_cases'], 120)
            self.assertEqual(meta['new_simulation_steps'], 3840)
            self.assertEqual(meta['new_independent_initial_worlds'], 0)
            self.assertEqual(meta['new_environment_sources'], 20)
            self.assertTrue(meta['python_version'])
            self.assertEqual(len(list((root/'cases').glob('*.json'))), 120)
            self.assertEqual(len(meta['output_sha256']), 122)
            self.assertEqual(json.loads((root/'results.json').read_text()), rows)

    def test_failure_preserves_completed_case_and_exclusive_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'run'
            with self.setup_run(root)[0], self.setup_run(root)[1], self.setup_run(root)[2], patch.object(r, 'run_case', side_effect=[dict(summary=summaries()[0]), RuntimeError('case failed')]), patch('builtins.print'):
                with self.assertRaisesRegex(RuntimeError, 'case failed'):
                    r.main()
            meta = json.loads((root/'metadata.json').read_text())
            self.assertEqual(meta['status'], 'failed')
            self.assertEqual(meta['completed_cases'], 1)
            self.assertEqual(meta['new_simulation_steps'], 32)
            self.assertEqual(len(list((root/'cases').glob('*.json'))), 1)
            self.assertFalse((root/'summary.json').exists())
            before = (root/'metadata.json').read_bytes()
            with patch.object(r, 'OUTPUT', root), patch.object(r.subprocess, 'check_output', return_value=''):
                with self.assertRaises(FileExistsError):
                    r.main()
            self.assertEqual(before, (root/'metadata.json').read_bytes())

    def test_clean_launch_and_time_budget(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'run'
            with patch.object(r, 'OUTPUT', root), patch.object(r.subprocess, 'check_output', return_value='dirty'):
                with self.assertRaisesRegex(ValueError, 'clean'):
                    r.main()
            self.assertFalse(root.exists())
            with self.setup_run(root)[0], self.setup_run(root)[1], self.setup_run(root)[2], patch.object(r, 'SECONDS', 0):
                with self.assertRaisesRegex(ValueError, 'budget'):
                    r.main()
            self.assertEqual(json.loads((root/'metadata.json').read_text())['completed_cases'], 0)

    def test_input_change_retains_completed_case(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'run'
            bound = {str(i): 'hash' for i in range(57)}
            changed = dict(bound, changed='hash')
            with self.setup_run(root)[0], self.setup_run(root)[1], patch.object(r, 'bindings', side_effect=[bound, bound, changed, changed]), patch.object(r, 'run_case', return_value=dict(summary=summaries()[0])):
                with self.assertRaisesRegex(ValueError, 'bound inputs changed'):
                    r.main()
            meta = json.loads((root/'metadata.json').read_text())
            self.assertEqual(meta['status'], 'failed')
            self.assertEqual(meta['completed_cases'], 1)
            self.assertEqual(meta['input_sha256_after'], changed)
            self.assertFalse((root/'summary.json').exists())
            self.assertEqual(len(meta['output_sha256']), 2)

    def test_initial_binding_failure_and_storage_budget(self):
        for problem in ('bindings', 'storage'):
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)/'run'
                binding_patch = patch.object(r, 'bindings', side_effect=ValueError('invalid original proof')) if problem == 'bindings' else self.setup_run(root)[2]
                with self.setup_run(root)[0], self.setup_run(root)[1], binding_patch, patch.object(r, 'STORAGE', 1 if problem == 'storage' else 268435456):
                    with self.assertRaises(ValueError):
                        r.main()
                meta = json.loads((root/'metadata.json').read_text())
                self.assertEqual(meta['status'], 'failed')
                self.assertEqual(meta['completed_cases'], 0)
                self.assertEqual(json.loads((root/'results.json').read_text()), [])
                self.assertFalse((root/'summary.json').exists())
