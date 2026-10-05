"""Small archived fixtures and adversarial timing verification."""
from copy import deepcopy
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from scripts import verify_v4_feed_timing as v


def fixture():
    with tarfile.open('docs/research/results/v4-study-028-cases.tar.gz') as archive:
        branch = json.load(archive.extractfile('cases/branch-000.json'))
    energy = json.loads(Path('docs/research/results/v4-study-029-records.json').read_text())[0]
    return branch, energy


class FeedTimingVerifierTests(unittest.TestCase):
    def test_archived_full_window_and_energy_binding(self):
        branch, energy = fixture()
        original = deepcopy(branch)
        steps = []
        record = v.recount(branch, energy, on_step=lambda: steps.append(1))
        self.assertEqual(branch, original)
        self.assertEqual(len(steps), 17)
        self.assertEqual(record['totals']['steps'], 17)
        self.assertEqual(record['totals']['child_accepted'], energy['totals']['accepted'])
        self.assertEqual([r['tick'] for r in record['rows']], list(range(16, 33)))
        for target in ('energy', 'physical', 'identity'):
            b, e = deepcopy(branch), deepcopy(energy)
            if target == 'energy': e['totals']['accepted'] += 1
            elif target == 'physical': b['rows'][-1]['physical']['spent'] += 1
            else: b['rows'][-1]['site_ids'][101] = 7
            with self.subTest(target=target), self.assertRaises(ValueError): v.recount(b, e)

    def test_existing_proof_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            proof = root / 'independent-verification.json'
            proof.write_text('existing')
            with patch.object(v, 'OUTPUT', root), self.assertRaises(ValueError): v.main()
            self.assertEqual(proof.read_text(), 'existing')

    def test_budget(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(v, 'monotonic', return_value=300), self.assertRaises(ValueError):
                v.check_budget(Path(d), 0)
            with patch.object(v, 'monotonic', return_value=1), self.assertRaises(ValueError):
                v.check_budget(Path(d), 0, 33554432)

    @staticmethod
    def timing_record(genotype='homogeneous', exchange=False, site=0, death=30):
        rows = []
        for tick in (30, 31, 32):
            before = 1 if tick <= death else (None if tick == death + 1 else 2)
            after = 1 if tick < death else (None if tick == death else 2)
            accepted = 0 if before is None else 8
            rows.append(dict(tick=tick, phase=v.phase(tick, death), identity_before=before,
                identity_after=after, proposed=8, site_accepted=accepted,
                child_accepted=accepted if before == 1 else 0,
                other_accepted=accepted if before != 1 else 0, rejected=8-accepted))
        return dict(selection=dict(genotype=genotype, mode='random-both', seed=120000,
            exchange=exchange, tick=29, site=site, identity=0, root=0, energy_before=5),
            child_identity=1, child_site=100, birth_tick=29, death_tick=death,
            rows=rows, totals=v.totals(rows), first_proposed_tick=30,
            first_proposed_phase=v.phase(30, death), first_after_death_tick=death+1 if death < 32 else None)

    def test_death_empty_site_replacement_and_thirteen_totals(self):
        record = self.timing_record()
        v.validate_record(record)
        self.assertEqual(record['totals'], dict(steps=3, proposal_events=3,
            before_death_events=0, death_events=1, after_death_events=2,
            proposed=24, before_death_proposed=0, death_proposed=8,
            after_death_proposed=16, site_accepted=16, child_accepted=8,
            other_accepted=8, rejected=8))
        for target in ('empty', 'resurrection', 'bool', 'extra', 'first', 'missing'):
            changed = deepcopy(record)
            if target == 'empty': changed['rows'][1]['site_accepted'] = 8
            elif target == 'resurrection': changed['rows'][2]['identity_before'] = 1
            elif target == 'bool': changed['totals']['before_death_events'] = False
            elif target == 'extra': changed['rows'][0]['extra'] = 0
            elif target == 'first': changed['first_after_death_tick'] = 32
            else: changed['rows'].pop()
            with self.subTest(target=target), self.assertRaises(ValueError): v.validate_record(changed)

    def test_pairs_exact_tickets_site_and_phase_shifts(self):
        records = [self.timing_record(g, e, s, 30 if g == 'homogeneous' else 32)
                   for g in v.GENOTYPES for e, count in ((False, 21), (True, 5)) for s in range(count)]
        result = v.aggregate(records)
        self.assertEqual([c['n'] for c in result['cells']], [21, 5, 21, 5])
        self.assertEqual(len(result['pairs']), 26)
        self.assertEqual(result['pairs'][0]['phase_shift_ticks'], [30, 31, 32])
        self.assertEqual(result['pairs'][0]['delta']['proposed'], 0)
        self.assertEqual(result['pairs'][0]['delta']['other_accepted'], -8)
        for target in ('site', 'duplicate', 'missing', 'tickets'):
            changed = deepcopy(records)
            if target == 'site': changed[26]['child_site'] += 1
            elif target == 'duplicate': changed[-1] = deepcopy(changed[-2])
            elif target == 'missing': changed.pop()
            else:
                r = changed[26]
                for k in ('proposed', 'site_accepted', 'child_accepted'): r['rows'][-1][k] = 0
                r['totals'] = v.totals(r['rows'])
            with self.subTest(target=target), self.assertRaises(ValueError): v.aggregate(changed)

    def test_initial_inventory_and_failure_hash_evidence(self):
        from scripts import feed_timing_inputs as inputs
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source, missing = root / 'input.json', root / 'missing.json'
            source.write_text('before')
            for name in ('metadata.json', 'records.json', 'summary.json'): (root / name).write_text('{}')
            original = inputs.digest(source)
            def broken():
                source.write_text('after')
                raise ValueError('binding broken')
            with patch.object(v, 'OUTPUT', root), patch.object(inputs, 'input_paths', return_value=[str(source), str(missing)]), patch.object(inputs, 'bindings', side_effect=broken):
                with self.assertRaisesRegex(ValueError, 'binding broken'): v.main()
            failure = json.loads((root / 'verification-failure.json').read_text())
            self.assertEqual(failure['input_sha256'][str(source)], original)
            self.assertEqual(failure['input_sha256_after'][str(source)], inputs.digest(source))
            self.assertIn(str(missing), failure['read_errors_before'])
            self.assertIn(str(missing), failure['read_errors_after'])
            self.assertEqual(failure['completed_branches'], 0)
            self.assertFalse((root / 'independent-verification.json').exists())

    def test_no_proposal_uses_null_first_fields(self):
        record = self.timing_record()
        for row in record['rows']:
            for key in ('proposed', 'site_accepted', 'child_accepted', 'other_accepted', 'rejected'):
                row[key] = 0
        record['totals'] = v.totals(record['rows'])
        record.update(first_proposed_tick=None, first_proposed_phase=None, first_after_death_tick=None)
        v.validate_record(record)
        self.assertEqual(record['totals']['proposal_events'], 0)
        record['first_proposed_tick'] = 0
        with self.assertRaises(ValueError):
            v.validate_record(record)
