import copy
from dataclasses import asdict
import json
from random import Random
import unittest

from bitgenesis.v2.construction_audit import reconstruct,verify_attempt
from bitgenesis.v2.development import DevelopmentGenome,develop
from bitgenesis.v2.direct_control import construct_direct
from bitgenesis.v2.world import World,Config


def serialized(value):
    return json.loads(json.dumps(asdict(value)))


class ConstructionAuditTests(unittest.TestCase):
    def test_independent_reconstruction_across_budgets(self):
        rng=Random(81200)
        for _ in range(100):
            genome=DevelopmentGenome.random(rng)
            for budget in (0,34,35,36,100,640):
                self.assertEqual(reconstruct({'genes':list(genome.genes)},'developmental',budget),
                                 serialized(develop(genome,budget)))
        for weights in ((0,)*35,(1,)+(0,)*34,tuple(range(-17,18))):
            for budget in (0,34,35,36,70,100):
                for padding in (0,20):
                    self.assertEqual(reconstruct({'weights':list(weights)},'direct',budget,padding),
                                     serialized(construct_direct(weights,budget,padding)))

    def test_corrupted_attempts_rejected(self):
        world=World(Config(width=5,height=5,founders=10),81201)
        attempts=json.loads(json.dumps(world.attempts))
        for attempt in attempts:
            verify_attempt(attempt)
        for field in ('construction_cost','failure_loss','living_energy'):
            altered=copy.deepcopy(attempts[0])
            altered[field]+=1
            with self.assertRaises(ValueError):
                verify_attempt(altered)
        altered=copy.deepcopy(attempts[0])
        altered['construction']['history'][0][0]+=1
        with self.assertRaises(ValueError):
            verify_attempt(altered)
