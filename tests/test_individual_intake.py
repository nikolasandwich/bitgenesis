import unittest
from scripts.analyze_v0_individual_intake import individuals, cohort


class IndividualIntakeTests(unittest.TestCase):
    def test_terminal_only_founder_and_horizon_birth_are_retained(self):
        people = individuals([dict(tick=1, id=0, eaten=8, child_id=2)],
                             [dict(tick=1, id=1)], founders=2, horizon=1)
        self.assertEqual([p['food_eaten'] for p in people], [8, 0, 0])
        self.assertEqual([p['action_ticks'] for p in people], [1, 1, 0])
        self.assertEqual(people[1]['death_tick'], 1)
        self.assertIsNone(people[2]['death_tick'])
        self.assertEqual(cohort(people)['zero_intake_individuals'], 2)
        self.assertEqual(cohort(people)['zero_action_individuals'], 1)

    def test_missing_actor_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'partitioned'):
            individuals([], [], founders=1, horizon=1)

    def test_empty_and_zero_intake_cohorts_have_no_concentration(self):
        self.assertIsNone(cohort([])['top_intake_share'])
        people = individuals([], [dict(tick=1, id=0)], founders=1, horizon=1)
        self.assertIsNone(cohort(people)['top_intake_share'])
