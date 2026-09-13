from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import unittest

from bitgenesis.v0.engine import Config, World
from scripts.run_v0_food_geometry import food_map
from scripts.summarize_v0_food_geometry import verify_initial, verify_rows


class FoodGeometryTests(unittest.TestCase):
    def initialized(self, arm):
        world = World(Config(seed=1300,initial_food=0,regrowth_probability=15,mutation_probability=0))
        for o in world.living.values():
            o.genome = 250
        world.food = food_map(arm,1300)
        world.supplied_energy += 5120
        document = dict(arm=arm,seed=1300,config=asdict(world.config),food=world.food.copy(),
            founders=[asdict(o) for o in world.living.values()],snapshot=world.snapshot(),
            rng_sha256=hashlib.sha256(json.dumps(world.rng.getstate()).encode()).hexdigest())
        return world, document

    def test_all_layouts_and_founder_rng_pairing(self):
        documents = []
        for arm in ("uniform","dispersed","block"):
            _, document = self.initialized(arm)
            result = verify_initial(document,arm,1300)
            self.assertTrue(0 <= result["founders_on_food"] <= 80)
            documents.append(document)
        self.assertTrue(all(d["founders"] == documents[0]["founders"] for d in documents))
        self.assertEqual(len({d["rng_sha256"] for d in documents}),1)

    def test_changed_geometry_with_same_energy_and_changed_rng_rejected(self):
        _, document = self.initialized("block")
        altered = deepcopy(document)
        full, empty = altered["food"].index(24), altered["food"].index(0)
        altered["food"][full], altered["food"][empty] = 0,24
        with self.assertRaisesRegex(ValueError,"layout"):
            verify_initial(altered,"block",1300)
        document["rng_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError,"RNG"):
            verify_initial(document,"block",1300)

    def test_metric_prefix_accounting_and_truncation(self):
        world, _ = self.initialized("uniform")
        rows = [world.snapshot()]
        for _ in range(2):
            world.step()
            rows.append(world.snapshot())
        self.assertEqual(verify_rows(rows,steps=2)["tick"],2)
        with self.assertRaisesRegex(ValueError,"Truncated"):
            verify_rows(rows[:-1],steps=2)
        rows[1]["organism_energy"] += 1
        with self.assertRaisesRegex(ValueError,"Energy"):
            verify_rows(rows,steps=2)
