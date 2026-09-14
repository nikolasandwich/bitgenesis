import unittest
from random import Random
from bitgenesis.v1.evaluation import action_distribution
from bitgenesis.v2.development import DevelopmentGenome, develop
from bitgenesis.v2.direct_control import construct_direct
from scripts.probe_v1_study001 import probe_states


class DevelopmentControlTests(unittest.TestCase):
    def test_mutation_replay_and_local_inheritance(self):
        a,b=Random(80000),Random(80000)
        genome=DevelopmentGenome.random(a)
        self.assertEqual(genome,DevelopmentGenome.random(b))
        for _ in range(1000):
            child=genome.offspring(a,1000)
            self.assertEqual(child,genome.offspring(b,1000))
            self.assertLessEqual(sum(x!=y for x,y in zip(genome.genes,child.genes)),1)
            genome=child
        self.assertEqual(genome.offspring(a,0),genome)

    def test_exact_direct_control_with_matched_spending(self):
        developed=develop(DevelopmentGenome((17,80,0,0,0,0,1,0,1,3)),1000)
        self.assertTrue(developed.valid)
        padding=35*(developed.rounds_completed-1)
        direct=construct_direct(developed.weights,1000,padding)
        self.assertEqual(direct.cost,developed.cost)
        self.assertEqual(direct.weights,developed.weights)
        for state in probe_states():
            for mode in ('intact','blind','shuffled'):
                self.assertEqual(action_distribution(developed.weights,state['normalized'],mode),
                                 action_distribution(direct.weights,state['normalized'],mode))

    def test_direct_failures_account_for_work(self):
        weights=(1,)+(0,)*34
        self.assertEqual(construct_direct(weights,34).reason,'read_budget')
        self.assertEqual(construct_direct(weights,35).cost,35)
        result=construct_direct(weights,40,10)
        self.assertFalse(result.valid)
        self.assertEqual(result.cost,36)
        self.assertEqual(result.reason,'padding_budget')
        self.assertFalse(construct_direct((0,)*35,100).valid)
