from copy import deepcopy
import unittest
from scripts.summarize_v0_common_environment_checkpoints import (
    ARMS, CHECKPOINTS, FIELDS, group_observations,
)


class CommonCheckpointTests(unittest.TestCase):
    def test_source_arm_separation_and_extinct_nulls(self):
        rows = []
        for source in (1900, 1901):
            for arm in ARMS:
                for replicate in range(5):
                    for tick in CHECKPOINTS:
                        alive = source == 1900 and arm == 'sampled' and replicate < 2
                        row = dict.fromkeys(FIELDS, 0)
                        row.update(source_seed=source, arm=arm, replicate=replicate,
                                   tick=tick, population=10 if alive else 0,
                                   mean_genome=256 if alive else None,
                                   max_generation=3 if alive else None)
                        rows.append(row)
        original = deepcopy(rows)
        groups = group_observations(rows, {1900, 1901})
        self.assertEqual(len(groups), 24)
        for group in groups:
            mixed = group['source_seed'] == 1900 and group['arm'] == 'sampled'
            self.assertEqual(group['worlds'], 5)
            self.assertEqual(group['alive'], 2 if mixed else 0)
            self.assertEqual(group['ranges']['population'], [0, 10] if mixed else [0, 0])
            self.assertEqual(group['null_mean_worlds'], 3 if mixed else 5)
            self.assertEqual(group['null_generation_worlds'], 3 if mixed else 5)
        self.assertEqual(rows, original)
        for broken in (rows[:-1], rows + [rows[0]], rows[:-1] + [rows[0]]):
            with self.assertRaises(ValueError):
                group_observations(broken, {1900, 1901})
        self.assertEqual(group_observations([], set()), [])


if __name__ == '__main__':
    unittest.main()
