from dataclasses import asdict,replace
import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config
from scripts.run_v0_food_geometry import food_map
from scripts.run_v0_common_environment import initialize,evaluate


class CommonEnvironmentTests(unittest.TestCase):
    def test_seed_trait_extremes_and_recording_match_plain_world(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        for seed in (23,24):
            paired_initial=[]
            for trait in (0,250,1000):
                world=initialize(base,seed,trait)
                plain=World(replace(base,seed=seed,initial_food=0,regrowth_probability=15,regrowth_amount=4,food_capacity=24,birth_threshold=40,birth_cost=0,movement_cost=0,mutation_probability=0,mutation_step=100))
                for o in plain.living.values():o.genome=trait
                for e in plain.events:e['genome']=trait
                plain.food[:]=food_map('block',seed);plain.supplied_energy+=5120
                paired_initial.append((world.food[:],[(o.id,o.position,o.energy) for o in world.living.values()],world.rng.getstate()))
                calls=[]
                def compare(recorded):
                    if recorded.tick:plain.step()
                    self.assertEqual(recorded.snapshot(),plain.snapshot());self.assertEqual(recorded.food,plain.food)
                    self.assertEqual(recorded.events,plain.events);self.assertEqual(recorded.rng.getstate(),plain.rng.getstate())
                    self.assertEqual(recorded.occupied,plain.occupied)
                    self.assertEqual([asdict(o) for o in recorded.lineage.values()],[asdict(o) for o in plain.lineage.values()])
                    calls.append(recorded.tick);plain.events.clear()
                with tempfile.TemporaryDirectory() as tmp:
                    a=Path(tmp)/'a';b=Path(tmp)/'b'
                    identity=dict(source_seed=1900,replicate=0,arm='sampled',founder_trait=trait,sampled_individual_id=0,source_founder_id=0)
                    result=evaluate(world,a,100,identity,compare)
                    other=evaluate(initialize(base,seed,trait),b,100,{**identity,'arm':'ancestor'})
                    self.assertEqual(calls,list(range(101)))
                    initial=json.loads((a/'initial.json').read_text())
                    self.assertEqual(initial['snapshot']['mean_genome'],trait)
                    self.assertEqual({o['genome'] for o in initial['founders']},{trait})
                    self.assertEqual(result['final_state_sha256'],other['final_state_sha256'])
                    for name in ('metrics.csv','events.jsonl','lineage.json'):self.assertEqual((a/name).read_bytes(),(b/name).read_bytes())
            self.assertEqual(paired_initial[0],paired_initial[1]);self.assertEqual(paired_initial[1],paired_initial[2])

    def test_invalid_fixed_trait_rejected(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        for value in (-1,1001,True,2.5):
            with self.assertRaises(ValueError):initialize(base,23,value)


if __name__=='__main__':unittest.main()
