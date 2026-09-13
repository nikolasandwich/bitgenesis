import unittest

from scripts.audit_v0_neutral_labels import compare_rows


class NeutralLabelTests(unittest.TestCase):
    def pair(self):
        return ({"tick":"0","population":"80","a":"72","b":"8","b_fraction":"0.1"},
                {"tick":"0","population":"80","a":"8","b":"72","b_fraction":"0.9"})

    def test_label_only_difference_is_allowed(self):
        a,b = self.pair()
        self.assertEqual(compare_rows([a],[b]),1)

    def test_physical_difference_and_truncation_are_rejected(self):
        a,b = self.pair()
        b["population"] = "79"
        with self.assertRaisesRegex(ValueError,"physical"):
            compare_rows([a],[b])
        with self.assertRaisesRegex(ValueError,"lengths"):
            compare_rows([a],[])

    def test_reversed_subset_is_rejected(self):
        a,b = self.pair()
        with self.assertRaisesRegex(ValueError,"Nested"):
            compare_rows([b],[a])


if __name__ == "__main__":
    unittest.main()
