import unittest
from scripts.check_v4_information_loss import check


class InformationLossTests(unittest.TestCase):
    def test_distinct_patterns_have_identical_post_damage_future(self):
        result=check()
        self.assertNotEqual(result['first_labels'],result['second_labels'])
        self.assertEqual(result['identical_continued_transitions'],128)
        self.assertTrue(result['observer_records_differ'])
