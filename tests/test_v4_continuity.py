import unittest
from bitgenesis.v4.structure_continuity import follow


class ContinuityTests(unittest.TestCase):
    def row(self, series, parents, horizon=2):
        return follow(series, parents, 1, (horizon,))[horizon][0]

    def test_static_and_complete_multigeneration_replacement_are_distinct(self):
        static = self.row({1:[[0,1]],2:[[0,1]],3:[[0,1]]}, [None,None])
        self.assertTrue(static['continuous_closed_multi'])
        self.assertFalse(static['primary'])
        replaced = self.row({1:[[0,1]],2:[[2,3]],3:[[4,5]]}, [None,None,0,1,2,3])
        self.assertTrue(replaced['primary'])
        self.assertEqual(replaced['first_complete_replacement_tick'], 2)
        self.assertEqual(replaced['endpoint']['represented_anchor_members'], 2)
        self.assertEqual(replaced['endpoint']['new_descendants'], 2)

    def test_split_rejoin_mixing_extinction_and_singleton(self):
        rejoined = self.row({1:[[0,1]],2:[[0],[1]],3:[[0,1]]}, [None,None])
        self.assertFalse(rejoined['continuous_closed_multi'])
        self.assertTrue(rejoined['endpoint_closed_after_break'])
        self.assertEqual(rejoined['first_break_tick'], 2)
        self.assertEqual(rejoined['state_steps']['fragmented'], 1)
        mixed = self.row({1:[[0,1],[2]],2:[[0,1,2]],3:[[0,1,2]]}, [None]*3)
        self.assertEqual(mixed['endpoint']['state'], 'mixed')
        self.assertEqual(mixed['outsider_unit_steps']['mixed'], 2)
        gone = self.row({1:[[0,1]],2:[],3:[]}, [None,None])
        self.assertEqual(gone['endpoint']['state'], 'extinct')
        self.assertFalse(gone['complete_replacement'])
        single = self.row({1:[[0]],2:[[1]],3:[[2]]}, [None,0,1])
        self.assertFalse(single['primary'])
        self.assertEqual(single['endpoint']['state'], 'closed_singleton')

    def test_singleton_bottleneck_and_ancestral_takeover_remain_visible(self):
        bottleneck = self.row({1:[[0,1]],2:[[2]],3:[[2,3]]}, [None,None,0,2])
        self.assertTrue(bottleneck['complete_replacement'])
        self.assertFalse(bottleneck['primary'])
        self.assertEqual(bottleneck['state_steps']['closed_singleton'],1)
        self.assertTrue(bottleneck['endpoint_closed_after_break'])
        takeover = self.row({1:[[0,1]],2:[[2,3]],3:[[2,3]]}, [None,None,0,0])
        self.assertTrue(takeover['primary'])
        self.assertEqual(takeover['endpoint']['represented_anchor_members'],1)
        self.assertEqual(takeover['anchor_size'],2)

    def test_anchor_live_parent_and_child_are_separate_cut_roots(self):
        rows = follow({1:[[0],[1]],2:[[2],[3]]}, [None,0,0,1], 1, (1,))[1]
        self.assertEqual([r['endpoint']['descendants'] for r in rows], [1,1])
        self.assertEqual([r['endpoint']['destination_components'] for r in rows], [1,1])
        self.assertTrue(all(r['complete_replacement'] for r in rows))

    def test_unrelated_same_position_is_not_ancestry_and_malformed_inputs_fail(self):
        with self.assertRaises(ValueError):
            self.row({1:[[0,1]],2:[[2,3]],3:[[2,3]]}, [None]*4)
        with self.assertRaises(ValueError):
            self.row({1:[[0,1]],2:[[0],[0]],3:[[0,1]]}, [None,None])
        with self.assertRaises(ValueError):
            self.row({1:[[0,1]],3:[[0,1]]}, [None,None])
        with self.assertRaises(ValueError):
            self.row({1:[[0,1]],2:[[0,1]],3:[[0,1]]}, [1,0])
        self.assertEqual(follow({1:[],2:[]}, [], 1, (1,)), {1:[]})


class ContinuityAuditTests(unittest.TestCase):
    def test_short_trajectory_phase_identity_and_corruption(self):
        import json
        from copy import deepcopy
        from hashlib import sha256
        from pathlib import Path
        import tempfile
        from bitgenesis.v4.hereditary_runner import run
        from bitgenesis.v4.structure_trace import trace
        from bitgenesis.v4.lineage import trace as lineage
        from bitgenesis.v4.structure_continuity import analyze
        from bitgenesis.v4.continuity_audit import event_parents, check_panels
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/'engineering'
            run(root, 103000, 8, width=4, height=4, occupancy=500)
            before = {p.name:sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
            observed = trace(root)
            parents = [r['parent'] for r in lineage(root)['individuals']]
            self.assertEqual(event_parents(root, observed), parents)
            panels = analyze(observed, parents, anchors=(1,3), horizons=(1,3))
            checked = check_panels(observed, parents, panels, anchors=(1,3), horizons=(1,3))
            self.assertEqual(checked['panels'], 20)
            self.assertGreater(checked['component_windows'], 0)
            altered = deepcopy(panels)
            altered[0]['records'][0]['endpoint']['descendants'] += 1
            with self.assertRaises(ValueError):
                check_panels(observed, parents, altered, anchors=(1,3), horizons=(1,3))
            broken = deepcopy(observed)
            broken['observations'][0]['interaction_site_ids'] = broken['observations'][0]['final_site_ids'][::-1]
            with self.assertRaises(ValueError):
                event_parents(root, broken)
            self.assertEqual(before, {p.name:sha256(p.read_bytes()).hexdigest() for p in root.iterdir()})
