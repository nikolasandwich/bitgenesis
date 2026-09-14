from dataclasses import asdict
import unittest
from bitgenesis.v0.engine import Config, World
from scripts.observe_v0_energy import EnergyWorld
from scripts.observe_v0_local_resources import LocalResourceWorld


class LocalResourceObserverTests(unittest.TestCase):
    def test_world_rng_and_all_existing_streams_are_unchanged(self):
        cases = [Config(seed=s,width=8,height=8,initial_population=12,
                        movement_cost=0,birth_cost=cost) for s in (5,23) for cost in (0,4)]
        cases += [Config(width=2,height=2,initial_population=4,initial_energy=40),
                  Config(width=2,height=2,initial_population=1,initial_energy=3,movement_cost=9)]
        for config in cases:
            with self.subTest(config=config):
                observed, reference, plain = LocalResourceWorld(config), EnergyWorld(config), World(config)
                for world in (observed,reference,plain):
                    for organism in world.living.values():organism.genome=1000
                for _ in range(100):
                    actors={i:(o.position,o.energy) for i,o in observed.living.items()}
                    for world in (observed,reference,plain):world.step()
                    rows=observed.drain_local_resources()
                    self.assertEqual(len(rows),len(actors))
                    self.assertEqual({r['id'] for r in rows},set(actors))
                    for row in rows:
                        self.assertEqual((row['position'],row['energy_before_action']),actors[row['id']])
                        self.assertEqual(row['sites'][0]['occupant_id'],row['id'])
                        self.assertEqual(len({r['position'] for r in row['sites']}),len(row['sites']))
                    for drain in ('drain_feeding','drain_pre_feeding_deaths','drain_energy'):
                        self.assertEqual(getattr(observed,drain)(),getattr(reference,drain)())
                    for other in (reference,plain):
                        self.assertEqual(observed.snapshot(),other.snapshot())
                        self.assertEqual(observed.food,other.food)
                        self.assertEqual(observed.occupied,other.occupied)
                        self.assertEqual(observed.events,other.events)
                        self.assertEqual(observed.rng.getstate(),other.rng.getstate())
                        self.assertEqual([asdict(o) for o in observed.lineage.values()],
                                         [asdict(o) for o in other.lineage.values()])
                self.assertEqual(observed.drain_local_resources(),[])

    def test_local_snapshot_follows_regrowth_and_precedes_lethal_basal_payment(self):
        world=LocalResourceWorld(Config(width=3,height=3,initial_population=1,
            initial_energy=1,initial_food=0,regrowth_probability=1000,regrowth_amount=4))
        actor=world.living[0];position=actor.position
        expected=list(dict.fromkeys([position,*world.neighbors(position)]))
        world.step();row,=world.drain_local_resources()
        self.assertEqual(row['energy_before_action'],1)
        self.assertEqual([s['position'] for s in row['sites']],expected)
        self.assertEqual([s['food'] for s in row['sites']],[4]*5)
        self.assertEqual([s['occupant_id'] for s in row['sites']],[0,None,None,None,None])
        self.assertEqual(world.drain_feeding(),[])
        self.assertEqual(world.drain_pre_feeding_deaths()[0]['phase'],'basal')
        self.assertEqual(world.snapshot()['population'],0)
        # Retained values are snapshots, not references to mutable world containers.
        world.food[position]=9
        self.assertEqual(row['sites'][0]['food'],4)

    def test_narrow_world_sites_deduplicate_and_record_occupancy(self):
        world=LocalResourceWorld(Config(width=2,height=2,initial_population=4,
            initial_energy=40,initial_food=8,regrowth_probability=0))
        for actor in world.living.values():actor.genome=0
        world.step();rows=world.drain_local_resources()
        self.assertEqual(len(rows),4)
        self.assertTrue(all(len(r['sites'])==3 for r in rows))
        self.assertTrue(all(s['occupant_id'] is not None for r in rows for s in r['sites']))
        self.assertEqual(sorted(s['food'] for s in rows[0]['sites']),[8,8,8])
        self.assertEqual(sorted(s['food'] for s in rows[-1]['sites']),[0,0,8])
