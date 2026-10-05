import unittest
from scripts.verify_v4_middle_energy import energy_stage, eligible_intervals
class MiddleEnergyVerifierTests(unittest.TestCase):
    def test_threshold_and_gaps(self):
        self.assertEqual(eligible_intervals([(3,16),(4,15),(5,16)]),[[3,3],[5,5]])
        self.assertEqual(eligible_intervals([]),[])
    def test_paid_bonds_require_both_endpoint_reservations(self):
        units=[None]*256
        for site,energy in ((85,2),(86,2),(87,2)):
            units[site]={'energy':energy,'material':0}
        energies,bonds,inputs=energy_stage(units,[0]*256)
        self.assertEqual(bonds,[])
        self.assertEqual(energies[86],1)
        units[86]['energy']=3
        energies,bonds,inputs=energy_stage(units,[0]*256)
        self.assertEqual(bonds,[[85,86],[86,87]])
        self.assertEqual(energies[86],0)
    def test_leak_saturates_at_zero(self):
        units=[None]*256;units[101]={'energy':0,'material':0}
        energies,bonds,inputs=energy_stage(units,[0]*256)
        self.assertEqual(inputs[101]['leakage'],0)
        self.assertEqual(energies[101],0)
