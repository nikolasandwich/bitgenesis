import unittest
from scripts.analyze_v0_cohort_energy import budgets


class CohortEnergyTests(unittest.TestCase):
    def test_internal_transfers_cancel_and_final_newborn_energy_is_retained(self):
        rows=[dict(id=0,energy_before_action=10,energy_after_action=4,eaten=0,
                   basal_paid=2,movement_paid=0,birth_paid=0,child_id=1,child_energy=4),
              dict(id=1,energy_before_action=4,energy_after_action=1,eaten=0,
                   basal_paid=1,movement_paid=0,birth_paid=0,child_id=2,child_energy=2)]
        result=budgets(rows,{0:10})
        self.assertEqual(result['descendants']['received_from_founders'],4)
        self.assertEqual(result['descendants']['child_energy'],2)
        self.assertEqual(result['descendants']['ending_energy'],3)
        self.assertEqual(result['founders']['ending_energy'],4)

    def test_unbalanced_cohort_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'balance'):
            budgets([dict(id=0,energy_before_action=10,energy_after_action=9,eaten=0,
                          basal_paid=0,movement_paid=0,birth_paid=0,child_id=None,child_energy=0)],{0:10})
