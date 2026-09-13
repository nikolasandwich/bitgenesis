import unittest

from bitgenesis.v0.engine import Config, World
from scripts.analyze_v0_geometry_budget import uptake


class GeometryBudgetTests(unittest.TestCase):
    def test_uptake_matches_observed_food_removals_without_changing_world(self):
        class ObservedFood(list):
            eaten = 0
            def __setitem__(self, position, value):
                self.eaten += max(0,self[position]-value)
                super().__setitem__(position,value)
        config=Config(width=8,height=8,initial_population=12)
        observed,reference=World(config),World(config)
        observed.food=ObservedFood(observed.food)
        rows=[observed.snapshot()]
        for _ in range(100):
            observed.step();reference.step();rows.append(observed.snapshot())
            self.assertEqual(observed.snapshot(),reference.snapshot())
            self.assertEqual(observed.rng.getstate(),reference.rng.getstate())
        self.assertGreater(observed.food.eaten,0)
        self.assertEqual(uptake(rows),observed.food.eaten)

    def test_inconsistent_uptake_is_rejected(self):
        first=dict(supplied_energy=10,food_energy=8,organism_energy=2,
                   dissipated_energy=0,population=1)
        valid=dict(supplied_energy=12,food_energy=7,organism_energy=4,
                   dissipated_energy=1,population=1)
        self.assertEqual(uptake([first,valid]),3)
        for field,value in (("food_energy",20),("supplied_energy",30),("organism_energy",5)):
            wrong=dict(valid);wrong[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                uptake([first,wrong])
