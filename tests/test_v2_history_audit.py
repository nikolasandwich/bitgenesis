import json
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bitgenesis.v2.audit import audit
from bitgenesis.v2.development import DevelopmentGenome
from bitgenesis.v2.runner import run
from bitgenesis.v2.world import Config


class V2HistoryAuditTests(unittest.TestCase):
    def test_birth_failure_death_and_direct_histories(self):
        fixture=DevelopmentGenome((6,100,0,0,0,0,0,0,1,1))
        with tempfile.TemporaryDirectory() as directory:
            for index,(energy,threshold) in enumerate(((200,160),(80,40),(35,80),(37,80))):
                path=Path(directory)/str(index)
                with patch('bitgenesis.v2.world.DevelopmentGenome.random',return_value=fixture):
                    run(path,Config(width=3,height=3,founders=1,initial_energy=energy,
                        birth_threshold=threshold,feeding_limit=0,renewal_per_thousand=0,
                        mutation_per_thousand=0),81300+index,5)
                self.assertEqual(audit(path)['summary']['steps'],5)
            path=Path(directory)/'direct'
            run(path,Config(width=5,height=5,founders=10,initial_energy=400,birth_threshold=160),81304,30,encoding='direct')
            self.assertGreater(audit(path)['summary']['births'],0)

    def test_semantic_corruption_beyond_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'run'
            run(root,Config(width=5,height=5,founders=10),81305,5)
            audit(root)
            for name in ('steps.jsonl','summary.json','events.jsonl'):
                original=(root/name).read_bytes()
                original_meta=(root/'metadata.json').read_bytes()
                try:
                    if name=='summary.json':
                        value=json.loads(original)
                        value['failed_attempts']+=1
                        text=json.dumps(value)
                    else:
                        values=[json.loads(line) for line in original.splitlines()]
                        if name=='steps.jsonl':
                            values[0]['actors'][0]['energy_after']+=1
                        else:
                            values.pop(0)
                        text=''.join(json.dumps(v)+'\n' for v in values)
                    (root/name).write_text(text,encoding='utf-8')
                    meta=json.loads(original_meta)
                    meta['output_sha256'][name]=sha256((root/name).read_bytes()).hexdigest()
                    (root/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
                    with self.assertRaises(ValueError):
                        audit(root)
                finally:
                    (root/name).write_bytes(original)
                    (root/'metadata.json').write_bytes(original_meta)
