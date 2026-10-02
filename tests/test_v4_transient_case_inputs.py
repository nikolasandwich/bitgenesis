import unittest
from scripts.transient_case_inputs import validate_cases

class CaseInputTests(unittest.TestCase):
    def rows(self):
        return [dict(exchange=e,directory=f'data/v4-study-016/branches/history-false-seed-112000-mutation-0-exchange-{str(e).lower()}',source='data/v4-study-015/baselines/seed-112000-drive-250-mutation-0') for e in (True,False)]
    def test_exact_pair_and_types(self):
        rows=self.rows();validate_cases(rows)
        for bad in (rows[:1],rows+[rows[0]],rows[::-1]):
            with self.assertRaises(AssertionError):validate_cases(bad)
        rows=self.rows();rows[0]['exchange']=1
        with self.assertRaises(AssertionError):validate_cases(rows)
    def test_different_branch_rejected(self):
        rows=self.rows();rows[0]['directory']=rows[0]['directory'].replace('112000','112001')
        with self.assertRaises(AssertionError):validate_cases(rows)
