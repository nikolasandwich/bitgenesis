from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.hereditary_runner import run
from bitgenesis.v4.structure_trace import trace


class StructureTraceTests(unittest.TestCase):
    def test_audited_phases_and_independent_overlaps_preserve_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'run'
            run(root, 102001, 20, width=8, height=8)
            original = {p.name: sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
            result = trace(root)
            self.assertEqual(original, {p.name: sha256(p.read_bytes()).hexdigest() for p in root.iterdir()})
            self.assertEqual(result['input_sha256'], original)
            previous_ids = [None] * 64
            initial = json.loads((root / 'initial.json').read_text(encoding='utf-8'))
            counter = 0
            for site, unit in enumerate(initial['units']):
                if unit is not None:
                    previous_ids[site] = counter
                    counter += 1
            previous = result['initial']['components']
            for observation, line in zip(result['observations'], (root / 'steps.jsonl').read_text().splitlines()):
                row = json.loads(line)
                self.assertEqual(observation['interaction_site_ids'], previous_ids)
                for site in row['material']['dissolved']:
                    previous_ids[site] = None
                for proposal in row['material']['proposals']:
                    if proposal['reason'] == 'formed':
                        previous_ids[proposal['target']] = counter
                        counter += 1
                self.assertEqual(observation['final_site_ids'], previous_ids)
                for name, groups in observation['final']['components'].items():
                    expected = [(a, b, len(set(old) & set(new)))
                                for a, old in enumerate(previous[name]) for b, new in enumerate(groups)
                                if set(old) & set(new)]
                    actual = [(e['previous'], e['current'], e['shared'])
                              for e in observation['final_continuity'][name]['overlaps']]
                    self.assertEqual(actual, expected)
                previous = observation['final']['components']
            self.assertIsNone(result['observations'][0]['interaction_continuity'])
            self.assertGreater(result['lineage_summary']['births'], 0)

    def test_zero_horizon(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'run'
            run(root, 102002, 0, width=3, height=3)
            self.assertEqual(trace(root)['observations'], [])
