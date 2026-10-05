import unittest
from unittest.mock import patch
from scripts import copy_slots_inputs as inputs

class CopySlotsInputsTest(unittest.TestCase):
    def test_inventory_fallback(self):
        old={f'old-{i}':'hash' for i in range(401)}
        with patch.object(inputs,'read',return_value={'input_sha256':old}):
            self.assertEqual(len(inputs.input_paths()),413)
        with patch.object(inputs,'read',side_effect=[OSError('missing'),{'input_sha256':old}]):
            errors={};self.assertEqual(len(inputs.input_paths(errors)),413);self.assertEqual(len(errors),1)
        with patch.object(inputs,'read',side_effect=OSError('missing')):
            errors={};self.assertEqual(len(inputs.input_paths(errors)),12);self.assertEqual(len(errors),2)
