import unittest
from unittest.mock import patch
from scripts import energy_continuation_inputs as inputs

class InputsTest(unittest.TestCase):
    def test_full_inventory_and_archive_fallback(self):
        prior={f'old-{i}':'hash' for i in range(401)}
        with patch.object(inputs,'source_cases',return_value=[]), patch.object(inputs,'read',return_value={'input_sha256':prior}):
            self.assertEqual(len(inputs.input_paths()),413)
        with patch.object(inputs,'source_cases',return_value=[]), patch.object(inputs,'read',side_effect=[OSError('missing'),{'input_sha256':prior}]):
            errors={};self.assertEqual(len(inputs.input_paths(errors)),413);self.assertEqual(len(errors),1)
        with patch.object(inputs,'source_cases',return_value=[]), patch.object(inputs,'read',side_effect=OSError('missing')):
            errors={};self.assertEqual(len(inputs.input_paths(errors)),12);self.assertEqual(len(errors),2)
