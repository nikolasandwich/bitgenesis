import unittest
from unittest.mock import patch
from scripts import feed_timing_inputs as inputs

class TimingInputsTest(unittest.TestCase):
    def test_inventory_and_fallback(self):
        old={str(p):'hash' for p in inputs.source_cases()}
        old.update({f'old-{i}':'hash' for i in range(427)})
        with patch.object(inputs,'read',return_value={'input_sha256':old}):
            self.assertEqual(len(inputs.input_paths()),491)
        with patch.object(inputs,'read',side_effect=[OSError('missing'),{'input_sha256':old}]):
            errors={};self.assertEqual(len(inputs.input_paths(errors)),491);self.assertEqual(len(errors),1)
        with patch.object(inputs,'read',side_effect=OSError('missing')):
            errors={};self.assertEqual(len(inputs.input_paths(errors)),64);self.assertEqual(len(errors),2)
