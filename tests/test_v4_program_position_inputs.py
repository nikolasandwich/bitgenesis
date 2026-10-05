import unittest
from unittest.mock import patch
from scripts import program_position_inputs as inputs

class InputsTests(unittest.TestCase):
    def test_encoding_selects_correct_saved_source(self):
        self.assertIn('study-023',str(inputs.source_path(120000,'north')))
        self.assertIn('study-019',str(inputs.source_path(120000,'east')))
        with self.assertRaises(ValueError):inputs.source_path(120020,'east')
        with self.assertRaises(ValueError):inputs.source_path(120000,'unknown')
    def test_missing_manifest_retained(self):
        errors={}
        with patch.object(inputs,'read',side_effect=OSError('missing')):p=inputs.input_paths(errors)
        self.assertTrue(errors)
        self.assertIn('scripts/run_v4_program_position.py',p)
