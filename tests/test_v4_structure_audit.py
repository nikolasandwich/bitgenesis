import copy
import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.hereditary_runner import run
from bitgenesis.v4.structure_trace import trace
from bitgenesis.v4.structure_audit import audit


class StructureAuditTests(unittest.TestCase):
    def test_complete_observation_and_corrupt_measurement_rejection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)/'run'
            output = Path(temporary)/'observation.json'
            run(root, 102003, 8, width=5, height=5)
            original = trace(root)
            def write(value):
                output.write_text(json.dumps(value), encoding='utf-8')
            write(original)
            checked = audit(root, output)
            self.assertEqual((checked['partitions'], checked['transitions']), (42, 37))
            bad = copy.deepcopy(original)
            bad['observations'][0]['final']['metrics']['contact']['component_count'] += 1
            write(bad)
            with self.assertRaisesRegex(ValueError, 'partition/metric/continuity'):
                audit(root, output)
            bad = copy.deepcopy(original)
            identities = bad['observations'][0]['interaction_site_ids']
            site = next(i for i, identity in enumerate(identities) if identity is not None)
            identities[site] += 1000
            write(bad)
            with self.assertRaisesRegex(ValueError, 'identity mapping'):
                audit(root, output)

    def test_empty_zero_horizon(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)/'run'
            output = Path(temporary)/'observation.json'
            run(root, 102004, 0, width=3, height=3, occupancy=0)
            output.write_text(json.dumps(trace(root)), encoding='utf-8')
            checked = audit(root, output)
            self.assertEqual((checked['partitions'], checked['transitions']), (2, 0))
