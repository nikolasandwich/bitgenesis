import unittest
from scripts.summarize_v0_food_geometry import INITIAL
from scripts.summarize_v0_joint_zero_charge import verify_rows


class JointZeroChargeVerifierTests(unittest.TestCase):
    def test_birth_cost_changes_exact_dissipation_without_changing_initial_state(self):
        free={**INITIAL,'tick':1,'births':1,'population':81,'organism_energy':1840,
              'dissipated_energy':80,'max_generation':1}
        paid={**free,'organism_energy':1836,'dissipated_energy':84}
        verify_rows([INITIAL,free],0,steps=1)
        verify_rows([INITIAL,paid],4,steps=1)
        for row,cost in ((free,4),(paid,0)):
            with self.assertRaisesRegex(ValueError,'transition'):
                verify_rows([INITIAL,row],cost,steps=1)

    def test_invalid_cost_and_fixed_trait_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'birth charge'):
            verify_rows([INITIAL],True,steps=0)
        with self.assertRaisesRegex(ValueError,'trait'):
            verify_rows([{**INITIAL,'mean_genome':251}],0,steps=0)
