import unittest
from scripts.summarize_v0_renewal_granularity import INITIAL, verify_rows


class RenewalVerifierTests(unittest.TestCase):
    def transition(self, supply):
        return {**INITIAL, "tick": 1, "food_energy": 5120+supply,
                "supplied_energy": 7040+supply, "organism_energy": 1840,
                "dissipated_energy": 80}

    def test_packet_specific_supply_bound(self):
        # Accounting-valid aggregate transitions, not claims of spatial realizability.
        for amount in (1,4,12):
            with self.subTest(amount=amount):
                verify_rows([INITIAL,self.transition(1024*amount)],amount,steps=1)
                with self.assertRaisesRegex(ValueError,"transition bounds"):
                    verify_rows([INITIAL,self.transition(1024*amount+1)],amount,steps=1)
        with self.assertRaises(ValueError):
            verify_rows([INITIAL,self.transition(0)],True,steps=1)

    def test_hidden_charge_rejected_even_when_energy_balances(self):
        row=self.transition(0)
        row.update(organism_energy=1836,dissipated_energy=84)
        with self.assertRaisesRegex(ValueError,"transition bounds"):
            verify_rows([INITIAL,row],4,steps=1)

    def test_excess_uptake_rejected_even_when_energy_balances(self):
        row=self.transition(0)
        row["food_energy"]-=641
        row["organism_energy"]+=641
        with self.assertRaisesRegex(ValueError,"uptake bounds"):
            verify_rows([INITIAL,row],4,steps=1)
