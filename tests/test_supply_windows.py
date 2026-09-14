import unittest
from scripts.analyze_v0_supply_windows import partition


class SupplyWindowTests(unittest.TestCase):
    def fixture(self):
        return [dict(tick=0,population=1,food_energy=5,supplied_energy=6,organism_energy=1,dissipated_energy=0),
                dict(tick=1,population=0,food_energy=7,supplied_energy=8,organism_energy=0,dissipated_energy=1),
                dict(tick=2,population=0,food_energy=11,supplied_energy=12,organism_energy=0,dissipated_energy=1)]

    def test_extinction_tick_belongs_to_active_start(self):
        result=partition(self.fixture(),1)
        self.assertEqual(result['added_during_active_start_ticks'],2)
        self.assertEqual(result['added_after_extinction'],4)
        self.assertEqual(result['cumulative_uptake'],0)
        self.assertEqual(result['active_start_ticks'],1)

    def test_absorbing_state_corruption_rejected(self):
        rows=self.fixture();rows[-1]['food_energy']-=1
        with self.assertRaises(ValueError):partition(rows,1)
        with self.assertRaises(ValueError):partition(self.fixture(),None)

    def test_survivor_and_horizon_death_have_distinct_censoring(self):
        dead=partition(self.fixture()[:2],1)
        self.assertEqual(dead['added_after_extinction'],0)
        self.assertFalse(dead['right_censored'])
        rows=self.fixture()[:2];rows[-1].update(population=1,organism_energy=1,food_energy=6)
        live=partition(rows,None)
        self.assertEqual(live['added_after_extinction'],0)
        self.assertTrue(live['right_censored'])
