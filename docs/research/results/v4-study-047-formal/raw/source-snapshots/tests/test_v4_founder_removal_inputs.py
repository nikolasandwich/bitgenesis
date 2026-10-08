import unittest
from unittest.mock import patch
from scripts import founder_removal_inputs as inputs


class FounderRemovalInputsTests(unittest.TestCase):
    def test_inventory_read_error_is_retained(self):
        with patch.object(inputs, 'read', side_effect=OSError('missing')):
            errors = {}
            paths = inputs.input_paths(errors)
            self.assertEqual(len(errors), 2)
            self.assertIn('experiments/v4/study-036.md', paths)
            self.assertIn('data/v4-study-034/records.json', paths)

    def test_bound_manifest_rejects_changed_source(self):
        with patch.object(inputs, 'digest', return_value='actual'):
            with self.assertRaises(AssertionError):
                inputs.validate_manifest({'source.json': 'expected'})
            self.assertEqual(inputs.validate_manifest({'source.json': 'actual'}), {'source.json': 'actual'})
