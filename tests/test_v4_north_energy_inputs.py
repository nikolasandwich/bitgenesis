import unittest
from unittest.mock import patch
from scripts import north_energy_inputs as io

class EnergyInputTest(unittest.TestCase):
    def inventory(self):return dict.fromkeys([str(p) for _,p in io.source_cases()]+[f'prior-{i}' for i in range(149)],'hash')
    def test_complete_and_failed_inventory(self):
        with patch.object(io,'read',return_value={'input_sha256':self.inventory()}):
            errors={};self.assertEqual(len(io.input_paths(errors)),401);self.assertFalse(errors)
        with patch.object(io,'read',side_effect=[OSError('missing'),{'input_sha256':self.inventory()}]):
            errors={};self.assertEqual(len(io.input_paths(errors)),401);self.assertEqual(len(errors),1)
        with patch.object(io,'read',side_effect=OSError('missing')):
            errors={};self.assertEqual(len(io.input_paths(errors)),252);self.assertEqual(len(errors),2)
