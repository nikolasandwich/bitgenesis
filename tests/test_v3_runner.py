from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v3.runner import run
from bitgenesis.v3.world import Config


class V3RunnerTests(unittest.TestCase):
    def test_persisted_replay_and_substrate_balance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=Config(width=5,height=5,founders=10,initial_b=4)
            for name in ('a','b'):
                run(root/name,config,85100,50)
            for name in ('initial.json','steps.jsonl','events.jsonl','final.json','summary.json'):
                self.assertEqual((root/'a'/name).read_bytes(),(root/'b'/name).read_bytes())
            def read(name):
                return json.loads((root/'a'/name).read_text())
            meta,initial,final,summary=map(read,('metadata.json','initial.json','final.json','summary.json'))
            for name,digest in meta['output_sha256'].items():
                self.assertEqual(sha256((root/'a'/name).read_bytes()).hexdigest(),digest)
            flows=summary['resource_flows']
            self.assertEqual(sum(final['food']),sum(initial['food'])+flows['external_a']-flows['consumed_a'])
            self.assertEqual(sum(final['substrate_b']),sum(initial['substrate_b'])+flows['released_b']-flows['consumed_b'])
            self.assertEqual(flows['consumed_a']+flows['consumed_b'],
                             flows['feeding_energy']+flows['released_b']+flows['feeding_dissipation'])
            self.assertEqual(summary['total_energy'],sum(final['food'])+sum(final['substrate_b'])+
                sum(o['energy'] for o in final['lineage'] if o['death_tick'] is None))
            self.assertIn('../v2/development.py',meta['source_sha256'])

    def test_failed_founders_and_record_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=Config(width=3,height=3,founders=2,initial_energy=1)
            summary=run(root/'failed',config,85101,3)
            self.assertEqual(summary['failed_attempts'],2)
            self.assertEqual(summary['population'],0)
            with self.assertRaises(ValueError):
                run(root/'budget',config,85101,3,max_actor_records=26)
            self.assertFalse((root/'budget').exists())
            with self.assertRaises(FileExistsError):
                run(root/'failed',config,85101,3)


if __name__=='__main__':
    unittest.main()
