import json
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v2.runner import run
from bitgenesis.v2.world import Config


class V2RunnerTests(unittest.TestCase):
    def test_records_replay_and_attempt_ledgers(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=Config(width=5,height=5,founders=10)
            for name in ('a','b'):
                run(root/name,config,81101,30)
            for name in ('initial.json','steps.jsonl','events.jsonl','final.json','summary.json'):
                self.assertEqual((root/'a'/name).read_bytes(),(root/'b'/name).read_bytes())
            initial=json.loads((root/'a/initial.json').read_text())
            final=json.loads((root/'a/final.json').read_text())
            summary=json.loads((root/'a/summary.json').read_text())
            declared=sum(initial['food'])+config.founders*config.initial_energy
            total=sum(initial['food'])+sum(o['energy'] for o in initial['lineage'])
            self.assertEqual(total,declared-initial['initialization_spent'])
            for attempt in final['attempts']:
                self.assertEqual(attempt['allocation'],attempt['construction_cost']+attempt['failure_loss']+attempt['living_energy'])
            self.assertEqual(len(final['attempts']),summary['attempts'])
            self.assertEqual(sum(not a['valid'] for a in final['attempts']),summary['failed_attempts'])
            for line in (root/'a/steps.jsonl').read_text().splitlines():
                tick=json.loads(line)
                self.assertEqual(tick['energy_before'],total)
                total+=tick['resource_added']-tick['spent']
                self.assertEqual(tick['energy_after'],total)
            self.assertEqual(total,summary['total_energy'])
            self.assertEqual(total,sum(final['food'])+sum(o['energy'] for o in final['lineage'] if o['death_tick'] is None))

    def test_direct_mode_and_failed_founder_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            failed=run(root/'failed',Config(width=3,height=3,founders=2,initial_energy=1),81102,2)
            self.assertEqual((failed['founder_attempts'],failed['successful_founders'],failed['failed_attempts']),(2,0,2))
            self.assertEqual(failed['failure_loss'],2)
            direct=run(root/'direct',Config(width=3,height=3,founders=2),81102,2,encoding='direct')
            self.assertEqual(direct['successful_founders'],2)
            with self.assertRaises(FileExistsError):
                run(root/'direct',Config(),81102,2)
