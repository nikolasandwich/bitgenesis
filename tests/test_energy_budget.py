import unittest
from unittest.mock import patch

from bitgenesis.v0.engine import Config, World
from scripts.analyze_v0_energy_budget import budget


class EnergyBudgetTests(unittest.TestCase):
    def test_reconstruction_matches_instrumented_charges(self):
        world = World(Config(seed=51, width=8, height=8, initial_population=12,
                             movement_cost=3, birth_cost=5))
        charged = {1: 0, 3: 0, 5: 0}
        original = World._pay
        def record(instance, organism, amount):
            before = organism.energy
            original(instance, organism, amount)
            charged[amount] += before - organism.energy
        rows = [world.snapshot()]
        with patch.object(World, "_pay", record):
            for _ in range(100):
                world.step()
                rows.append(world.snapshot())
        actual = budget(rows, 0, 100, birth_cost=5)
        self.assertEqual((actual["basal"], actual["movement"], actual["reproduction"]),
                         (charged[1], charged[3], charged[5]))
        self.assertGreater(charged[3], 0)
        self.assertGreater(charged[5], 0)

    def test_zero_birth_cost_matches_actual_charges_with_births_and_deaths(self):
        world = World(Config(seed=52, width=8, height=8, initial_population=12,
                             initial_energy=88, initial_food=0,
                             regrowth_probability=15, mutation_probability=0,
                             movement_cost=3, birth_cost=0))
        for organism in world.living.values():
            organism.genome = 250
        charged = {0: 0, 1: 0, 3: 0}
        calls = {0: 0, 1: 0, 3: 0}
        original = World._pay

        def record(instance, organism, amount):
            before = organism.energy
            original(instance, organism, amount)
            charged[amount] += before - organism.energy
            calls[amount] += 1

        rows = [world.snapshot()]
        with patch.object(World, "_pay", record):
            for _ in range(100):
                world.step()
                world.check_invariants()
                rows.append(world.snapshot())
        actual = budget(rows, 0, 100, birth_cost=0)
        self.assertEqual((actual["basal"], actual["movement"], actual["reproduction"]),
                         (charged[1], charged[3], charged[0]))
        self.assertGreater(calls[0], 0)
        self.assertEqual(calls[0], rows[-1]["births"])
        self.assertEqual(actual["reproduction"], 0)
        self.assertGreater(rows[-1]["deaths"], 0)
        self.assertGreater(charged[1] + charged[3], 0)

    def test_unsupported_basal_cost_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "basal_cost=1"):
            budget([], 0, 1, basal_cost=2)

    def test_corrupted_dissipation_is_rejected(self):
        world = World(Config())
        rows = [world.snapshot()]
        world.step()
        rows.append(world.snapshot())
        rows[-1]["dissipated_energy"] = 0
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            budget(rows, 0, 1)
