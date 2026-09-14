import unittest
from collections import Counter
from random import Random

from bitgenesis.v1.controller import Genome, inputs, intervene


class ControllerTests(unittest.TestCase):
    def test_exact_uniform_ties_for_every_possible_tie_count(self):
        values = inputs((0,) * 5, 0, 80)
        for count in range(1, 6):
            weights = tuple(1 if i % 7 == 6 and i // 7 < count else 0 for i in range(35))
            genome = Genome(weights)
            self.assertEqual(Counter(genome.action(values, ticket) for ticket in range(60)),
                             Counter({i: 60 // count for i in range(count)}))

    def test_normalization_and_interventions(self):
        values = inputs((24, 0, 6, 12, 18), 24, 80)
        self.assertEqual(values, (1000, 0, 250, 500, 750, 500, 1000))
        seen = [intervene(values, "shuffled", i) for i in range(24)]
        self.assertEqual(len(set(seen)), 24)
        for slot in range(1, 5):
            self.assertEqual(Counter(row[slot] for row in seen),
                             Counter({v: 6 for v in values[1:5]}))
        for row in seen:
            self.assertEqual(row[0], values[0])
            self.assertEqual(row[5:], values[5:])
        self.assertEqual(intervene(values, "blind", 0), (0, 0, 0, 0, 0, 500, 1000))
        self.assertEqual(inputs((0,) * 5, 0, 320)[5], 1000)

    def test_food_response_is_encoded_in_weights_not_action_selector(self):
        weights = [0] * 35
        weights[7 + 1] = 1
        weights[14 + 2] = 1
        genome = Genome(tuple(weights))
        self.assertEqual(genome.maxima(inputs((0, 10, 0, 0, 0), 10, 80)), (1,))
        self.assertEqual(genome.maxima(inputs((0, 0, 10, 0, 0), 10, 80)), (2,))
        self.assertEqual(Genome((0,) * 35).maxima(inputs((0, 10, 0, 0, 0), 10, 80)), tuple(range(5)))

    def test_inheritance_replay_bounds_and_sparse_mutation(self):
        left, right = Random(31), Random(31)
        genome = Genome.random(left)
        self.assertEqual(genome, Genome.random(right))
        for _ in range(1000):
            child = genome.offspring(left, 1000)
            self.assertEqual(child, genome.offspring(right, 1000))
            self.assertLessEqual(sum(a != b for a, b in zip(genome.weights, child.weights)), 1)
            self.assertTrue(all(abs(a - b) <= 10 for a, b in zip(genome.weights, child.weights)))
            genome = child
        self.assertEqual(genome.offspring(left, 0), genome)

    def test_invalid_values_rejected(self):
        for weights in [(0,) * 34, (True,) * 35, (101,) * 35, [0] * 35]:
            with self.assertRaises(ValueError):
                Genome(weights)
        with self.assertRaises(ValueError):
            inputs((1, 0, 0, 0, 0), 0, 10)
        with self.assertRaises(ValueError):
            inputs((0,) * 5, 24, 0)
        with self.assertRaises(ValueError):
            Genome((0,) * 35).action((0,) * 6 + (1000,), 60)
