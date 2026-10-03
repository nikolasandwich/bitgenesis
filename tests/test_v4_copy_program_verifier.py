import copy
import unittest

from scripts import verify_v4_copy_program as verifier


class ProbeVerifierTests(unittest.TestCase):
    def fixture(self, source_id=5):
        units = [None] * 256
        ids = [None] * 256
        units[117] = dict(material=0, energy=31, program=[0, 0, 0, source_id - 4])
        ids[117] = source_id
        case = dict(name='constructed-off', final=dict(units=units, site_ids=ids))
        initial = dict(units=[None] * 256, raw=[0] * 256)
        initial['units'][85] = dict(material=0, energy=64, program=units[117]['program'].copy())
        initial['raw'][69] = 1
        tape = dict(tick=1, directions=[3] * 256, mutation_tickets=[[999, 0, 1] for _ in range(256)],
                    driven=dict(inputs=[dict(proposed=0) for _ in range(256)]))
        from bitgenesis.v4.exchange_branch_audit import physical_step
        physical = physical_step(initial['units'], initial['raw'], verifier.CONFIG, tape, False)
        return case, dict(source_id=source_id, status='complete', source=dict(site=117, **units[117]),
                          initial=initial, physical=physical)

    def test_actual_distinct_materials(self):
        for identity in (5, 6):
            case, probe = self.fixture(identity)
            self.assertEqual(verifier.verify_probe(probe, case),
                             dict(source_id=identity, status='complete', formed_materials=[identity - 4]))

    def test_unavailable_preserves_fixed_identity(self):
        case = dict(name='constructed-off', final=dict(site_ids=[None] * 256, units=[None] * 256))
        probe = dict(source_id=5, status='unavailable', source=None, initial=None, physical=None)
        self.assertEqual(verifier.verify_probe(probe, case)['formed_materials'], [])
        probe['source_id'] = 7
        with self.assertRaises(ValueError):
            verifier.verify_probe(probe, case)

    def test_source_program_direction_and_ledger_tampering(self):
        for field in ('source', 'program', 'direction', 'material'):
            case, probe = self.fixture()
            if field == 'source':
                probe['source']['site'] = 118
            elif field == 'program':
                probe['initial']['units'][85]['program'][3] = 2
            elif field == 'direction':
                probe['physical']['directions'][85] = 0
            else:
                probe['physical']['units'][69]['material'] = 2
            with self.subTest(field=field), self.assertRaises(ValueError):
                verifier.verify_probe(probe, case)


class CaseVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Invoke the public producer as a black box; the verifier imports no producer logic.
        from scripts.run_v4_copy_program import run_case, run_probe, summarize
        from scripts.run_v4_copy_control import run_case as old_run_case
        cls.cases = [run_case(name) for name in verifier.NAMES]
        cls.probes = [run_probe(cls.cases[0], identity) for identity in (5, 6)]
        cls.old_cases = [old_run_case(name) for name in verifier.NAMES]
        cls.summary = summarize(cls.cases, cls.probes, cls.old_cases)

    def setUp(self):
        from unittest.mock import patch
        real_read = verifier.read
        def read(path):
            return self.old_cases if str(path) == 'data/v4-copy-control/cases.json' else real_read(path)
        patcher = patch.object(verifier, 'read', side_effect=read)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_full_queue_and_independent_aggregate(self):
        summary = verifier.aggregate(self.cases, self.probes, self.old_cases)
        self.assertEqual(summary, self.summary)
        self.assertTrue(summary['cases'][0]['persistent10'])
        self.assertFalse(summary['cases'][1]['persistent10'])
        self.assertEqual(summary['cases'][2]['births'], 0)
        self.assertEqual([p['formed_materials'] for p in summary['probes']], [[1], [2]])
        self.assertEqual(summary['formation_directions'][0]['counts'], [0, 0, 4, 0])
        self.assertEqual(summary['formed_programs'][0]['counts'],
                         [dict(program=[0, 0, 0, 1], count=2), dict(program=[0, 0, 0, 2], count=2)])

    def test_initial_program_and_saved_direction_tamper(self):
        for where in ('initial', 'direction', 'ancestry', 'summary'):
            case = copy.deepcopy(self.cases[0])
            if where == 'initial':
                case['initial']['units'][85]['program'][3] = 2
            elif where == 'direction':
                case['rows'][0]['physical']['directions'][85] = 3
            elif where == 'ancestry':
                case['final']['parents'][5] = 1
            else:
                case['summary']['persistent10'] = False
            with self.subTest(where=where), self.assertRaises(ValueError):
                verifier.verify_case(case)

    def test_physical_comparison_keeps_actual_energy_and_material(self):
        old = copy.deepcopy(self.old_cases)
        old[0]['initial']['units'][85]['energy'] -= 1
        summary = verifier.aggregate(self.cases, self.probes, old)
        self.assertFalse(summary['physical_equivalence'][0]['equal'])
        self.assertFalse(summary['expectations_met'])
        self.assertEqual(len(summary['cases']), 3)
        self.assertEqual(len(summary['probes']), 2)

    def write_run(self, root, summary=None):
        import json
        summary = self.summary if summary is None else summary
        values = {'cases.json': self.cases, 'probes.json': self.probes, 'summary.json': summary}
        for name, value in values.items():
            (root / name).write_text(json.dumps(value))
        bound = {str(i): str(i) for i in range(214)}
        bound['scripts/verify_v4_copy_program.py'] = verifier.digest(verifier.__file__)
        metadata = dict(status='complete', planned_cases=3, completed_cases=3, planned_probes=2,
                        completed_probes=2, new_simulation_steps=98, new_independent_sources=0,
                        artificial_control=True, git_commit='a' * 40, time_limit_seconds=300,
                        storage_limit_bytes=33554432, elapsed_seconds=1, input_sha256=bound,
                        input_sha256_after=bound, expectations_met=summary['expectations_met'],
                        output_sha256={name: verifier.digest(root / name) for name in values})
        (root / 'metadata.json').write_text(json.dumps(metadata))
        return bound

    def test_complete_proof_and_exclusive_rerun(self):
        import contextlib
        import io
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bound = self.write_run(root)
            with patch.object(verifier, 'OUTPUT', root), patch.object(verifier, 'bindings', return_value=bound), contextlib.redirect_stdout(io.StringIO()):
                verifier.main()
                proof = (root / 'independent-verification.json').read_bytes()
                self.assertEqual(json.loads(proof)['saved_steps'], 98)
                with self.assertRaises(FileExistsError):
                    verifier.main()
                self.assertEqual((root / 'independent-verification.json').read_bytes(), proof)

    def test_invalid_summary_retains_failure_and_original_files(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tampered = copy.deepcopy(self.summary)
            tampered['formation_directions'][0]['counts'] = [0, 0, 3, 1]
            bound = self.write_run(root, tampered)
            original = (root / 'summary.json').read_bytes()
            with patch.object(verifier, 'OUTPUT', root), patch.object(verifier, 'bindings', return_value=bound):
                with self.assertRaisesRegex(ValueError, 'aggregate'):
                    verifier.main()
            self.assertTrue((root / 'verification-failure.json').exists())
            self.assertFalse((root / 'independent-verification.json').exists())
            self.assertEqual((root / 'summary.json').read_bytes(), original)

    def test_unmet_expectations_still_verify_complete_queue(self):
        import contextlib
        import io
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        old = copy.deepcopy(self.old_cases)
        old[0]['final']['units'][85]['energy'] -= 1
        summary = verifier.aggregate(self.cases, self.probes, old)
        self.assertFalse(summary['expectations_met'])
        real_read = verifier.read
        def read(path):
            return old if str(path) == 'data/v4-copy-control/cases.json' else real_read(path)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bound = self.write_run(root, summary)
            with patch.object(verifier, 'OUTPUT', root), patch.object(verifier, 'bindings', return_value=bound), patch.object(verifier, 'read', side_effect=read), contextlib.redirect_stdout(io.StringIO()):
                verifier.main()
            proof = json.loads((root / 'independent-verification.json').read_text())
            self.assertEqual(proof['status'], 'verified')
            self.assertFalse(proof['expectations_met'])
            self.assertEqual(proof['cases'], 3)
            self.assertEqual(proof['probes'], 2)

    def test_running_verifier_must_match_bound_code(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bound = self.write_run(root)
            bound['scripts/verify_v4_copy_program.py'] = '0' * 64
            metadata = json.loads((root / 'metadata.json').read_text())
            metadata['input_sha256'] = metadata['input_sha256_after'] = bound
            (root / 'metadata.json').write_text(json.dumps(metadata))
            with patch.object(verifier, 'OUTPUT', root), patch.object(verifier, 'bindings', return_value=bound):
                with self.assertRaisesRegex(ValueError, 'running verifier binding'):
                    verifier.main()
            self.assertTrue((root / 'verification-failure.json').exists())
            self.assertFalse((root / 'independent-verification.json').exists())
