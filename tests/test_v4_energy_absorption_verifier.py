import unittest
from fractions import Fraction as F
from unittest.mock import patch
from scripts import verify_v4_energy_absorption as v


class VerifierTests(unittest.TestCase):
    def test_bareiss_integer_swap_and_singular(self):
        self.assertEqual(v.determinant([[0, 2], [3, 4]]), -6)
        self.assertEqual(v.determinant([[1, 2], [2, 4]]), 0)
        self.assertEqual(v.determinant([[2, 1, 3], [4, 3, 1], [6, 5, 2]]), 6)

    def test_cramer_rationals_and_singular(self):
        self.assertEqual(v.cramer([[2, 1], [1, -1]], [1, 0]), [F(1, 3), F(1, 3)])
        with self.assertRaises(ValueError):
            v.cramer([[1, 2], [2, 4]], [1, 2])

    def test_affine_recurrence_synthetic_seeds(self):
        seeds = list(range(1, 8))
        for forcing in (0, 64):
            forms = v.boundary_forms(forcing)
            values = [0] + seeds
            for energy in range(1, 16):
                values.append(64 * values[energy] - 63 * values[energy-1] - forcing)
            self.assertEqual(len(forms), 23)
            for energy, (coeff, constant) in enumerate(forms):
                self.assertEqual(sum(a*b for a, b in zip(coeff, seeds)) + constant, values[energy])

    def fixture(self):
        states = [dict(energy=e, hit='1/4', dead='3/4', mean_steps='1') for e in range(1, 16)]
        curve = [dict(horizon=t, alive=['1' if t == 0 and e == 5 else '0' for e in range(1, 16)],
                      hit='0' if t == 0 else '1/4', dead='0' if t == 0 else '3/4',
                      surviving='1' if t == 0 else '0') for t in range(33)]
        return states, dict(curve=curve, cohort=[{}] * 52)

    def test_mocked_build_all_33_points(self):
        states, prior = self.fixture()
        with patch.object(v, 'solve_states', return_value=states):
            records, summary = v.build(prior)
        self.assertEqual(len(records['finite_checks']), 33)
        self.assertEqual(summary, dict(initial_energy=5, eventual_hit='1/4', eventual_dead='3/4',
                                     mean_absorption_steps='1', at_32_hit='1/4', additional_hit_after_32='0',
                                     remaining_mean_steps_after_32='0', at_32_surviving='0'))
        self.assertTrue(all(r['hit_reconstructed'] == '1/4' and r['mean_steps_reconstructed'] == '1'
                            for r in records['finite_checks']))

    def test_build_rejects_inconsistent_horizon_and_mass(self):
        for change in ('horizon', 'mass', 'hit', 'canonical'):
            states, prior = self.fixture()
            if change == 'horizon': prior['curve'][4]['horizon'] = 3
            if change == 'mass': prior['curve'][0]['surviving'] = '1/2'
            if change == 'hit': prior['curve'][5]['hit'] = '1/2'
            if change == 'canonical': prior['curve'][0]['hit'] = '0/2'
            with patch.object(v, 'solve_states', return_value=states), self.assertRaises(ValueError):
                v.build(prior)

    def test_bellman_rejects_synthetic_invalid_states(self):
        states, _ = self.fixture()
        with self.assertRaises(ValueError): v.validate_states(states)

    def test_mocked_main_binds_515_and_preserves_failure(self):
        import tempfile
        from pathlib import Path
        from scripts import energy_absorption_inputs as io
        original_digest = io.digest
        for tamper in (False, True):
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                bound = {f'fixture/{i}': 'a'*64 for i in range(514)}
                bound['scripts/verify_v4_energy_absorption.py'] = original_digest(Path(v.__file__))
                bound = dict(sorted(bound.items()))
                states, prior = self.fixture()
                with patch.object(v, 'solve_states', return_value=states):
                    records, summary = v.build(prior)
                io.save(root / 'records.json', records)
                io.save(root / 'summary.json', summary)
                meta = dict(status='complete', planned_states=15, completed_states=15,
                            finite_horizons=33, initial_energy=5, new_full_world_steps=0,
                            new_phase_transitions=0, new_environment_sources=0, new_independent_initial_worlds=0,
                            time_limit_seconds=60, storage_limit_bytes=8388608, git_commit='a'*40,
                            elapsed_seconds=0.1, input_paths=list(bound), input_sha256=bound,
                            input_sha256_after=bound,
                            output_sha256={n: original_digest(root/n) for n in ('records.json', 'summary.json')})
                if tamper: meta['completed_states'] = 14
                io.save(root / 'metadata.json', meta)
                def digest(path):
                    return bound[str(path)] if str(path) in bound else original_digest(path)
                with patch.object(v, 'OUTPUT', root), patch.object(v, 'build', return_value=(records, summary)), \
                     patch.object(io, 'bindings', return_value=bound), patch.object(io, 'input_paths', return_value=list(bound)), \
                     patch.object(io, 'digest', side_effect=digest), patch.object(io, 'read', side_effect=lambda p: prior if str(p) == 'data/v4-study-031/records.json' else __import__('json').loads(Path(p).read_text())):
                    if tamper:
                        with self.assertRaises(ValueError): v.main()
                        evidence = io.read(root/'verification-failure.json')
                        self.assertEqual(evidence['status'], 'failed')
                        self.assertEqual(len(evidence['input_sha256']), 515)
                    else:
                        v.main()
                        proof = io.read(root/'independent-verification.json')
                        self.assertEqual(proof['input_files'], 515)
                        self.assertEqual(proof['completed_states'], 15)
                        self.assertEqual(proof['finite_horizons'], 33)
                        self.assertEqual(proof['files_sha256'], {n: original_digest(root/n) for n in ('metadata.json', 'records.json', 'summary.json')})
                        with self.assertRaises(ValueError): v.main()
