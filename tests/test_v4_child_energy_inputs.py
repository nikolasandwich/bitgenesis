import unittest
from unittest.mock import patch
from scripts import child_energy_inputs as inputs

class ChildEnergyInputsTest(unittest.TestCase):
    def test_complete_inventory_and_fallback(self):
        old={f'old-{i}':'hash' for i in range(413)}
        with patch.object(inputs,'read',return_value={'input_sha256':old}):
            self.assertEqual(len(inputs.input_paths()),479)
        with patch.object(inputs,'read',side_effect=[OSError('missing'),{'input_sha256':old}]):
            errors={};self.assertEqual(len(inputs.input_paths(errors)),479);self.assertEqual(len(errors),1)
        with patch.object(inputs,'read',side_effect=OSError('missing')):
            errors={};self.assertEqual(len(inputs.input_paths(errors)),66);self.assertEqual(len(errors),2)
        self.assertEqual(len(list(inputs.source_cases())),52)
