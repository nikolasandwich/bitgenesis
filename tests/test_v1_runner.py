import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bitgenesis.v1.runner import run
from bitgenesis.v1.world import Config


class RunnerTests(unittest.TestCase):
    def test_persisted_replay_and_independent_record_accounting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = Config(width=5, height=5, founders=6, initial_energy=80)
            for name in ('a', 'b'):
                run(root / name, config, 70100, 30)
            for name in ('initial.json', 'steps.jsonl', 'events.jsonl', 'final.json', 'summary.json'):
                self.assertEqual((root / 'a' / name).read_bytes(), (root / 'b' / name).read_bytes())
            initial = json.loads((root / 'a/initial.json').read_text())
            energy = sum(initial['food']) + sum(o['energy'] for o in initial['lineage'])
            records = [json.loads(line) for line in (root / 'a/steps.jsonl').read_text().splitlines()]
            for tick, row in enumerate(records, 1):
                self.assertEqual(row['tick'], tick)
                self.assertEqual(row['energy_before'], energy)
                spent = 0
                for actor in row['actors']:
                    paid = sum(actor[key] for key in ('basal', 'decision', 'movement', 'birth_cost'))
                    self.assertEqual(actor['energy_after'], actor['energy_before'] + actor['intake']
                                     - paid - actor['child_energy'])
                    spent += paid
                self.assertEqual(row['spent'], spent)
                energy += row['resource_added'] - spent
                self.assertEqual(row['energy_after'], energy)
            final = json.loads((root / 'a/final.json').read_text())
            living = [o for o in final['lineage'] if o['death_tick'] is None]
            self.assertEqual(energy, sum(final['food']) + sum(o['energy'] for o in living))
            self.assertEqual(len({(o['x'], o['y']) for o in living}), len(living))
            events = [json.loads(line) for line in (root / 'a/events.jsonl').read_text().splitlines()]
            births = [e for e in events if e['event'] == 'birth']
            self.assertEqual([e['id'] for e in births], list(range(len(final['lineage']))))
            self.assertEqual(len(events) - len(births), len(final['lineage']) - len(living))
            self.assertEqual(json.loads((root / 'a/metadata.json').read_text())['status'], 'complete')

    def test_budget_and_overwrite_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'run'
            with self.assertRaises(ValueError):
                run(output, Config(), 1, 100, max_actor_records=1)
            self.assertFalse(output.exists())
            run(output, Config(founders=0), 1, 0)
            original = (output / 'metadata.json').read_bytes()
            with self.assertRaises(FileExistsError):
                run(output, Config(founders=0), 1, 0)
            self.assertEqual((output / 'metadata.json').read_bytes(), original)

    def test_failed_run_is_not_marked_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'run'
            with patch('bitgenesis.v1.runner.World.step', side_effect=RuntimeError('injected')):
                with self.assertRaises(RuntimeError):
                    run(output, Config(), 1, 1)
            metadata = json.loads((output / 'metadata.json').read_text())
            self.assertEqual(metadata['status'], 'failed')
            self.assertEqual(metadata['completed_steps'], 0)
            self.assertFalse((output / 'summary.json').exists())
