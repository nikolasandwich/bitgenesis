from dataclasses import asdict
from random import Random
import unittest
from unittest.mock import patch

from bitgenesis.v2.development import DevelopmentGenome
from bitgenesis.v2.world import Config, World

FIXTURE=DevelopmentGenome((6,100,0,0,0,0,0,0,1,1))


class DevelopmentWorldTests(unittest.TestCase):
    def test_paid_founder_and_child_development(self):
        config=Config(width=3,height=3,founders=1,initial_energy=200,birth_threshold=160,
                      basal_cost=0,decision_cost=0,feeding_limit=0,renewal_per_thousand=0,
                      mutation_per_thousand=0)
        with patch('bitgenesis.v2.world.DevelopmentGenome.random',return_value=FIXTURE):
            world=World(config,81000)
        self.assertEqual(world.initialization_spent,36)
        self.assertEqual(world.organisms[0].energy,164)
        record=world.step()
        self.assertEqual(len(record['actors']),1)
        self.assertEqual(len(world.organisms),2)
        self.assertEqual((world.organisms[0].energy,world.organisms[1].energy),(82,46))
        self.assertEqual(record['spent'],36)
        self.assertEqual(world.organisms[1].genome,FIXTURE)
        self.assertEqual(world.organisms[0].offspring,1)

    def test_failed_child_is_logged_and_loses_its_allocation(self):
        config=Config(width=3,height=3,founders=1,initial_energy=80,birth_threshold=40,
                      basal_cost=0,decision_cost=0,feeding_limit=0,renewal_per_thousand=0,
                      mutation_per_thousand=0)
        with patch('bitgenesis.v2.world.DevelopmentGenome.random',return_value=FIXTURE):
            world=World(config,81001)
        row=world.step()['actors'][0]
        self.assertEqual(len(world.organisms),1)
        self.assertEqual(len(world.attempts),2)
        self.assertEqual(world.attempts[-1]['reason'],'round_budget')
        self.assertEqual(row['failure_loss'],22)
        self.assertEqual(row['child_energy'],0)
        self.assertEqual(world.organisms[0].offspring,0)
        self.assertEqual(world.organisms[0].energy,22)

    def test_initial_failure_has_no_free_living_individual(self):
        with patch('bitgenesis.v2.world.DevelopmentGenome.random',return_value=FIXTURE):
            world=World(Config(width=3,height=3,founders=2,initial_energy=35),81002)
        self.assertFalse(world.organisms)
        self.assertEqual(world.initialization_spent,70)
        self.assertEqual(len(world.attempts),2)
        self.assertTrue(all(not a['valid'] for a in world.attempts))

    def test_both_encodings_replay_and_accounting(self):
        for encoding in ('developmental','direct'):
            config=Config(width=5,height=5,founders=8,initial_energy=640,birth_threshold=800)
            a,b=World(config,81003,encoding=encoding),World(config,81003,encoding=encoding)
            for _ in range(50):
                record=a.step()
                self.assertEqual(record,b.step())
                for actor in record['actors']:
                    self.assertEqual(actor['energy_after'],actor['energy_before']+actor['intake']-
                        sum(actor[k] for k in ('basal','decision','movement','birth_cost','development_cost','failure_loss','child_energy')))
                self.assertEqual(len(a.occupied),len(a.organisms))
            self.assertEqual(a.attempts,b.attempts)
            self.assertEqual(a.events,b.events)
            for attempt in a.attempts:
                self.assertEqual(attempt['allocation'],attempt['construction_cost']+attempt['failure_loss']+attempt['living_energy'])
