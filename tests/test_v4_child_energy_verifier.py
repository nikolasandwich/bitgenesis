"""Independent verifier counterexamples use only a small archived fixture."""
from copy import deepcopy
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from scripts import verify_v4_child_energy as verifier


def fixture():
    with tarfile.open('docs/research/results/v4-study-028-cases.tar.gz') as archive:
        return json.load(archive.extractfile('cases/branch-000.json'))


class ChildEnergyVerifierTests(unittest.TestCase):
    def synthetic_records(self):
        records = []
        for genotype, durations in (
                ('homogeneous', ([4] + [3] * 20, [6] + [5] * 4)),
                ('heterogeneous', ([9] + [6] * 20, [9] + [10] * 4))):
            for exchange, lengths in zip((False, True), durations):
                for site, length in enumerate(lengths):
                    rows, energy = [], 5
                    for offset in range(length):
                        final = offset == length - 1
                        accepted = int(energy == 1 and not final)
                        bonds = energy - 1 if final else 0
                        after = energy + accepted - 1 - bonds
                        rows.append(dict(tick=offset + 2, energy_before=energy,
                            proposed=accepted, accepted=accepted, leakage=1, bond_cost=bonds,
                            exchange_in=0, exchange_out=0, energy_interaction=after,
                            formation_spent=0, offspring_energy=0, energy_after=after, dissolved=final))
                        energy = after
                    selection = dict(genotype=genotype, mode='random-both', seed=120000,
                        exchange=exchange, tick=1, site=site, identity=0, root=0, energy_before=1)
                    record = dict(selection=selection, child_identity=1, child_site=100,
                        birth_tick=1, death_tick=1+length, initial_energy=5, rows=rows,
                        totals=verifier.totals(rows))
                    records.append(record)
        return records

    def test_aggregate_full_shape_zero_rows_and_paired_deltas(self):
        records = self.synthetic_records()
        result = verifier.aggregate(records)
        self.assertEqual([c['totals']['steps'] for c in result['cells']], [64, 26, 129, 49])
        self.assertEqual(result['cells'][0]['zero_accepted'], 21)
        self.assertEqual(len(result['pairs']), 26)
        self.assertEqual(result['pairs'][0]['heterogeneous_index'], 26)
        self.assertEqual(result['pairs'][0]['delta']['steps'], 5)
        for mutation in ('duplicate', 'missing_pair', 'extra_row_key', 'bool_total', 'truncated'):
            changed = deepcopy(records)
            if mutation == 'duplicate':
                changed[-1] = deepcopy(changed[-2])
            elif mutation == 'missing_pair':
                changed[-1]['selection']['identity'] = 22
            elif mutation == 'extra_row_key':
                changed[0]['rows'][0]['extra'] = 0
            elif mutation == 'bool_total':
                changed[0]['totals']['final_energy'] = False
            else:
                changed.pop()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                verifier.aggregate(changed)

    def test_main_failure_preserves_actual_input_hashes_and_read_errors(self):
        from scripts import child_energy_inputs as inputs
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.json'
            source.write_text('before')
            missing = root / 'missing.json'
            for name in ('metadata.json', 'records.json', 'summary.json'):
                (root / name).write_text('{}')
            before = inputs.digest(source)
            def broken_bindings():
                source.write_text('after')
                raise ValueError('binding damaged')
            with patch.object(verifier, 'OUTPUT', root), \
                 patch.object(inputs, 'input_paths', return_value=[str(source), str(missing)]), \
                 patch.object(inputs, 'bindings', side_effect=broken_bindings):
                with self.assertRaisesRegex(ValueError, 'binding damaged'):
                    verifier.main()
            failure = json.loads((root / 'verification-failure.json').read_text())
            self.assertEqual(failure['input_sha256'][str(source)], before)
            self.assertEqual(failure['input_sha256_after'][str(source)], inputs.digest(source))
            self.assertIn(str(missing), failure['read_errors_before'])
            self.assertIn(str(missing), failure['read_errors_after'])
            self.assertFalse((root / 'independent-verification.json').exists())

    def test_budget_checks_actual_files_and_pending_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'record').write_bytes(b'123')
            with patch.object(verifier, 'monotonic', return_value=300):
                with self.assertRaisesRegex(ValueError, 'time budget'):
                    verifier.check_budget(root, 0)
            with patch.object(verifier, 'monotonic', return_value=1):
                verifier.check_budget(root, 0)
                with self.assertRaisesRegex(ValueError, 'storage budget'):
                    verifier.check_budget(root, 0, 33554430)
                with (root / 'large').open('wb') as stream:
                    stream.truncate(33554432)
                with self.assertRaisesRegex(ValueError, 'storage budget'):
                    verifier.check_budget(root, 0)

    def test_selected_parent_and_founder_are_bound(self):
        for mutation in ('identity', 'root', 'parent'):
            branch = fixture()
            if mutation == 'parent':
                branch['initial']['parents'][7] = 1
            else:
                branch['selection'][mutation] += 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                verifier.recount(branch)

    def test_existing_proof_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proof = root / 'independent-verification.json'
            proof.write_text('existing proof')
            with patch.object(verifier, 'OUTPUT', root), self.assertRaisesRegex(ValueError, 'already exists'):
                verifier.main()
            self.assertEqual(proof.read_text(), 'existing proof')
            self.assertFalse((root / 'verification-failure.json').exists())

    def test_entire_saved_continuation_replayed_after_child_death(self):
        branch = fixture()
        steps = []
        original = deepcopy(branch)
        result = verifier.recount(branch, on_step=lambda: steps.append(1))
        self.assertEqual(len(steps), 17)
        self.assertEqual(branch, original)
        self.assertEqual((result['child_identity'], result['child_site']), (7, 101))
        self.assertEqual((result['birth_tick'], result['death_tick']), (15, 18))
        self.assertEqual([r['tick'] for r in result['rows']], [16, 17, 18])
        self.assertEqual(result['totals']['final_energy'], 0)
        branch['rows'][-1]['physical']['spent'] += 1
        with self.assertRaises(ValueError):
            verifier.recount(branch)

    def test_saved_identities_and_parents_are_independently_checked(self):
        for target in ('identity', 'parent'):
            branch = fixture()
            if target == 'identity':
                branch['rows'][0]['site_ids'][101] = 200
            else:
                branch['final']['parents'][7] = None
            with self.assertRaises(ValueError):
                verifier.recount(branch)

    def test_cost_and_offspring_are_distinct_and_only_actual_bonds_count(self):
        physical = dict(tick=1, driven=dict(inputs=[dict(proposed=2, accepted=2, leakage=1)],
            interaction=dict(bonds=[], transfers=[])),
            interaction_units=[dict(energy=20)], units=[dict(energy=8)],
            material=dict(dissolved=[], proposals=[dict(source=0, target=1, reason='formed',
                construction_cost=4, copy_cost=1, child_energy=7)]))
        row = verifier.extract_row([dict(energy=19)], physical, 0, False)
        self.assertEqual(row['formation_spent'], 5)
        self.assertEqual(row['offspring_energy'], 7)
        self.assertEqual(row['bond_cost'], 0)
        self.assertEqual(row['energy_after'], 8)

    def test_actual_incident_bonds_and_directed_transfers(self):
        physical = dict(tick=1, driven=dict(inputs=[dict(proposed=3, accepted=3, leakage=1)],
            interaction=dict(bonds=[[0, 1], [2, 0], [3, 4]], transfers=[
                dict(donor=1, recipient=0, amount=4), dict(donor=0, recipient=2, amount=1),
                dict(donor=3, recipient=4, amount=9)])),
            interaction_units=[dict(energy=23)], units=[dict(energy=23)],
            material=dict(dissolved=[], proposals=[]))
        row = verifier.extract_row([dict(energy=20)], physical, 0, False)
        self.assertEqual((row['bond_cost'], row['exchange_in'], row['exchange_out']), (2, 4, 1))
        self.assertEqual(row['energy_interaction'], 23)

    def test_same_site_replacement_is_not_original_child(self):
        physical = dict(tick=1, driven=dict(inputs=[dict(proposed=0, accepted=0, leakage=1)],
            interaction=dict(bonds=[], transfers=[])), interaction_units=[dict(energy=0)],
            units=[dict(energy=5)], material=dict(dissolved=[0], proposals=[]))
        row = verifier.extract_row([dict(energy=1)], physical, 0, True)
        self.assertEqual(row['energy_after'], 0)
        self.assertTrue(row['dissolved'])


if __name__ == '__main__':
    unittest.main()
