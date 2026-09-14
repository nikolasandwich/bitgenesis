import unittest
from scripts.summarize_v0_food_geometry import INITIAL
from scripts.summarize_v0_movement_charge import verify_rows


class MovementChargeVerifierTests(unittest.TestCase):
    def test_zero_charge_requires_exact_basal_and_birth_dissipation(self):
        end={**INITIAL,'tick':1,'organism_energy':1840,'dissipated_energy':80}
        self.assertEqual(verify_rows([INITIAL,end],0,steps=1)['population'],80)
        changed={**end,'organism_energy':1839,'dissipated_energy':81}
        verify_rows([INITIAL,changed],1,steps=1)
        with self.assertRaisesRegex(ValueError,'Zero-charge'):
            verify_rows([INITIAL,changed],0,steps=1)

    def test_zero_charge_does_not_skip_existing_metric_checks(self):
        end={**INITIAL,'tick':1,'organism_energy':1840,'dissipated_energy':80,'mean_genome':251}
        with self.assertRaisesRegex(ValueError,'trait'):
            verify_rows([INITIAL,end],0,steps=1)
