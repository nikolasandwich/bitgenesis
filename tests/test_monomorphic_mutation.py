from collections import Counter
from dataclasses import asdict, replace
import json
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config
from scripts.run_v0_food_geometry import food_map
from scripts.run_v0_monomorphic_mutation import initialize, record_world


class MonomorphicMutationTests(unittest.TestCase):
    def test_both_recorded_treatments_match_plain_engine_each_tick(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        initial_states=[]
        for mutation in (0,100):
            recorded=initialize(base,23,mutation)
            plain=World(replace(base,seed=23,initial_food=0,mutation_probability=mutation,
                regrowth_probability=15,regrowth_amount=4,food_capacity=24,birth_threshold=40,
                birth_cost=0,movement_cost=0,mutation_step=100))
            for o in plain.living.values():o.genome=250
            for event in plain.events:event['genome']=250
            plain.food[:]=food_map('block',23);plain.supplied_energy+=5120
            initial_states.append(([asdict(o) for o in recorded.living.values()],recorded.food[:],recorded.rng.getstate()))
            calls=[]
            def compare(world):
                if world.tick:plain.step()
                self.assertEqual(world.snapshot(),plain.snapshot())
                self.assertEqual(world.food,plain.food)
                self.assertEqual(world.occupied,plain.occupied)
                self.assertEqual([asdict(o) for o in world.lineage.values()],[asdict(o) for o in plain.lineage.values()])
                self.assertEqual(world.events,plain.events)
                self.assertEqual(world.rng.getstate(),plain.rng.getstate())
                calls.append(world.tick);plain.events.clear()
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp)/'world';result=record_world(recorded,out,100,compare)
                self.assertEqual(calls,list(range(101)))
                events=[json.loads(s) for s in (out/'events.jsonl').read_text().splitlines()]
                births=[e for e in events if e['event']=='birth']
                self.assertEqual(len(births),80+result['births'])
                self.assertTrue(all(e['birth_tick']==e['tick'] for e in births))
                self.assertEqual({e['genome'] for e in births[:80]},{250})
                self.assertTrue(all(e['energy']==24 for e in births[:80]))
                lineage=json.loads((out/'lineage.json').read_text())
                born={str(k):v for k,v in sorted(Counter(e['genome'] for e in births).items())}
                self.assertEqual(born,result['observations']['100']['ever_born_genome_histogram'])
                alive={str(k):v for k,v in sorted(Counter(o['genome'] for o in lineage if o['death_tick'] is None).items())}
                self.assertEqual(alive,result['observations']['100']['living_genome_histogram'])
                if mutation==0:self.assertEqual(set(born),{'250'});self.assertEqual(result['changed_births'],0)
                else:self.assertGreater(result['changed_births'],0)
        self.assertEqual(initial_states[0],initial_states[1])

    def test_undeclared_mutation_and_existing_output_rejected(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        for value in (True,1,1000):
            with self.assertRaises(ValueError):initialize(base,23,value)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileExistsError):record_world(initialize(base,23,0),Path(tmp),100)


if __name__=='__main__':unittest.main()
