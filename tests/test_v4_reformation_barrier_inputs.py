import unittest
from unittest.mock import patch
from scripts import reformation_barrier_inputs as inputs

class ReformationInputsTests(unittest.TestCase):
    def test_missing_inventories_record_both_errors(self):
        errors={}
        with patch.object(inputs,'read',side_effect=OSError('missing')):
            paths=inputs.input_paths(errors)
        self.assertEqual(len(errors),2)
        self.assertIn('data/v4-study-036/cases/branch-057.json',paths)
        self.assertIn('experiments/v4/study-037.md',paths)
