import json
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v1.audit import audit
from bitgenesis.v1.runner import run
from bitgenesis.v1.world import Config


class AuditTests(unittest.TestCase):
    def test_valid_edge_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            for i, config in enumerate((Config(width=3, height=3, founders=0),
                    Config(width=3, height=3, founders=2, initial_energy=1),
                    Config(width=5, height=5, founders=8, initial_energy=80),
                    Config(width=3, height=3, founders=9, movement_cost=30))):
                path = Path(directory) / str(i)
                run(path, config, 70200 + i, 20)
                self.assertEqual(audit(path)['steps'], 20)

    def test_semantic_corruption_even_with_rehashed_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'run'
            run(root, Config(width=5, height=5, founders=8, initial_energy=80), 70210, 20)
            audit(root)
            mutations = [
                ('steps.jsonl', lambda v: v[0]['actors'][0].__setitem__('energy_after', 999)),
                ('steps.jsonl', lambda v: v[0].__setitem__('actors', v[0]['actors'][:-1])),
                ('events.jsonl', lambda v: next(e for e in v if e['event'] == 'birth' and e['parent'] is not None).__setitem__('founder', 999)),
                ('final.json', lambda v: v['lineage'][0].__setitem__('offspring', 999)),
                ('summary.json', lambda v: v.__setitem__('births', 999)),
            ]
            for name, mutate in mutations:
                original = (root / name).read_bytes()
                metadata = (root / 'metadata.json').read_bytes()
                try:
                    value = [json.loads(line) for line in original.splitlines()] if name.endswith('jsonl') else json.loads(original)
                    mutate(value)
                    text = ''.join(json.dumps(row) + '\n' for row in value) if name.endswith('jsonl') else json.dumps(value)
                    (root / name).write_text(text, encoding='utf-8')
                    meta = json.loads(metadata)
                    meta['output_sha256'][name] = sha256((root / name).read_bytes()).hexdigest()
                    (root / 'metadata.json').write_text(json.dumps(meta), encoding='utf-8')
                    with self.assertRaises(ValueError, msg=name):
                        audit(root)
                finally:
                    (root / name).write_bytes(original)
                    (root / 'metadata.json').write_bytes(metadata)
