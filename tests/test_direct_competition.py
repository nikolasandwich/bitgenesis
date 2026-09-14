import csv
from dataclasses import asdict, replace
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config
from scripts.run_v0_food_geometry import food_map
from scripts.run_v0_direct_competition import initialize, evaluate


class DirectCompetitionTests(unittest.TestCase):
    def test_observer_matches_plain_world_and_neutral_swaps_complement(self):
        base = load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        for seed in (24, 25):
            for sampled, ancestor in ((0, 1000), (256, 250), (250, 250)):
                with tempfile.TemporaryDirectory() as temp:
                    results = []
                    for swap in (0, 1):
                        world, groups = initialize(base, seed, sampled, ancestor, swap)
                        plain = World(replace(base, seed=seed, initial_food=0, mutation_probability=0,
                            regrowth_probability=15, regrowth_amount=4, food_capacity=24,
                            birth_threshold=40, birth_cost=0, movement_cost=0, mutation_step=100))
                        for i, organism in plain.living.items():
                            organism.genome = sampled if (i < 40) != bool(swap) else ancestor
                        for event in plain.events:
                            event['genome'] = plain.living[event['id']].genome
                        plain.food[:] = food_map('block', seed); plain.supplied_energy += 5120
                        calls = []
                        def compare(recorded):
                            if recorded.tick:
                                plain.step()
                            self.assertEqual(recorded.snapshot(), plain.snapshot())
                            self.assertEqual(recorded.food, plain.food)
                            self.assertEqual(recorded.events, plain.events)
                            self.assertEqual(recorded.occupied, plain.occupied)
                            self.assertEqual(recorded.rng.getstate(), plain.rng.getstate())
                            self.assertEqual([asdict(o) for o in recorded.lineage.values()],
                                             [asdict(o) for o in plain.lineage.values()])
                            calls.append(recorded.tick); plain.events.clear()
                        result = evaluate(world, groups, Path(temp)/str(swap), 100,
                                          dict(swap=swap, sampled_trait=sampled, ancestor_trait=ancestor), compare)
                        results.append(result)
                        self.assertEqual(calls, list(range(101)))
                    if sampled == ancestor:
                        self.assertEqual(results[0]['final_state_sha256'], results[1]['final_state_sha256'])
                        for name in ('metrics.csv', 'events.jsonl', 'lineage.json'):
                            self.assertEqual((Path(temp)/'0'/name).read_bytes(), (Path(temp)/'1'/name).read_bytes())
                        def read(swap):
                            with (Path(temp)/str(swap)/'groups.csv').open(newline='') as stream:
                                return list(csv.DictReader(stream))
                        for a, b in zip(read(0), read(1), strict=True):
                            self.assertEqual(a['tick'], b['tick'])
                            for key in a:
                                if key.startswith('sampled_'):
                                    self.assertEqual(a[key], b[key.replace('sampled_', 'ancestor_', 1)])
                                elif key.startswith('ancestor_'):
                                    self.assertEqual(a[key], b[key.replace('ancestor_', 'sampled_', 1)])

    def test_invalid_trait_and_allocation_rejected(self):
        base = load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        for sampled, ancestor, swap in ((True, 250, 0), (-1, 250, 0), (250, 1001, 0), (250, 250, True), (250, 250, 2)):
            with self.assertRaises(ValueError):
                initialize(base, 24, sampled, ancestor, swap)
