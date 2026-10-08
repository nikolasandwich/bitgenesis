"""Independent Study045 boundaries; fixtures require no physical evolution."""
import ast
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import verify_v4_middle_turnover as verifier


class MiddleTurnoverVerifierTests(unittest.TestCase):
    def test_no_production_science_or_physics_imports(self):
        tree = ast.parse(Path(verifier.__file__).read_text())
        imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [name.name for node in ast.walk(tree) if isinstance(node, ast.Import) for name in node.names]
        self.assertFalse(any('analyze_' in name or name.startswith('bitgenesis') for name in imports))

    def test_full_ancestry_keeps_both_selected_hits_without_distinctness_rule(self):
        people = [dict(id=0, parent=None), dict(id=1, parent=0), dict(id=2, parent=1)]
        self.assertEqual(verifier.ancestry(2, people, [1, 2]), ([2, 1, 0], [2, 1]))

    def test_ancestry_rejects_cycles(self):
        with self.assertRaises(ValueError):
            verifier.ancestry(0, [dict(id=0, parent=0)], [])

    def test_budget_rejects_elapsed_and_storage_exact_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            with patch.object(verifier, 'monotonic', return_value=600):
                with self.assertRaisesRegex(ValueError, 'time'):
                    verifier.check_budget(0, path)
            (path / 'artifact.json').write_bytes(b'1234')
            with patch.object(verifier, 'monotonic', return_value=0):
                with self.assertRaisesRegex(ValueError, 'storage'):
                    verifier.check_budget(0, path, extra_bytes=134217724)


class TurnoverIntervalAndGapTests(unittest.TestCase):
    def test_diagnostic_immediate_exit_is_zero_length_and_retained(self):
        result = verifier.intervals(True, [(20, False), (21, True), (22, True), (23, False)])
        self.assertEqual(result, [
            dict(start=None, end=None, length=0, left_censored=True,
                 right_censored=False, entry_tick=None, exit_tick=20),
            dict(start=21, end=22, length=2, left_censored=False,
                 right_censored=False, entry_tick=21, exit_tick=23)])

    def test_diagnostic_is_not_added_to_duration(self):
        self.assertEqual(verifier.intervals(True, [(31, True), (32, True)]), [
            dict(start=31, end=32, length=2, left_censored=True,
                 right_censored=True, entry_tick=None, exit_tick=None)])

    def test_no_predecessor_next_birth_excludes_t0(self):
        people = [dict(id=0, site=101, birth_tick=23, death_tick=None, material=1)]
        ids = [None] * 256
        gap = verifier.site_gaps(101, 20, ids, people)[0]
        self.assertEqual(gap['empty_ticks'], [21, 22])
        self.assertEqual(gap['distance_ticks'], 3)
        self.assertTrue(gap['left_censored'])
        self.assertFalse(gap['right_censored'])

    def test_same_tick_replace_changes_material_without_empty_state(self):
        people = [dict(id=0, site=101, birth_tick=0, death_tick=22, material=0),
                  dict(id=1, site=101, birth_tick=22, death_tick=None, material=1)]
        ids = [None] * 256
        ids[101] = 0
        gap = verifier.site_gaps(101, 20, ids, people)[0]
        self.assertEqual(gap['empty_ticks'], [])
        self.assertEqual(gap['distance_ticks'], 0)
        self.assertTrue(gap['same_tick_replacement'])
        self.assertTrue(gap['material_changed'])

    def test_right_and_double_censoring_count_endpoint_state(self):
        ids = [None] * 256
        people = [dict(id=0, site=101, birth_tick=1, death_tick=30, material=0)]
        ids[101] = 0
        gap = verifier.site_gaps(101, 20, ids, people)[0]
        self.assertEqual(gap['empty_ticks'], [30, 31, 32])
        self.assertEqual(gap['distance_ticks'], 2)
        gap = verifier.site_gaps(102, 20, ids, people)[0]
        self.assertEqual(gap['empty_ticks'], list(range(21, 33)))
        self.assertTrue(gap['left_censored'] and gap['right_censored'])

    def test_material_zero_predicate_is_not_physical_empty(self):
        units = [None] * 256
        ids = [None] * 256
        units[101] = dict(material=1)
        ids[101] = 2
        row = verifier.turnover_row(21, units, ids, [dict.fromkeys(verifier.FLAGS, False)] * 3, 0)
        self.assertTrue(row['G'])
        self.assertFalse(row['physically_empty_both'])
        self.assertIsNone(row['component_equivalence'])

    def test_genetically_matching_component_counterexample_is_retained(self):
        slots = [dict.fromkeys(verifier.FLAGS, True) for _ in range(3)]
        slots[0]['whole_component'] = False
        row = verifier.turnover_row(21, [None] * 256, [None] * 256, slots, 0)
        self.assertTrue(row['genetic_context'])
        self.assertFalse(row['component_equivalence'])
        self.assertTrue(row['overlaps']['G_other_copy_gates'])


class TurnoverEnergyProjectionTests(unittest.TestCase):
    @staticmethod
    def fixture():
        empty = [None] * 256
        ids0 = empty.copy(); ids0[101] = 0
        ids1 = ids0.copy(); ids1[102] = 1
        ids2 = ids1.copy(); ids2[101] = None
        initial = [None] * 256; initial[101] = dict(energy=25, material=0)
        stage1 = [None] * 256; stage1[101] = dict(energy=23, material=0)
        end1 = [None] * 256; end1[101] = dict(energy=9, material=0); end1[102] = dict(energy=9, material=1)
        stage2 = [None] * 256; stage2[101] = dict(energy=0, material=0); stage2[102] = dict(energy=8, material=1)
        end2 = [None] * 256; end2[102] = dict(energy=8, material=1)
        people = [dict(id=0, site=101, parent=None, birth_tick=1, birth_energy=64, death_tick=32, material=0),
                  dict(id=1, site=102, parent=0, birth_tick=31, birth_energy=9, death_tick=None, material=1)]
        formation = dict(source=101, target=102, reason='formed', parent_energy=9, child_energy=9, cost=5)
        rows = [dict(tick=31, site_ids=ids1, births=[people[1].copy()], deaths=[], physical=dict(units=end1, interaction_units=stage1,
                    material=dict(proposals=[formation], dissolved=[]), directions=[3] * 256)),
                dict(tick=32, site_ids=ids2, births=[], deaths=[0], physical=dict(units=end2, interaction_units=stage2,
                    material=dict(proposals=[dict(source=102, target=103, reason='energy')], dissolved=[101]), directions=[3] * 256))]
        return dict(initial=dict(tick=30, site_ids=ids0, units=initial), rows=rows,
                    final=dict(site_ids=ids2, units=end2, individuals=people))

    def test_left_censored_entry_formation_and_death_energy(self):
        entry, formations, exit = verifier.project_energy(0, self.fixture())
        self.assertEqual(entry, dict(kind='initial', tick=30, energy=25))
        self.assertEqual(formations, [dict(tick=31, source=101, target=102, parent_identity=0,
                                         child_identity=1, preformation_energy=23, parent_energy=9, child_energy=9)])
        self.assertEqual(exit, dict(kind='death', tick=32, energy=0, right_censored=False))

    def test_newborn_does_not_act_and_endpoint_is_right_censored(self):
        entry, formations, exit = verifier.project_energy(1, self.fixture())
        self.assertEqual(entry, dict(kind='birth', tick=31, energy=9))
        self.assertEqual(formations, [])
        self.assertEqual(exit, dict(kind='endpoint', tick=32, energy=8, right_censored=True))

    def test_death_direction_ticket_cannot_be_a_formation_proposal(self):
        arm = self.fixture()
        arm['rows'][-1]['physical']['material']['proposals'].append(
            dict(source=101, target=100, reason='energy'))
        with self.assertRaisesRegex(ValueError, 'death.*proposal'):
            verifier.project_energy(0, arm)

    def test_success_requires_preserved_stage_energy(self):
        arm = self.fixture()
        arm['rows'][0]['physical']['material']['proposals'][0]['parent_energy'] = 10
        with self.assertRaises(ValueError):
            verifier.project_energy(0, arm)


class TurnoverFormalProofTests(unittest.TestCase):
    def test_all_twenty_zero_cells_and_full_denominator_are_retained(self):
        index = [dict(encoding=e, seed=seed, trigger=False)
                 for e in verifier.ENCODINGS for seed in range(120000, 120020)]
        result = verifier.summarize([], index)
        self.assertEqual(result['index_cases'], 100)
        self.assertEqual(result['no_trigger'], 100)
        self.assertEqual(len(result['cells']), 20)
        self.assertTrue(all(c['n'] == 0 and c['policy_denominator'] == 20 for c in result['cells']))
        self.assertTrue(all(c['ticks']['G'] == 0 and c['longest']['G'] == 0 for c in result['cells']))

    def test_source_failure_preserves_before_after_hashes_and_zero_physics(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            source = output.parent / (output.name + '-source')
            source.write_text('immutable source')
            try:
                for name in ('metadata.json', 'records.json', 'summary.json', 'index.json'):
                    (output / name).write_text('{}')
                with patch.object(verifier, 'OUTPUT', output), \
                     patch.object(verifier, 'input_paths', return_value=[str(source)]), \
                     patch.object(verifier, 'bindings', side_effect=ValueError('invalid method input')):
                    with self.assertRaisesRegex(ValueError, 'invalid method input'):
                        verifier.main()
                failure = verifier.read(output / 'verification-failure.json')
                self.assertEqual(failure['status'], 'failed')
                self.assertEqual(failure['new_simulation_steps'], 0)
                self.assertEqual(failure['input_sha256'], failure['input_sha256_after'])
                self.assertEqual(len(failure['files_sha256_before']), 4)
                self.assertEqual(failure['files_sha256_before'], failure['files_sha256_after'])
                self.assertFalse((output / 'independent-verification.json').exists())
                with patch.object(verifier, 'OUTPUT', output):
                    with self.assertRaisesRegex(ValueError, 'exclusive'):
                        verifier.main()
            finally:
                source.unlink()


class TurnoverReuseAndMetadataTests(unittest.TestCase):
    def test_042_uses_exact_reference_and_never_projects_again(self):
        arm = TurnoverEnergyProjectionTests.fixture()
        ledger = dict(identity=1, site=102, parent=0, birth_tick=31, birth_energy=9,
                      left_censored=False, rows=[dict(phase='birth', tick=31, end_energy=9),
                                                dict(phase='action', tick=32, reason='energy', end_energy=8)],
                      window=dict(right_censored=True, death_tick=None))
        ref = dict(source_path='data/v4-study-042/records.json', source_file_sha256='abc',
                   json_pointer='/0/identities/0', normalized_record_sha256=verifier.canonical_hash(ledger))
        with patch.object(verifier, 'digest', return_value='abc'), \
             patch.object(verifier, 'project_energy', side_effect=AssertionError('042 recalculation')):
            entry, events, exit = verifier.reuse_energy(1, arm, ref, [dict(identities=[ledger])])
            self.assertEqual(entry, dict(kind='birth', tick=31, energy=9))
            self.assertEqual(events, [])
            self.assertEqual(exit['energy'], 8)
            ref['normalized_record_sha256'] = 'different'
            with self.assertRaisesRegex(ValueError, 'normalized record hash'):
                verifier.reuse_energy(1, arm, ref, [dict(identities=[ledger])])

    def test_endpoint_birth_is_zero_actions_and_right_censored(self):
        arm = TurnoverEnergyProjectionTests.fixture()
        arm['initial']['tick'] = 31
        arm['rows'] = arm['rows'][:1]
        arm['rows'][0]['tick'] = 32
        arm['final']['individuals'][1]['birth_tick'] = 32
        arm['final']['site_ids'] = arm['rows'][0]['site_ids']
        arm['final']['units'] = arm['rows'][0]['physical']['units']
        entry, events, exit = verifier.project_energy(1, arm)
        self.assertEqual(entry['tick'], 32)
        self.assertEqual(events, [])
        self.assertEqual(exit, dict(kind='endpoint', tick=32, energy=9, right_censored=True))

    def test_metadata_requires_counts_error_inventories_and_finite_elapsed(self):
        hashes = {name: name for name in verifier.OUTPUT_NAMES}
        meta = dict(verifier.FIXED_METADATA, input_inventory_errors={}, input_read_errors_before={},
                    input_read_errors_after={}, input_paths=['source'], input_sha256={'source': 'hash'},
                    input_sha256_after={'source': 'hash'}, git_commit='a' * 40, elapsed_seconds=1,
                    output_sha256={k: v for k, v in hashes.items() if k != 'metadata.json'})
        verifier.verify_metadata(meta, ['source'], {'source': 'hash'}, hashes)
        for key, bad in (('identities', 201), ('elapsed_seconds', float('nan')),
                         ('elapsed_seconds', 600), ('input_read_errors_after', {'x': 'error'})):
            altered = dict(meta, **{key: bad})
            with self.assertRaises(ValueError):
                verifier.verify_metadata(altered, ['source'], {'source': 'hash'}, hashes)


if __name__ == '__main__':
    unittest.main()
