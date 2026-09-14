from dataclasses import asdict
from random import Random
import unittest

from bitgenesis.v2.development import DevelopmentGenome
from bitgenesis.v3.genome import EcologyGenome
from bitgenesis.v3.world import Config, World


class EcologyWorldTests(unittest.TestCase):
    def genome(self):
        return EcologyGenome(DevelopmentGenome((6,100,0,0,0,0,0,0,1,1)),16)

    def test_replay_births_and_independent_energy_accounting(self):
        config = Config(width=5,height=5,founders=4,initial_energy=400,birth_threshold=160,initial_b=24)
        worlds = [World(config,85000,founder_genomes=[self.genome()]*4) for _ in range(2)]
        dissipated = 0
        for _ in range(100):
            records = [w.step() for w in worlds]
            self.assertEqual(records[0],records[1])
            row = records[0]
            for actor in row['actors']:
                feeding = actor['feeding']
                if feeding is not None:
                    self.assertEqual(feeding['a_before']+feeding['b_before'],
                        feeding['remaining_a']+feeding['remaining_b']+
                        feeding['energy_gain']+feeding['dissipated'])
                self.assertEqual(actor['energy_after'], actor['energy_before'] + actor['intake']
                    -sum(actor[k] for k in ('basal','decision','movement','birth_cost',
                                            'child_energy','development_cost','failure_loss')))
            dissipated += sum(a['dissipated'] for a in row['actors'])
        self.assertGreater(len(worlds[0].attempts),4)
        self.assertGreater(dissipated,0)
        self.assertEqual([asdict(o) for o in worlds[0].lineage.values()],
                         [asdict(o) for o in worlds[1].lineage.values()])

    def test_recycling_removal_keeps_first_intake_yield(self):
        worlds=[World(Config(width=3,height=3,founders=1,recycling=r),85001,
                      founder_genomes=[self.genome()]) for r in (0,1)]
        rows=[w.step() for w in worlds]
        self.assertEqual(rows[0]['actors'][0]['intake'],rows[1]['actors'][0]['intake'])
        self.assertEqual(sum(worlds[0].substrate_b),0)
        self.assertGreater(sum(worlds[1].substrate_b),0)

    def test_joint_mutation_is_bounded_and_reaches_both_parts(self):
        genome=self.genome()
        rng=Random(85002)
        offspring=[genome.offspring(rng,1000) for _ in range(500)]
        self.assertTrue(any(g.development!=genome.development for g in offspring))
        self.assertTrue(any(g.allocation_a!=genome.allocation_a for g in offspring))
        self.assertEqual(genome.offspring(rng,0),genome)
        for g in offspring:
            self.assertLessEqual(sum(a!=b for a,b in zip(g.development.genes,genome.development.genes))
                                 +(g.allocation_a!=genome.allocation_a),1)

    def test_failed_founders_and_empty_world(self):
        invalid=EcologyGenome(DevelopmentGenome((0,0,0,0,0,0,0,0,1,1)),8)
        world=World(Config(width=3,height=3,founders=2),85003,founder_genomes=[invalid]*2)
        self.assertEqual(len(world.organisms),0)
        self.assertEqual(len(world.attempts),2)
        self.assertEqual(world.step()['population'],0)


if __name__=='__main__':
    unittest.main()
