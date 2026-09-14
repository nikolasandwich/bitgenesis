import unittest
from dataclasses import asdict

from bitgenesis.v1.controller import Genome
from bitgenesis.v1.world import Config, World


def fixed_action(action):
    weights = [0] * 35
    weights[action * 7 + 6] = 1
    return Genome(tuple(weights))


class WorldTests(unittest.TestCase):
    def test_replay_and_individual_accounting(self):
        config = Config(width=8, height=8, founders=12)
        a, b = World(config, 70001), World(config, 70001)
        for _ in range(100):
            record = a.step()
            self.assertEqual(record, b.step())
            self.assertEqual(len(a.occupied), len(a.organisms))
            self.assertEqual(set(a.occupied.values()), set(a.organisms))
            for r in record['actors']:
                self.assertEqual(r['energy_after'], r['energy_before'] + r['intake']
                    - sum(r[k] for k in ('basal', 'decision', 'movement', 'birth_cost', 'child_energy')))
            self.assertTrue(all(0 <= f <= config.capacity for f in a.food))
        self.assertEqual(a.events, b.events)
        self.assertEqual([asdict(o) for o in a.lineage.values()], [asdict(o) for o in b.lineage.values()])
        self.assertEqual({k: r.getstate() for k, r in a.rng.items()},
                         {k: r.getstate() for k, r in b.rng.items()})

    def test_death_before_food_or_decision(self):
        for energy, phase in ((1, 'basal'), (2, 'decision')):
            w = World(Config(width=3, height=3, founders=1, initial_energy=energy,
                             renewal_per_thousand=0), 70002)
            tie_state = w.rng['ties'].getstate()
            row = w.step()['actors'][0]
            self.assertEqual(len(w.organisms), 0)
            self.assertEqual(row['intake'], 0)
            self.assertIsNone(row['action'])
            self.assertEqual(w.events[-1]['phase'], phase)
            self.assertEqual(tie_state, w.rng['ties'].getstate())

    def test_blocked_attempt_is_charged_without_reproduction_space(self):
        w = World(Config(width=3, height=3, founders=9, initial_energy=100,
                         basal_cost=0, decision_cost=0, movement_cost=3,
                         feeding_limit=0, renewal_per_thousand=0), 70003)
        for o in w.organisms.values():
            o.genome = fixed_action(1)
        positions = dict(w.occupied)
        records = w.step()['actors']
        self.assertEqual(w.occupied, positions)
        self.assertEqual(len(w.lineage), 9)
        self.assertTrue(all(r['blocked'] and r['movement'] == 3 for r in records))

    def test_birth_transfer_ancestry_and_newborn_wait(self):
        w = World(Config(width=3, height=3, founders=1, initial_energy=80,
                         basal_cost=0, decision_cost=0, birth_cost=4,
                         feeding_limit=0, renewal_per_thousand=0,
                         mutation_per_thousand=0), 70004)
        parent = w.organisms[0]
        parent.genome = fixed_action(0)
        result = w.step()
        self.assertEqual(len(result['actors']), 1)
        self.assertEqual(parent.energy, 38)
        child = w.organisms[1]
        self.assertEqual((child.energy, child.parent, child.founder, child.generation, child.birth_tick),
                         (38, 0, 0, 1, 1))
        self.assertEqual(child.genome, parent.genome)
        self.assertEqual(parent.offspring, 1)
        self.assertEqual(result['spent'], 4)

    def test_resource_proposals_stay_aligned_after_extinction(self):
        a = World(Config(width=3, height=3, founders=0, initial_food=0), 70005)
        b = World(Config(width=3, height=3, founders=0, initial_food=24), 70005)
        for _ in range(10):
            a.step()
            b.step()
        self.assertEqual(a.rng['resources'].getstate(), b.rng['resources'].getstate())
        self.assertNotEqual(a.food, b.food)

    def test_interventions_pay_equal_costs_and_draw_counts(self):
        worlds = [World(Config(width=3, height=3, founders=1, feeding_limit=0,
                              birth_threshold=1000), 70006, mode)
                  for mode in ('intact', 'blind', 'shuffled')]
        for w in worlds:
            w.organisms[0].genome = fixed_action(0)
        records = [w.step()['actors'][0] for w in worlds]
        self.assertEqual([r['decision'] for r in records], [1, 1, 1])
        self.assertEqual(len({r['tie_ticket'] for r in records}), 1)
        self.assertEqual(len({r['permutation'] for r in records}), 1)
        self.assertEqual(records[1]['sensed'][:5], (0,) * 5)
        self.assertEqual(records[0]['inputs'][5], 137)

    def test_wrap_and_movement_death_before_feeding(self):
        for energy, survives in ((10, True), (3, False)):
            w = World(Config(width=3, height=3, founders=1, initial_energy=energy,
                             basal_cost=0, decision_cost=0, movement_cost=3,
                             renewal_per_thousand=0), 70007)
            o = w.organisms[0]
            w.occupied.clear()
            o.x, o.y = 2, 1
            w.occupied[(2, 1)] = 0
            o.genome = fixed_action(1)
            r = w.step()['actors'][0]
            self.assertFalse(r['blocked'])
            if survives:
                self.assertEqual((o.x, o.y), (0, 1))
                self.assertEqual(r['intake'], 8)
            else:
                self.assertEqual(len(w.organisms), 0)
                self.assertEqual(r['intake'], 0)
                self.assertEqual(w.events[-1]['phase'], 'movement')
