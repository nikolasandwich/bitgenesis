import copy
import unittest
from bitgenesis.v4.structure import partition, snapshot, continuity


class StructureTests(unittest.TestCase):
    def test_periodic_material_and_realized_boundaries_are_passive(self):
        units = [None] * 25
        ids = [None] * 25
        for site, identity, label in ((0, 10, 0), (4, 11, 0), (1, 12, 1), (12, 13, 0)):
            units[site] = dict(material=label, energy=0)
            ids[site] = identity
        before = copy.deepcopy((units, ids))
        # Empty realized graph represents an audited no-energy bond phase.
        result = snapshot(units, ids, 5, 5, phase='interaction', bonds=[])
        self.assertEqual(result['components'], dict(contact=[[10, 11, 12], [13]],
                         material=[[10, 11], [12], [13]], bond=[[10], [11], [12], [13]]))
        self.assertEqual([r['numerator'] for r in result['boundary_disagreement']], [3, 3, 2])
        self.assertEqual(before, (units, ids))
        # Supplied phase bonds remain valid with zero post-charge energy.
        bonded = snapshot(units, ids, 5, 5, phase='interaction', bonds=[[0, 4]])
        self.assertEqual(bonded['components']['bond'], [[10, 11], [12], [13]])
        with self.assertRaises(ValueError):
            snapshot(units, ids, 5, 5, phase='interaction', bonds=[[0, 1]])
        with self.assertRaises(ValueError):
            snapshot(units, ids, 5, 5, phase='final', bonds=[])
        with self.assertRaises(ValueError):
            snapshot(units, [None] * 25, 5, 5, phase='final')

    def test_empty_is_not_zero_uncertainty(self):
        result = snapshot([None] * 9, [None] * 9, 3, 3, phase='final')
        self.assertEqual(result['components'], dict(contact=[], material=[]))
        self.assertIsNone(result['boundary_disagreement'][0]['fraction'])
        self.assertIsNone(result['metrics']['contact']['singleton_fraction'])

    def test_split_merge_and_replacement_do_not_invent_group_parent(self):
        r = continuity([[1, 2, 3], [4, 5], [6]], [[1, 4], [2, 3], [7]])
        self.assertEqual(r['splits'], [0])
        self.assertEqual(r['merges'], [0])
        self.assertEqual(r['lost_members'], [5, 6])
        self.assertEqual(r['added_members'], [7])
        self.assertEqual(r['previous_without_overlap'], [2])
        self.assertEqual(r['current_without_overlap'], [2])
        self.assertEqual(sum(e['shared'] for e in r['overlaps']), 4)
        # Same site/program with a new birth ID supplies no surviving overlap.
        self.assertEqual(continuity([[6]], [[7]])['overlaps'], [])
        with self.assertRaises(ValueError):
            continuity([[1], [1]], [[1]])

    def test_partition_against_independent_union_find(self):
        import random
        rng = random.Random(102000)
        for _ in range(40):
            members = list(range(12))
            edges = [(a, b) for a in members for b in range(a + 1, 12) if rng.randrange(5) == 0]
            parents = list(members)
            def root(a):
                while parents[a] != a:
                    a = parents[a]
                return a
            for a, b in edges:
                parents[root(a)] = root(b)
            expected = {}
            for i in members:
                expected.setdefault(root(i), []).append(i)
            self.assertEqual(partition(members, edges), sorted(expected.values()))


if __name__ == '__main__':
    unittest.main()
