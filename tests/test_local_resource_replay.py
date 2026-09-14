from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import unittest
from bitgenesis.v0.runner import load_config
from scripts.run_v0_joint_zero_charge import initialize as original
from scripts.replay_v0_local_resources import initialize, boundary, check_window


class LocalResourceReplayTests(unittest.TestCase):
    def test_engineering_initialization_and_twenty_tick_boundary_window(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        for cost in (0,4):
            ref=original(base,'block',40,cost,23)
            initial=dict(arm='block',birth_threshold=40,birth_cost=cost,movement_cost=0,seed=23,
                config=asdict(ref.config),food=list(ref.food),founders=[asdict(o) for o in ref.living.values()],
                snapshot=ref.snapshot(),rng_sha256=hashlib.sha256(json.dumps(ref.rng.getstate()).encode()).hexdigest())
            world=initialize(initial);boundaries=[];captured=[]
            for tick in range(31):
                world.local_capture_enabled=tick>10
                actors=set(world.living);before=world.snapshot()
                if tick:world.step();ref.step()
                self.assertEqual(world.snapshot(),ref.snapshot())
                self.assertEqual(world.rng.getstate(),ref.rng.getstate())
                streams=dict(local=world.drain_local_resources(),energy=world.drain_energy(),feeding=world.drain_feeding(),terminal=world.drain_pre_feeding_deaths())
                for drain in ('drain_energy','drain_feeding','drain_pre_feeding_deaths'):getattr(ref,drain)()
                if tick>10:
                    check_window(world,actors,before,streams);captured.append(tick)
                else:self.assertEqual(streams['local'],[])
                if tick>=10:boundaries.append(boundary(world))
            self.assertEqual(captured,list(range(11,31)))
            self.assertEqual([b['tick'] for b in boundaries],list(range(10,31)))
            self.assertEqual(sum(boundaries[-1]['food']),world.snapshot()['food_energy'])
            self.assertEqual(dict(boundaries[-1]['occupied']),world.occupied)
