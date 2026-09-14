from fractions import Fraction
import unittest
from scripts.analyze_v0_intake_opportunity import opportunity


class IntakeOpportunityTests(unittest.TestCase):
    def local(self,energy=2,here=0):
        return dict(energy_before_action=energy,sites=[dict(position=0,food=here,occupant_id=0)]+[dict(position=i,food=8 if i==1 else 0,occupant_id=None) for i in range(1,5)])

    def test_single_food_neighbor_and_basal_death(self):
        r=opportunity(self.local());self.assertEqual(r['expected_intake'],Fraction(1,2));self.assertEqual(r['positive_intake_probability'],Fraction(1,16))
        self.assertEqual(opportunity(self.local(energy=1))['expected_intake'],0)

    def test_occupied_target_stays_on_current_food(self):
        row=self.local(here=8)
        for site in row['sites'][1:]:site['occupant_id']=site['position']
        self.assertEqual(opportunity(row),dict(expected_intake=Fraction(8),positive_intake_probability=Fraction(1)))
        row=self.local();row['sites'][1]['occupant_id']=1
        self.assertEqual(opportunity(row)['expected_intake'],0)

    def test_all_empty_neighbors_with_food(self):
        row=self.local()
        for site in row['sites'][1:]:site['food']=24
        self.assertEqual(opportunity(row),dict(expected_intake=Fraction(2),positive_intake_probability=Fraction(1,4)))
