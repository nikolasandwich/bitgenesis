import unittest
from unittest.mock import patch
from scripts import north_opportunity_inputs as io

class NorthInputTests(unittest.TestCase):
    def inventory(self):
        old=[str(p) for _,p in io.source_cases() if 'v4-study-025' not in str(p)]
        return dict.fromkeys(old+[f'prior-{i}' for i in range(135)],'hash')
    def test_order_and_complete_inventory(self):
        sources=list(io.source_cases());self.assertEqual(len(sources),240)
        self.assertEqual(len({str(p) for _,p in sources}),240)
        self.assertEqual([g for g,_ in sources[:120]],['homogeneous']*120)
        with patch.object(io,'read',return_value={'input_sha256':self.inventory()}):
            errors={};paths=io.input_paths(errors)
        self.assertEqual(len(paths),389);self.assertEqual(errors,{})
        self.assertTrue(all(str(p) in paths for _,p in sources))
    def test_archive_fallback_and_unknown_inventory(self):
        with patch.object(io,'read',side_effect=[OSError('root missing'),{'input_sha256':self.inventory()}]):
            errors={};self.assertEqual(len(io.input_paths(errors)),389);self.assertEqual(len(errors),1)
        with patch.object(io,'read',side_effect=OSError('unreadable')):
            errors={};paths=io.input_paths(errors)
        self.assertEqual(len(paths),254);self.assertEqual(len(errors),2)
        self.assertTrue(all(str(p) in paths for _,p in io.source_cases()))
