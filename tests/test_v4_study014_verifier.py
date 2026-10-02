import unittest
from scripts.verify_v4_study014_summary import aggregate_saved

class ReplicationVerifierTests(unittest.TestCase):
    def test_missing_cohort_rejected(self):
        with self.assertRaises(ValueError):aggregate_saved([])

    def test_empty_and_wrong_binding_inventory_rejected(self):
        import tempfile
        from pathlib import Path
        from scripts.verify_v4_study014_summary import verify_files
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'required').write_text('payload')
            with self.assertRaises(AssertionError):verify_files(p,{}, {'required'})
            with self.assertRaises(ValueError):verify_files(p,{'required':'wrong'},{'required'})
