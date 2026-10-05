"""Short-horizon exact checks; no formal full-curve engineering run."""
from copy import deepcopy
from fractions import Fraction as F
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import verify_v4_energy_probability as v


class EnergyProbabilityVerifierTests(unittest.TestCase):
    def test_closed_forms_and_mass(self):
        rows = v.curve(5)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]['alive'], ['0'] * 4 + ['1'] + ['0'] * 10)
        self.assertEqual(rows[1]['alive'][3], '63/64')
        self.assertEqual(rows[1]['alive'][11], '1/64')
        self.assertEqual(F(rows[2]['hit']), F(1, 64**2))
        self.assertEqual(F(rows[3]['first_hit']), F(2*63, 64**3))
        self.assertEqual(F(rows[5]['dead']), F(63, 64)**5)
        previous_hit = previous_dead = F(0)
        for row in rows:
            self.assertEqual(set(row), {'horizon', 'alive', 'first_hit', 'first_death', 'hit', 'dead', 'surviving'})
            alive = sum(map(F, row['alive']))
            hit, dead = F(row['hit']), F(row['dead'])
            self.assertEqual(F(row['surviving']), alive)
            self.assertEqual(hit + dead + alive, 1)
            self.assertEqual(F(row['first_hit']), hit-previous_hit)
            self.assertEqual(F(row['first_death']), dead-previous_dead)
            for value in row['alive'] + [row[k] for k in ('first_hit', 'first_death', 'hit', 'dead', 'surviving')]:
                self.assertIs(type(value), str)
                self.assertEqual(str(F(value)), value)
                self.assertGreaterEqual(F(value), 0)
            previous_hit, previous_dead = hit, dead

    def test_death_and_hit_absorb_before_future_tickets(self):
        for steps in (0, 1, 5):
            self.assertEqual(v.terminal_probability(steps, 0, 'dead'), 1)
            self.assertEqual(v.terminal_probability(steps, 0, 'hit'), 0)
            self.assertEqual(v.terminal_probability(steps, 0, 7), 0)
            self.assertEqual(v.terminal_probability(steps, 16, 'hit'), 1)
            self.assertEqual(v.terminal_probability(steps, 22, 'dead'), 0)
        self.assertEqual(v.terminal_probability(1, 1, 'dead'), F(63, 64))
        self.assertEqual(v.terminal_probability(1, 9, 'hit'), F(1, 64))

    def test_horizon_types_and_boundaries(self):
        for bad in (-1, 33, True, 2.0, '2', None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                v.curve(bad)

    def test_cohort_mapping_and_linear_expectation_with_mock_curve(self):
        timing = json.loads(Path('docs/research/results/v4-study-030-records.json').read_text())
        original = deepcopy(timing)
        fake = [dict(horizon=h, hit=str(F(h, 64)), dead='1/4', surviving=str(F(48-h, 64))) for h in range(33)]
        with patch.object(v, 'curve', return_value=fake) as called:
            records, summary = v.build(timing)
            called.assert_called_once_with()
        self.assertEqual(timing, original)
        self.assertEqual(records['curve'], fake)
        self.assertEqual([r['selection'] for r in records['cohort']], [r['selection'] for r in timing])
        self.assertEqual([r['horizon'] for r in records['cohort']], [32-r['birth_tick'] for r in timing])
        self.assertEqual([r['n'] for r in summary], [21, 5, 21, 5])
        for cell in summary:
            group = [r for r in records['cohort'] if r['selection']['genotype'] == cell['genotype'] and r['selection']['exchange'] == cell['exchange']]
            expected = sum(F(r['horizon'], 64) for r in group)
            self.assertEqual(F(cell['expected_hits']), expected)
            self.assertEqual(F(cell['mean_hit']), expected/len(group))
            self.assertEqual(sum(F(cell['mean_'+k]) for k in ('hit', 'dead', 'surviving')), 1)
        for change in ('missing', 'duplicate', 'birth', 'bool', 'extra'):
            bad = deepcopy(timing)
            if change == 'missing': bad.pop()
            elif change == 'duplicate': bad[-1] = deepcopy(bad[-2])
            elif change == 'birth': bad[0]['birth_tick'] += 1
            elif change == 'bool': bad[0]['birth_tick'] = True
            else: bad[0]['selection']['extra'] = 1
            with self.subTest(change=change), patch.object(v, 'curve', return_value=fake), self.assertRaises(ValueError):
                v.build(bad)

    def test_budget_and_proof_exclusivity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with patch.object(v, 'monotonic', return_value=60), self.assertRaises(ValueError):
                v.check_budget(root, 0)
            with patch.object(v, 'monotonic', return_value=0), self.assertRaises(ValueError):
                v.check_budget(root, 0, 8388608)
            proof = root / 'independent-verification.json'
            proof.write_text('preserve')
            with patch.object(v, 'OUTPUT', root), self.assertRaises(ValueError):
                v.main()
            self.assertEqual(proof.read_text(), 'preserve')

    def test_failure_retains_initial_inventory_and_changed_hashes(self):
        from scripts import energy_probability_inputs as inputs
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source, missing = root / 'source.json', root / 'missing.json'
            source.write_text('before')
            for name in ('metadata.json', 'records.json', 'summary.json'):
                (root / name).write_text('{}')
            original = inputs.digest(source)
            def broken():
                source.write_text('after')
                raise ValueError('broken binding')
            with patch.object(v, 'OUTPUT', root), patch.object(inputs, 'input_paths', return_value=[str(source), str(missing)]), patch.object(inputs, 'bindings', side_effect=broken):
                with self.assertRaisesRegex(ValueError, 'broken binding'):
                    v.main()
            failure = json.loads((root / 'verification-failure.json').read_text())
            self.assertEqual(failure['input_sha256'][str(source)], original)
            self.assertEqual(failure['input_sha256_after'][str(source)], inputs.digest(source))
            self.assertEqual(failure['completed_horizons'], 0)
            self.assertIn(str(missing), failure['read_errors_before'])
            self.assertIn(str(missing), failure['read_errors_after'])
            self.assertEqual(set(failure['files_sha256_before']), {'metadata.json', 'records.json', 'summary.json'})
            self.assertEqual(failure['files_sha256_before'], failure['files_sha256_after'])
            self.assertFalse((root / 'independent-verification.json').exists())

    def test_comparison_rejects_noncanonical_and_type_corruptions(self):
        original = v.curve(2)
        for target in ('float', 'bool', 'fraction', 'distribution', 'first', 'extra'):
            changed = deepcopy(original)
            if target == 'float': changed[0]['hit'] = 0.0
            elif target == 'bool': changed[0]['horizon'] = False
            elif target == 'fraction': changed[0]['dead'] = '0/1'
            elif target == 'distribution': changed[1]['alive'][11] = '0'
            elif target == 'first': changed[2]['first_hit'] = '0'
            else: changed[0]['extra'] = '0'
            with self.subTest(target=target), self.assertRaises(ValueError):
                v.same(changed, original, 'exact protocol output')
